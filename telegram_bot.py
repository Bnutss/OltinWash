import os
import django
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OltinWash.settings')
django.setup()

BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

import telegram_handlers

dp.include_router(telegram_handlers.router)
