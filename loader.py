import aioredis
from aiogram import Bot,Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN,parse_mode='HTML')
dp = Dispatcher(storage=MemoryStorage())
redis = aioredis.from_url("redis://localhost", decode_responses=True)