import re
import json
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.inline.inline_buttons import start_button, check_member_button, user_profile_button, refresh_button
from keyboards.default.default_buttons import get_location_button
from states.all_states import UserStart
from database.config import PRIVATE_CHANNEL, CHANNEL_USERNAME, ADMINS
from database.orm_query import select_user
from loader import bot, redis
from datetime import datetime
from services.ai_prompt import ask_ai_deepseek
from handlers.users.weather import decrement_prompt, fetch_weather, get_weather_emoji, AI_WEATHER_ANALYST_PROMPT, CACHE_EXPIRE


user_router = Router()


# HTML escape function
def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


async def get_weather_from_redis(lat: float, lon: float):
    key = f"weather:{round(lat,3)}:{round(lon,3)}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    return None


# check subscription member function
async def is_user_subscribed(user_id: int) -> bool:
    """Foydalanuvchi kanalga obuna bo'lganligini tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id=PRIVATE_CHANNEL, user_id=user_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return False


# User start functions
@user_router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    username = message.from_user.username
    registration_date = datetime.now().strftime("%Y-%m-%d")
    is_premium = message.from_user.is_premium if message.from_user.is_premium else 'Unknown'
    lang_code = message.from_user.language_code if message.from_user.language_code else 'Unknown'
    user = await select_user(telegram_id, session)
    full_name = html_escape(message.from_user.full_name)
    lat = user.lat
    lon = user.lon
    address = user.address
    subscribed = await is_user_subscribed(telegram_id)
    check_member_btn = await check_member_button(CHANNEL_USERNAME)
    if not user:
        try:
            user_profile_btn = await user_profile_button(telegram_id)
            await bot.send_message(chat_id=-1003134144759, text=f"New 👤: {full_name}\nUsername📩: {f'@{username}' if username else 'None'}\nTelegram 🆔: {telegram_id}\nReg 📆: {registration_date}\nPremium🤑: {is_premium}\nLang: {lang_code}",
                                       reply_markup=user_profile_btn)
            await message.answer(f"👋 Hello {full_name}!\nWelcome to the weather bot 🌦\n\n"
                                 f"⚠️ To fully use the bot, please submit your location first",
                                 reply_markup=get_location_button())
        except Exception as e:
            for admin in ADMINS:
                await bot.send_message(chat_id=admin, text=f"Error while creating new user: {e}")

    # if not subscribed:
    #     # Obuna bo'lmagan foydalanuvchi uchun
    #     await message.answer(f"👋 Hello {full_name}!\n\nTo use the Essay Checker Bot, you must subscribe to our "
    #                          f"main channel first.", reply_markup=check_member_btn)
    #     return

    weather_data = await get_weather_from_redis(lat, lon)
    refresh_weather_btn = await refresh_button()

    if weather_data:
        print("Weather from redis cache 2 >>>>>")
        await message.answer(weather_data, parse_mode="Markdown", reply_markup=refresh_weather_btn)

    else:
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
        key = f"weather:{round(lat, 3)}:{round(lon, 3)}"
        await redis.setex(key, CACHE_EXPIRE, json.dumps(text_to_send))

        await message.answer(text_to_send, parse_mode="Markdown", reply_markup=refresh_weather_btn)
    await state.set_state(UserStart.menu)


@user_router.callback_query(F.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id

    try:
        member = await call.bot.get_chat_member(chat_id=PRIVATE_CHANNEL, user_id=user_id)
        await call.message.delete()
        if member.status in ["member", "administrator", "creator"]:
            start_btn = await start_button(bot_username="Essay_CheckBot", telegram_id=user_id)
            await call.message.answer(
                "✅ Subscription confirmed!\n\nYou can now use the bot fully.", reply_markup=start_btn

            )
        else:
            btn = await check_member_button(CHANNEL_USERNAME)
            await call.message.answer(
                "❌ You are not subscribed.\n\nPlease subscribe first:",
                reply_markup=btn
            )

    except Exception as e:
        await call.message.answer(f"Error checking subscription: {e}")


