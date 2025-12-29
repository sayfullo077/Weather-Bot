import urllib.parse
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database.config import PRIVATE_CHANNEL

USERS_PER_PAGE = 5


def build_users_keyboard(users, page: int):
    keyboard = InlineKeyboardBuilder()

    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    sliced_users = users[start:end]

    for idx, user in enumerate(sliced_users, start=start + 1):
        keyboard.button(
            text=f"{idx}. {user.full_name}",
            callback_data=f"user:{user.telegram_id}"
        )

    # Pagination buttons
    nav = InlineKeyboardBuilder()

    if page > 0:
        nav.button(text="⬅️ Prev", callback_data=f"users_page:{page - 1}")

    if end < len(users):
        nav.button(text="➡️ Next", callback_data=f"users_page:{page + 1}")

    nav.adjust(2)

    keyboard.adjust(1)
    keyboard.attach(nav)

    return keyboard.as_markup()


async def start_button(bot_username: str, telegram_id: int):
    btn = InlineKeyboardBuilder()
    referral_link = f"https://t.me/{bot_username}?start=ref_{telegram_id}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}"
    btn.button(text="⁉️ Help / Instructions", url="https://telegra.ph/Essay-Checker-Bot--User-Guide-12-09")
    btn.button(text="📤 Share Bot", url=share_url)
    btn.button(text="⚡️ Start", callback_data="start_btn")
    btn.adjust(1)
    return btn.as_markup()


async def user_finish_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="✅ Yakunlash", callback_data="user_finish")
    btn.button(text="❌ Bekor qilish", callback_data="cancel")
    btn.adjust(2)
    return btn.as_markup()


async def back_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="◀️ Back", callback_data="back")
    btn.adjust(1)
    return btn.as_markup()


async def check_member_button(CHANNEL_USERNAME):
    # @ belgisi bo‘lsa olib tashlaymiz
    clean_username = CHANNEL_USERNAME.replace("@", "")

    btn = InlineKeyboardBuilder()
    btn.button(
        text="📢 Subscribe to Channel",
        url=f"https://t.me/{clean_username}"
    )
    btn.button(
        text="✅ Check Subscription",
        callback_data="check_sub"
    )
    btn.adjust(1)
    return btn.as_markup()


async def user_profile_button(telegram_id: int):
    btn = InlineKeyboardBuilder()
    btn.button(text="ℹ️ Profile", url=f"tg://user?id={telegram_id}")
    btn.adjust(1)
    return btn.as_markup()


async def refresh_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="🌦 Weather update ", callback_data='weather_update')
    btn.button(text="🌎 Location update", callback_data='location_update')
    btn.adjust(1)
    return btn.as_markup()
