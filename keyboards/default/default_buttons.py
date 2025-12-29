from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton


async def admin_menu_button():
    kb = ReplyKeyboardBuilder()

    kb.button(text="🔑 Token")
    kb.button(text="📊 Info")
    kb.button(text="👤 Users")
    kb.button(text="📨 Message")

    kb.adjust(2)

    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def token_menu_button():
    kb = ReplyKeyboardBuilder()

    kb.button(text="📝 Edit")
    kb.button(text="🗑 Delete")
    kb.button(text="◀️ Back")

    kb.adjust(2, 1)

    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def add_token_button():
    kb = ReplyKeyboardBuilder()

    kb.button(text="➕ Add token")
    kb.button(text="◀️ Back")

    kb.adjust(1)

    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def back_button():
    kb = ReplyKeyboardBuilder()
    kb.button(text="◀️ Back")
    kb.adjust(1)

    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def admin_confirm_button():
    kb = ReplyKeyboardBuilder()

    kb.button(text="✅ Yes")
    kb.button(text="❌ No")

    kb.adjust(2)

    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def edit_token_menu_button():
    kb = ReplyKeyboardBuilder()

    kb.button(text="🏷 Edit Title")
    kb.button(text="🔑 Edit Token")
    kb.button(text="◀️ Back")

    kb.adjust(2, 1)

    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


# get location button
def get_location_button():
    kb = ReplyKeyboardBuilder()

    kb.button(
        text="🌐 Send Location",
        request_location=True
    )

    kb.adjust(1)

    return kb.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )