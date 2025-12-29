import json
import aiohttp
import re
import logging
from typing import Dict, Any
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext

from loader import redis
from services.ai_prompt import ask_ai_deepseek
from states.all_states import LocationState, UserStart
from database.config import (
    OPENWEATHER_API_KEY,
    OPENWEATHER_URL,
    LOCATIONIQ_BASE_URL,
    LOCATIONIQ_API_KEY,
)
from database.orm_query import orm_add_user, select_user, orm_update_location
from keyboards.inline.inline_buttons import refresh_button, back_button
from keyboards.default.default_buttons import get_location_button

user_router = Router()

CACHE_EXPIRE = 1800  # 30 daqiqa
DAILY_MAX_PROMPTS = 20
BONUS_AMOUNT = 10
logger = logging.getLogger("BACK_HANDLER")

def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


async def get_weather_from_redis(lat: float, lon: float):
    key = f"weather:{round(lat,3)}:{round(lon,3)}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    return None


# ================= PROMPT LIMIT =================

async def initialize_user_count(user_id: int) -> int:
    key = f"user:{user_id}:daily_prompt_count"
    value = await redis.get(key)
    if value is None:
        await redis.set(key, DAILY_MAX_PROMPTS, ex=86400)
        return DAILY_MAX_PROMPTS
    return int(value)


async def decrement_prompt(user_id: int) -> int:
    await initialize_user_count(user_id)
    return await redis.decr(f"user:{user_id}:daily_prompt_count")


# ================= AI PROMPT =================

AI_WEATHER_ANALYST_PROMPT = """
You are an Advanced Weather Analyst AI.
Analyze the weather in a friendly and practical way.
Give short recommendations and warnings if needed.
"""

# ================= EMOJI =================

WEATHER_EMOJI = {
    "Clear": "☀️",
    "Sunny": "☀️",
    "Partly cloudy": "🌤",
    "Cloudy": "☁️",
    "Overcast": "☁️",
    "Mist": "🌫",
    "Fog": "🌫",
    "Rain": "🌧",
    "Snow": "❄️",
    "Thunder": "⛈",
}


def get_weather_emoji(text: str) -> str:
    for key, emoji in WEATHER_EMOJI.items():
        if key.lower() in text.lower():
            return emoji
    return "🌤"


# ================= REVERSE GEOCODE =================

