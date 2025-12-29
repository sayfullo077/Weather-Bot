import re
import aiogram
import time
import platform
import psutil
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import ReplyKeyboardBuilder, KeyboardButton, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy import select, func
from aiogram.filters import Command
from states.all_states import AdminState
from keyboards.default.default_buttons import admin_menu_button, back_button
from keyboards.inline.inline_buttons import build_users_keyboard
from filters.is_admin import IsBotAdmin
from database.models import User, AI_Token
from database.orm_query import select_all_users, select_user


BOT_START_TIME = time.time()


def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


admin_router = Router()


@admin_router.message(Command("admin"), IsBotAdmin())
async def admin_menu(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    fullname = html_escape(message.from_user.full_name)
    admin_menu_btn = await admin_menu_button()
    await message.answer(f"👋 Hello {fullname}!\n\nWelcome to the Admin panel.", reply_markup=admin_menu_btn)
    await state.set_state(AdminState.menu)


@admin_router.message(F.text == "📊 Info", AdminState.menu, IsBotAdmin())
async def bot_info(message: types.Message, session: AsyncSession, state: FSMContext):
    back_btn = await back_button()
    """
    Display detailed bot information including user stats, system stats, and AI token status.
    """
    # --- User statistics ---
    total_users_query = await session.execute(select(func.count(User.id)))
    total_users = total_users_query.scalar() or 0

    # Kunlik foydalanuvchilar (bugun qo‘shilgan)
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_users_query = await session.execute(
        select(func.count(User.id)).where(User.created >= today_start)
    )
    daily_users = daily_users_query.scalar() or 0

    # --- System statistics ---
    memory = psutil.virtual_memory()
    memory_used = memory.used / 1024 ** 2  # MB
    memory_total = memory.total / 1024 ** 2  # MB
    cpu_percent = psutil.cpu_percent(interval=0.5)

    # --- Bot uptime ---
    uptime_seconds = int(time.time() - BOT_START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    # --- AI / Token status ---
    ai_token_query = await session.execute(select(AI_Token))
    ai_token = ai_token_query.scalar_one_or_none()
    if ai_token:
        token_info = f"{ai_token.title} (Remaining Count: {ai_token.count})"
    else:
        token_info = "No token set"

    # --- Bot info text ---
    info_text = (
        f"🤖 **Bot Info**\n\n"
        f"🕒 Uptime: {uptime_str}\n"
        f"👥 Total Users: {total_users}\n"
        f"📈 New Today: {daily_users}\n"
        f"💾 RAM Used: {memory_used:.1f}MB / {memory_total:.1f}MB\n"
        f"⚡ CPU Usage: {cpu_percent}%\n"
        f"🔑 AI Token: {token_info}\n\n"
        f"🛠 Python: {platform.python_version()}\n"
        f"🛠 Aiogram: {aiogram.__version__}"
    )

    # --- Send message ---
    await message.answer(info_text, reply_markup=back_btn)
    await state.set_state(AdminState.info)


@admin_router.message(F.text == "👤 Users", AdminState.menu, IsBotAdmin())
async def all_users_func(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext
):
    users = await select_all_users(session)
    back_btn = await back_button()
    await message.answer("📋", reply_markup=back_btn)

    if not users:
        await message.answer("Sorry, there are currently no saved users ❗️")
        return

    await state.update_data(users=users)

    keyboard = build_users_keyboard(users, page=0)

    await message.answer(
        text="Users list (page 1)",
        reply_markup=keyboard
    )

    await state.set_state(AdminState.user_list)


@admin_router.callback_query(
    F.data.startswith("users_page:"),
    AdminState.user_list,
    IsBotAdmin()
)
async def users_pagination(
    call: types.CallbackQuery,
    state: FSMContext
):
    page = int(call.data.split(":")[1])
    data = await state.get_data()
    users = data["users"]

    keyboard = build_users_keyboard(users, page)

    await call.message.edit_text(
        text=f"Users list (page {page + 1})",
        reply_markup=keyboard
    )

    await call.answer()


@admin_router.callback_query(F.data.startswith("user:"))
async def user_detail_callback(
    call: types.CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    telegram_id = int(call.data.split(":")[1])

    user = await select_user(telegram_id, session)

    if not user:
        await call.answer("User not found ❌", show_alert=True)
        return

    text = (
        f"👤 <b>User info</b>\n\n"
        f"🆔 ID: <code>{user.telegram_id}</code>\n"
        f"👤 Name: {user.full_name}\n"
        f"📍 Location: {user.address or '—'}"
    )
    back_btn = await back_button()
    await call.message.delete()
    await call.message.answer(text, parse_mode="HTML", reply_markup=back_btn)
    await state.set_state(AdminState.user_detail)