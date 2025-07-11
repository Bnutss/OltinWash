import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')


def check_bot_status():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не настроен!")
        return

    print("🔍 Проверяем статус бота...")

    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
    result = response.json()

    if result.get('ok'):
        info = result['result']
        print(f"📍 Webhook URL: {info.get('url', 'Не установлен')}")
        print(f"📊 Pending updates: {info.get('pending_update_count', 0)}")
        print(f"🔐 Has secret: {'Да' if info.get('url') else 'Нет'}")

        if 'last_error_message' in info:
            print(f"❌ Ошибка: {info['last_error_message']}")
        else:
            print("✅ Ошибок нет")

    me_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
    if me_response.json().get('ok'):
        bot_info = me_response.json()['result']
        print(f"🤖 Бот активен: @{bot_info['username']}")
    else:
        print("❌ Бот не отвечает!")


if __name__ == "__main__":
    check_bot_status()
