from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from filters.is_admin import IsBotAdmin
from states.all_states import TokenState, EditTokenState
from keyboards.default.default_buttons import back_button, edit_token_menu_button, admin_confirm_button, admin_menu_button
from database.orm_query import update_single_token
from aiogram import Router, types, F
from loader import bot
from database.config import ADMINS


admin_router = Router()


@admin_router.message(F.text == "📝 Edit", TokenState.menu, IsBotAdmin())
async def edit_token_menu_func(message: types.Message, state: FSMContext):
    data = await state.get_data()
    token_id = data.get("token_id")
    await state.update_data(token_id=token_id)
    edit_token_menu_btn = await edit_token_menu_button()
    await message.answer("Which part do you want to change?", reply_markup=edit_token_menu_btn)
    await state.set_state(EditTokenState.menu)


@admin_router.message(F.text == "🏷 Edit Title", EditTokenState.menu, IsBotAdmin())
async def edit_token_title_func(message: types.Message, state: FSMContext):
    back_btn = await back_button()
    await message.answer("Enter the new token title:", reply_markup=back_btn)
    await state.set_state(EditTokenState.title)


@admin_router.message(EditTokenState.title, IsBotAdmin())
async def edited_title_func(message: types.Message, state: FSMContext, session: AsyncSession):
    title = message.text.strip()
    data = await state.get_data()
    token_id = data.get("token_id")
    edit_token_menu_btn = await edit_token_menu_button()
    try:
        await update_single_token(token_id, session, title=title)
        await message.answer("The token title has been updated!", reply_markup=edit_token_menu_btn)

    except Exception as e:
        for admin in ADMINS:
            await bot.send_message(chat_id=admin, text=f"Error while editing the token title: {e}")
        await message.answer("Unexpected error! Please try again later ⁉️", reply_markup=edit_token_menu_btn)

    await state.set_state(EditTokenState.menu)


@admin_router.message(F.text == "🔑 Edit Token", EditTokenState.menu, IsBotAdmin())
async def edit_token_func(message: types.Message, state: FSMContext):
    back_btn = await back_button()
    await message.answer("Enter the new token:", reply_markup=back_btn)
    await state.set_state(EditTokenState.token)


@admin_router.message(EditTokenState.token, IsBotAdmin())
async def edited_token_func(message: types.Message, state: FSMContext, session: AsyncSession):
    token = message.text.strip()
    data = await state.get_data()
    token_id = data.get("token_id")
    edit_token_menu_btn = await edit_token_menu_button()
    try:
        await update_single_token(token_id, session, token=token)
        await message.answer("The token has been updated!", reply_markup=edit_token_menu_btn)

    except Exception as e:
        for admin in ADMINS:
            await bot.send_message(chat_id=admin, text=f"Error while editing the token: {e}")
        await message.answer("Unexpected error! Please try again later ⁉️", reply_markup=edit_token_menu_btn)

    await state.set_state(EditTokenState.menu)