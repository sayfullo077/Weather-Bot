from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from filters.is_admin import IsBotAdmin
from states.all_states import TokenState, AdminState
from keyboards.default.default_buttons import back_button, admin_confirm_button, admin_menu_button
from database.orm_query import save_single_token
from aiogram import Router, types, F
from loader import bot
from database.config import ADMINS


admin_router = Router()


@admin_router.message(F.text == "➕ Add token", IsBotAdmin())
async def add_title_func(message: types.Message, state: FSMContext):
    back_btn = await back_button()
    await message.answer("Please enter the token name", reply_markup=back_btn)
    await state.set_state(TokenState.add_title)


@admin_router.message(TokenState.add_title, IsBotAdmin())
async def add_token_func(message: types.Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    back_btn = await back_button()
    await message.answer("Please enter the token", reply_markup=back_btn)
    await state.set_state(TokenState.add_token)


@admin_router.message(TokenState.add_token, IsBotAdmin())
async def add_check_func(message: types.Message, state: FSMContext):
    token = message.text.strip()
    data = await state.get_data()
    title = data.get("title")
    await state.update_data(token=token)
    admin_confirm_btn = await admin_confirm_button()
    text = (f"🏷 Token name: {title}\n"
            f"🔑 Token: {token}\n\n"
            f"Is the information you entered correct?")
    await message.answer(text, reply_markup=admin_confirm_btn)
    await state.set_state(TokenState.check)


@admin_router.message(F.text == "✅ Yes", TokenState.check, IsBotAdmin())
async def confirm_token_save_func(message: types.Message, state: FSMContext, session: AsyncSession):
    admin_menu_btn = await admin_menu_button()
    try:
        data = await state.get_data()
        title = data.get("title")
        token = data.get("token")
        await save_single_token(title, token, session)
        await message.answer("The token has been successfully saved!", reply_markup=admin_menu_btn)

    except Exception as e:
        for admin in ADMINS:
            await bot.send_message(chat_id=admin, text=f"Error while adding the token: {e}")
        await message.answer("Unexpected error! Please try again later ⁉️", reply_markup=admin_menu_btn)

    await state.set_state(AdminState.menu)


@admin_router.message(F.text == "❌ No", TokenState.check, IsBotAdmin())
async def cancel_token_save_func(message: types.Message, state: FSMContext):
    admin_menu_btn = await admin_menu_button()
    await state.clear()
    await message.answer("Token addition has been canceled!", reply_markup=admin_menu_btn)
    await state.set_state(AdminState.menu)