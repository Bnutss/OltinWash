import requests

BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"
WEBHOOK_URL = "https://oltinwash.pythonanywhere.com/webhook/telegram/"

print("🗑️ Удаляем старый webhook...")

# Удаляем webhook
delete_response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
)
print(f"Удаление: {delete_response.json()}")

print("✨ Устанавливаем новый webhook...")

# Устанавливаем заново с очисткой pending
response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={
        "url": WEBHOOK_URL,
        "drop_pending_updates": True
    }
)

result = response.json()
if result.get('ok'):
    print("✅ Webhook установлен успешно!")
    print(f"URL: {WEBHOOK_URL}")
else:
    print(f"❌ Ошибка: {result}")
