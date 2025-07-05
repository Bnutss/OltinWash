import requests

BOT_TOKEN = "8124655365:AAHgaInvKblFkm51Cz4TQEquF8K1zUyt4kQ"

print("🔍 Проверяем статус webhook...")

response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
result = response.json()

if result.get('ok'):
    info = result['result']
    print(f"📍 URL: {info.get('url', 'Не установлен')}")
    print(f"📊 Pending updates: {info.get('pending_update_count', 0)}")

    if 'last_error_message' in info:
        print(f"❌ Последняя ошибка: {info['last_error_message']}")
        print(f"📅 Дата ошибки: {info.get('last_error_date', 'Неизвестно')}")
    else:
        print("✅ Ошибок нет")

    print(f"🔗 Max connections: {info.get('max_connections', 'Неизвестно')}")

else:
    print(f"❌ Ошибка API: {result}")
