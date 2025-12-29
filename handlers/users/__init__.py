from aiogram import Router
from . import start, feedback, help, ai_analysis, location, weather

user_router = Router()

user_router.include_router(start.user_router)
user_router.include_router(feedback.user_router)
user_router.include_router(help.user_router)
user_router.include_router(ai_analysis.user_router)
user_router.include_router(location.user_router)
user_router.include_router(weather.user_router)

__all__ = ["user_router"]