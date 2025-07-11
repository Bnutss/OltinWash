import os
from dotenv import load_dotenv

load_dotenv()


def test_environment():
    print("🧪 Тестируем переменные окружения...")

    bot_token = os.environ.get('BOT_TOKEN')
    webhook_secret = os.environ.get('WEBHOOK_SECRET')
    django_secret = os.environ.get('DJANGO_SECRET_KEY')

    print(f"BOT_TOKEN: {'✅ Настроен' if bot_token else '❌ НЕ настроен'}")
    print(f"WEBHOOK_SECRET: {'✅ Настроен' if webhook_secret else '❌ НЕ настроен'}")
    print(f"DJANGO_SECRET_KEY: {'✅ Настроен' if django_secret else '❌ НЕ настроен'}")

    if bot_token:
        print(f"Токен начинается с: {bot_token[:10]}...")


if __name__ == "__main__":
    test_environment()
