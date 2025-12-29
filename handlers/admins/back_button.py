from loader import dp
from aiogram.types import Message
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from filters.is_admin import IsBotAdmin
from states.all_states import (
    TokenState, AdminState, EditTokenState
)
from keyboards.inline.inline_buttons import build_users_keyboard
from keyboards.default.default_buttons import admin_menu_button, back_button, token_menu_button, add_token_button, edit_token_menu_button
from database.orm_query import get_single_token, select_all_users


admin_router = Router()


@dp.message(F.text == "◀️ Back", IsBotAdmin())
async def back_state_func(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    text = "Select the required section!"
    back_btn = await back_button()
    if current_state in [
        TokenState.menu,
        AdminState.info,
        AdminState.send_message,
        AdminState.user_list
        ]:
        await state.clear()
        admin_menu_btn = await admin_menu_button()
        await message.answer(text, reply_markup=admin_menu_btn)
        await state.set_state(AdminState.menu)
    elif current_state == EditTokenState.menu:
        ai_token = await get_single_token(session)

        if ai_token:
            token_id = ai_token.id
            await state.update_data(token_id=token_id)
            text = (
                f"🏷 Token name: {ai_token.title}\n"
                f"🔑 Token: {ai_token.token}\n"
                f"🔋 Token limit: {ai_token.count}"
                "\n\nSelect the required section!"
            )
            reply_markup = await token_menu_button()

        else:
            text = "Token not found! Please add a token."
            reply_markup = await add_token_button()

        await message.answer(text=text, reply_markup=reply_markup)
        await state.set_state(TokenState.menu)

    elif current_state in [
        EditTokenState.title,
        EditTokenState.token
    ]:
        data = await state.get_data()
        token_id = data.get("token_id")
        await state.update_data(token_id=token_id)
        edit_token_menu_btn = await edit_token_menu_button()
        await message.answer("Which part do you want to change?", reply_markup=edit_token_menu_btn)
        await state.set_state(EditTokenState.menu)

    elif current_state == AdminState.user_detail:
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