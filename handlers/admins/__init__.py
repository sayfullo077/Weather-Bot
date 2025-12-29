from aiogram import Router
from . import admin, add_token, edit_token, get_token, back_button, send_msg_menu

admin_router = Router()

admin_router.include_router(admin.admin_router)
admin_router.include_router(add_token.admin_router)
admin_router.include_router(edit_token.admin_router)
admin_router.include_router(get_token.admin_router)
admin_router.include_router(back_button.admin_router)
admin_router.include_router(send_msg_menu.admin_router)

__all__ = ["admin_router"]