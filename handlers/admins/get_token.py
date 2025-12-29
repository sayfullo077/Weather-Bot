from aiogram.fsm.context import FSMContext
from filters.is_admin import IsBotAdmin
from states.all_states import TokenState, AdminState
from database.orm_query import get_single_token, delete_ai_token
from keyboards.default.default_buttons import token_menu_button, add_token_button, admin_confirm_button, admin_menu_button
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import ADMINS
from loader import bot


admin_router = Router()


@admin_router.message(F.text == "🔑 Token", IsBotAdmin())
async def token_menu_func(message: types.Message, state: FSMContext, session: AsyncSession):
    ai_token = await get_single_token(session)

    if ai_token:
        token_id = ai_token.id
        await state.update_data(token_id=token_id)
        text = (
            f"🏷 Token name: {ai_token.title}\n"
            f"🔑 Token: {ai_token.token}\n"
            f"🔋 Token used count: {ai_token.count}"
            "\n\nSelect the required section!"
        )
        reply_markup = await token_menu_button()

    else:
        text = "Token not found! Please add a token."
        reply_markup = await add_token_button()

    await message.answer(text=text, reply_markup=reply_markup)
    await state.set_state(TokenState.menu)


@admin_router.message(F.text == "🗑 Delete", TokenState.menu, IsBotAdmin())
async def delete_token_func(message: types.Message, state: FSMContext):
    admin_confirm_btn = await admin_confirm_button()
    await message.answer(text="Do you confirm deletion?", reply_markup=admin_confirm_btn)
    await state.set_state(TokenState.delete)


@admin_router.message(F.text == "✅ Yes", TokenState.delete, IsBotAdmin())
async def confirm_token_delete_func(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        data = await state.get_data()
        token_id = data.get("token_id")
        await delete_ai_token(session, token_id)
        admin_menu_btn = await admin_menu_button()
        await message.answer(text="The token has been successfully deleted!", reply_markup=admin_menu_btn)

    except Exception as e:
        for admin in ADMINS:
            await bot.send_message(chat_id=admin, text=f"Error while adding the token: {e}")

    await state.set_state(AdminState.menu)


@admin_router.message(F.text == "❌ No", TokenState.delete, IsBotAdmin())
async def cancel_token_delete_func(message: types.Message, state: FSMContext):
    admin_menu_btn = await admin_menu_button()
    await state.clear()
    await message.answer("Token deletion has been canceled!", reply_markup=admin_menu_btn)
    await state.set_state(AdminState.menu)





