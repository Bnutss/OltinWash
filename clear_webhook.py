import requests

BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"
WEBHOOK_URL = "https://oltinwash.pythonanywhere.com/webhook/telegram/"

# Удаляем webhook
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")

# Устанавливаем заново с очисткой pending
response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={
        "url": WEBHOOK_URL,
        "drop_pending_updates": True
    }
)

print("✅ Webhook переустановлен с очисткой pending сообщений")
print(response.json())
