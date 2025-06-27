import os
import asyncio
import django
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OltinWash.settings')
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Импортируем и регистрируем обработчики
try:
    import telegram_handlers

    dp.include_router(telegram_handlers.router)
    logger.info("✅ Telegram handlers loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading telegram handlers: {e}")
    exit(1)


async def main():
    try:
        # Удаляем webhook если был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🗑️ Webhook удален")

        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username}")
        logger.info(f"📛 Имя бота: {bot_info.first_name}")

        # Запускаем polling
        logger.info("🔄 Запуск polling...")
        logger.info("✅ Бот работает! Напишите /start в Telegram")
        logger.info("🛑 Для остановки нажмите Ctrl+C")

        await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
