import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
WEBHOOK_URL_PROD = "https://oltinwash.pythonanywhere.com/webhook/telegram/"
WEBHOOK_URL_DEV = "https://your-ngrok-url.ngrok.io/webhook/telegram/"


def setup_webhook(use_production=True):
    if not BOT_TOKEN or not WEBHOOK_SECRET:
        print("❌ Токены не настроены!")
        return False

    webhook_url = WEBHOOK_URL_PROD if use_production else WEBHOOK_URL_DEV

    print("🗑️ Удаляем старый webhook...")
    delete_response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    print(f"Результат удаления: {delete_response.json()}")

    print(f"✨ Устанавливаем защищенный webhook на {webhook_url}...")
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        data={
            "url": webhook_url,
            "secret_token": WEBHOOK_SECRET,
            "drop_pending_updates": True,
            "max_connections": 40
        }
    )

    result = response.json()
    if result.get('ok'):
        print("✅ Защищенный webhook установлен успешно!")
        return True
    else:
        print(f"❌ Ошибка: {result}")
        return False


if __name__ == "__main__":
    setup_webhook(use_production=True)