async def reverse_geocode(lat: float, lon: float) -> str:
    cache_key = f"geo:{round(lat,4)}:{round(lon,4)}"
    cached = await redis.get(cache_key)
    if cached:
        return cached

    params = {
        "key": LOCATIONIQ_API_KEY,
        "lat": lat,
        "lon": lon,
        "format": "json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(LOCATIONIQ_BASE_URL, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    address = data.get("address", {})
    result = ", ".join(filter(None, [
        address.get("county"),
        address.get("city") or address.get("town") or address.get("village"),
        address.get("country")
    ]))

    await redis.setex(cache_key, CACHE_EXPIRE, result)
    return result


# ================= WEATHER =================

async def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    cached = await get_weather_from_redis(lat, lon)
    if cached:
        return cached

    params = {
        "key": OPENWEATHER_API_KEY,
        "q": f"{lat},{lon}",
        "lang": "en",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(OPENWEATHER_URL, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    return data



# ================= FORMAT =================

def format_weather(data: Dict[str, Any], address: str) -> str:
    current = data["current"]
    condition = current["condition"]["text"]
    emoji = get_weather_emoji(condition)

    return (
        f"{emoji} **Current Weather**\n"
        f"📍 {address}\n\n"
        f"🌡 Temp: **{current['temp_c']}°C**\n"
        f"🤔 Feels like: {current['feelslike_c']}°C\n"
        f"☁ Condition: {condition}\n"
        f"💨 Wind: {current['wind_kph']} kph\n"
        f"💧 Humidity: {current['humidity']}%\n"
    )


# ================= HANDLER =================

@user_router.message(F.location)
async def handle_location(message: types.Message, session: AsyncSession, state: FSMContext):
    current_state = await state.get_state()
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = message.from_user.id
    user = await select_user(user_id, session)
    full_name = html_escape(message.from_user.full_name)
    address = await reverse_geocode(lat, lon)

    if current_state == LocationState.get_location:
        update = await orm_update_location(session, user_id, address, lat, lon)
        if update:
            await message.delete()
            text = "Your address has been updated."
            await message.answer(text)

    if not user:
        await orm_add_user(session, user_id, full_name, address, lat, lon)
    await message.delete()
    await message.answer("⏳ Processing your weather request, please wait...",
                         reply_markup=ReplyKeyboardRemove())

    weather_data = await get_weather_from_redis(lat, lon)
    refresh_weather_btn = await refresh_button()

    if weather_data:
        print("Weather from redis cache 1 >>>>>", weather_data)
        await message.answer(weather_data, reply_markup=refresh_weather_btn)

    else:
        # 🔹 Ob-havo olish
        weather = await fetch_weather(lat, lon)

        # 🔹 Qisqa summary (AI uchun)
        base_text = (
            f"{get_weather_emoji(weather['current']['condition']['text'])} "
            f"{weather['current']['condition']['text']}, "
            f"{weather['current']['temp_c']}°C, "
            f"feels like {weather['current']['feelslike_c']}°C, "
            f"wind {weather['current']['wind_kph']} kph, "
            f"humidity {weather['current']['humidity']}%"
        )

        # 🔹 AI analiz, faqat tavsiyalar va izoh
        ai_prompt = (
            f"{AI_WEATHER_ANALYST_PROMPT}\n"
            f"User location: {address}\n"
            f"Weather summary: {base_text}\n"
            f"Do NOT repeat numbers or raw data, give only practical advice!"
        )
        ai_text = await ask_ai_deepseek(base_text, ai_prompt)

        await decrement_prompt(user_id)

        # 🔹 Foydalanuvchiga javob
        text_to_send = (
            f"📍 {address}\n"
            f"🌡 {weather['current']['temp_c']}°C, feels like {weather['current']['feelslike_c']}°C\n"
            f"☁ {weather['current']['condition']['text']}\n"
            f"💨 Wind: {weather['current']['wind_kph']} kph\n"
            f"💧 Humidity: {weather['current']['humidity']}%\n\n"
            f"🤖 AI Analysis:\n{ai_text}"
        )
        key = f"weather:{round(lat, 3)}:{round(lon, 3)}"
        await redis.setex(key, CACHE_EXPIRE, json.dumps(text_to_send))
        refresh_weather_btn = await refresh_button()
        await message.answer(text_to_send, parse_mode="Markdown", reply_markup=refresh_weather_btn)


@user_router.callback_query(F.data == "weather_update")
async def refresh_weather_func(call: types.CallbackQuery, session: AsyncSession):
    telegram_id = call.from_user.id
    user = await select_user(telegram_id, session)
    lat = user.lat
    lon = user.lon
    weather_data = await get_weather_from_redis(lat, lon)
    refresh_weather_btn = await refresh_button()
    await call.message.delete()

    if weather_data:
        await call.message.answer(weather_data, parse_mode="Markdown", reply_markup=refresh_weather_btn)

    else:
        if user:
            lat = user.lat
            lon = user.lon
            address = user.address
            weather = await fetch_weather(lat, lon)

            # 🔹 Qisqa summary (AI uchun)
            base_text = (
                f"{get_weather_emoji(weather['current']['condition']['text'])} "
                f"{weather['current']['condition']['text']}, "
                f"{weather['current']['temp_c']}°C, "
                f"feels like {weather['current']['feelslike_c']}°C, "
                f"wind {weather['current']['wind_kph']} kph, "
                f"humidity {weather['current']['humidity']}%"
            )

            # 🔹 AI analiz, faqat tavsiyalar va izoh
            ai_prompt = (
                f"{AI_WEATHER_ANALYST_PROMPT}\n"
                f"User location: {address}\n"
                f"Weather summary: {base_text}\n"
                f"Do NOT repeat numbers or raw data, give only practical advice!"
            )
            ai_text = await ask_ai_deepseek(base_text, ai_prompt)

            await decrement_prompt(telegram_id)

            # 🔹 Foydalanuvchiga javob
            text_to_send = (
                f"📍 {address}\n"
                f"🌡 {weather['current']['temp_c']}°C, feels like {weather['current']['feelslike_c']}°C\n"
                f"☁ {weather['current']['condition']['text']}\n"
                f"💨 Wind: {weather['current']['wind_kph']} kph\n"
                f"💧 Humidity: {weather['current']['humidity']}%\n\n"
                f"🤖 AI Analysis:\n{ai_text}"
            )

            await call.message.delete()
            await call.message.answer(text_to_send, parse_mode="Markdown", reply_markup=refresh_weather_btn)

        else:
            await call.message.answer("⚠️ To fully use the bot, please submit your location first",
                                 reply_markup=get_location_button())


@user_router.callback_query(F.data == "location_update")
async def refresh_location_func(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("Send your location to update address")
    await state.set_state(LocationState.get_location)
