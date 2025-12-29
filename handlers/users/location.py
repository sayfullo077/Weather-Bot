import aiohttp

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from states.all_states import LocationState
from database.config import LOCATIONIQ_API_KEY, LOCATIONIQ_BASE_URL, ADMINS
from database.orm_query import select_user
from keyboards.inline.inline_buttons import user_profile_button
from loader import bot

user_router = Router()


async def reverse_geocode(lat: float, lon: float, lang: str = "en") -> dict:
    params = {
        "key": LOCATIONIQ_API_KEY,
        "lat": lat,
        "lon": lon,
        "format": "json",
        "accept-language": lang
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(LOCATIONIQ_BASE_URL, params=params) as response:
            response.raise_for_status()
            return await response.json()


# @user_router.message(lambda msg: msg.location)
# async def handle_location(message: types.Message):
#     lat = message.location.latitude
#     lon = message.location.longitude
#     telegram_id = message.from_user.id
#
#     try:
#         data = await reverse_geocode(lat, lon)
#         address = data.get("address", {})
#         city = address.get("town") or address.get("city", "Noma’lum shahar")
#         state = address.get("state", "")
#         country = address.get("country", "")
#
#         await message.answer(
#             f"📍 Location determined:\n"
#             f"🏙 City: {city}\n"
#             f"🗺 State: {state}\n"
#             f"🌍 Country: {country}",
#             reply_markup=ReplyKeyboardRemove()
#         )
#
#     except Exception as e:
#         await message.answer("❌ There was an error determining the location.")
#         user_profile_btn = await user_profile_button(telegram_id=telegram_id)
#         for admin in ADMINS:
#             await bot.send_message(chat_id=admin, text=f"❌ There was an error determining the location.\n\n{e}",
#                                    reply_markup=user_profile_btn)
#
#
#
#
#

# async def reverse_geocode(lat, lon):
#     try:
#         url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={API_KEY}"
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 data = await response.json()
#
#         if data.get("results"):
#             components = data["results"][0]["components"]
#             country = components.get("country", "")
#             city = components.get("town") or components.get("city") or components.get("state", "")
#             district = components.get("state_district", "")
#             road = components.get("road", "")
#             house_number = components.get("house_number", "")
#             capital = components.get("_normalized_city", "")
#             short_address = f"{country}, {city} {district} {road} {house_number}".strip()
#
#             return (short_address if short_address.strip() else "Manzil topilmadi", capital)
#         else:
#             return "Manzil topilmadi"
#
#     except Exception as e:
#         return f"Xatolik yuz berdi: {str(e)}"