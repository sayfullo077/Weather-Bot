import re
from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters import Command
from states.all_states import UserMessageState, UserStart
from loader import bot
from database.config import ADMINS
from keyboards.inline.inline_buttons import back_button, start_button


def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


user_router = Router()
user_message_map = {}


@user_router.message(Command("feedback"))
async def ask_for_feedback(message: Message, state: FSMContext):
    back_btn = await back_button()
    await message.answer("📭 Leave your feedback. Your opinion matters to us.", reply_markup=back_btn)
    await state.set_state(UserMessageState.waiting_for_message)


@user_router.message(UserMessageState.waiting_for_message)
async def forward_to_admins(message: Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = html_escape(message.from_user.full_name)
    username = message.from_user.username
    telegram_id = message.from_user.id
    registration_date = datetime.now().strftime("%Y-%m-%d")
    is_premium = message.from_user.is_premium if message.from_user.is_premium else 'Unknown'
    user_text = html_escape(message.text)

    for admin in ADMINS:
        callback_data = f"reply_{user_id}"
        user_message_map[callback_data] = user_id
        await bot.send_message(
            chat_id=admin,
            text=(
                f"👤 User : {full_name}\n"
                f"🔑 Username : {f'@{username}' if username else 'None'}\n"
                f"🆔 Telegram : {telegram_id}\n"
                f"📆 Data : {registration_date}\n"
                f"💎 Premium : {is_premium}\n"
                f"📨 Message : {user_text}"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔰 Profile", url=f"tg://user?id={telegram_id}"),
                    InlineKeyboardButton(text="📤 Reply", callback_data=callback_data)
                ]
            ])
        )

    await message.delete()
    await message.answer("📬 Your message has been delivered to the admin. Please wait for a response shortly!")
    await state.clear()


@user_router.callback_query(F.data.startswith("reply_"))
async def ask_reply_message(callback: CallbackQuery, state: FSMContext):
    user_id = user_message_map.get(callback.data)
    if user_id:
        await callback.message.answer("✉️ Enter your reply message:")
        await state.update_data(user_id=user_id)
        await state.set_state(UserMessageState.waiting_for_admin_reply)
    else:
        await callback.answer("❗️ Xato: User ID noto'g'ri formatda!")


@user_router.message(UserMessageState.waiting_for_admin_reply)
async def send_reply_to_user(message: Message, state: FSMContext):
    state_data = await state.get_data()
    user_id = state_data.get("user_id")
    try:
        if user_id:
            await message.delete()
            await bot.send_message(user_id, f"<b>📥 Admin’s reply</b>:\n{message.text}")
            await message.answer("✅ The reply has been sent to the user!")
    except Exception as e:
        print(f"❗️ User 🆔 not found. Error : {e}")
    await state.clear()


@user_router.callback_query(F.data.startswith("back"))
async def back_btn_func(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    current_state = await state.get_state()

    if current_state == UserMessageState.waiting_for_message:
        telegram_id = call.from_user.id
        fullname = html_escape(call.from_user.full_name)
        start_btn = await start_button(bot_username="Essay_CheckBot", telegram_id=telegram_id)
        await call.message.edit_text(f"👋 Hello {fullname}!\n\nWelcome to the Essay Checker Bot.", reply_markup=start_btn)
        await state.set_state(UserStart.menu)
