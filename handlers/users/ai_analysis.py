from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message, ContentType, FSInputFile
from aiogram import F
from utils.file_reader import extract_text
from services.ai_prompt import ask_ai_deepseek
import os
import json
from loader import redis


user_router = Router()

DAILY_MAX_PROMPTS = 20  # kunlik limit
BONUS_AMOUNT = 10      # Neon bonus miqdori

#
# async def initialize_user_count(user_id: int):
#     key = f"user:{user_id}:daily_prompt_count"
#     exists = await redis.exists(key)
#     if not exists:
#         await redis.set(key, DAILY_MAX_PROMPTS, ex=24 * 60 * 60)
#         return DAILY_MAX_PROMPTS
#     return int(await redis.get(key))
#
#
# async def decrement_prompt(user_id: int) -> int:
#     key = f"user:{user_id}:daily_prompt_count"
#
#     count = await initialize_user_count(user_id)
#
#     if count <= 0:
#         return 0
#
#     count = await redis.decr(key)
#
#     ttl = await redis.ttl(key)
#     if ttl == -1:
#         await redis.expire(key, 24 * 60 * 60)
#
#     return count
#
#
# async def get_remaining_attempts(user_id: int) -> int:
#     key = f"user:{user_id}:daily_prompt_count"
#     count = await redis.get(key)
#     if count is None:
#         return DAILY_MAX_PROMPTS
#     return int(count)
#
#
# async def add_bonus_attempts(user_id: int):
#     key = f"user:{user_id}:daily_prompt_count"
#
#     # avto-init
#     await initialize_user_count(user_id)
#
#     new_value = await redis.incrby(key, BONUS_AMOUNT)
#
#     ttl = await redis.ttl(key)
#     if ttl == -1:
#         await redis.expire(key, 24 * 60 * 60)
#
#     return new_value
#
#
# AI_WEATHER_ANALYST_PROMPT = """
# You are an **Advanced Weather Analyst AI**.
#
# You will receive **weather data** (current, tomorrow, or weekly forecast) along with the user's **location**.
# Your task is to provide a **clear, human-friendly, and useful weather analysis** based on the given data.
#
# ### Instructions for AI:
# 1. Briefly describe the **overall weather situation** for the given location.
# 2. Highlight **key weather factors only**:
#    - Temperature trends
#    - Weather conditions (rain, snow, heat, cold, wind, etc.)
#    - Wind or extreme conditions (if any)
# 3. Explain how the weather **feels in real life**, not just numbers.
# 4. Provide **practical recommendations** (2–4 items), such as:
#    - Clothing advice
#    - Travel or outdoor activity suggestions
#    - Health or safety tips
# 5. If extreme or unusual weather is detected, **clearly warn the user**.
# 6. Keep the tone:
#    - Professional
#    - Friendly
#    - Informative (not robotic)
# 7. Do NOT repeat raw weather data verbatim.
# 8. Do NOT include technical API terms or JSON references.
# 9. Structure the response using:
#    - Short paragraphs
#    - Bullet points for recommendations
# 10. **Do NOT exceed 250 words**.
#
# The weather data will be provided separately.
# """
#
#
# @user_router.message(F.content_type != ContentType.DOCUMENT)
# async def all_wrong_data_handler(msg: Message):
#     image = FSInputFile("media/docs_format.jpg")
#     await msg.answer_photo(
#         photo=image,
#         caption=(
#             "⚠️ Please upload your essay *as a PDF, DOCX, or TXT file*.\n\n"
#             "Other message types are not supported."
#         ),
#         parse_mode="Markdown"
#     )
#
#
# @user_router.message(F.content_type == ContentType.DOCUMENT)
# async def handle_document(msg: Message):
#     user_id = msg.from_user.id
#
#     await initialize_user_count(user_id)
#     remaining = await get_remaining_attempts(user_id)
#
#     if remaining <= 0:
#         await msg.answer("⚠️ You have reached your daily limit of 3 AI prompts. Please try again tomorrow.")
#         return
#
#     doc = msg.document
#     file_path = f"downloads/{doc.file_id}_{doc.file_name}"
#     os.makedirs("downloads", exist_ok=True)
#     await msg.bot.download(doc, destination=file_path)
#
#     text = await extract_text(file_path)
#
#     if not text:
#         await msg.answer("❌ Sorry, I cannot read this file format. Please send TXT, DOCX, or PDF.")
#         os.remove(file_path)
#         return
#
#     await msg.answer("⏳ Your essay is being analyzed... Please wait.")
#
#     result = await ask_ai_deepseek(text, AI_WEATHER_ANALYST_PROMPT)
#
#     await decrement_prompt(user_id)
#
#     await msg.answer(result)
#
#     os.remove(file_path)
#
