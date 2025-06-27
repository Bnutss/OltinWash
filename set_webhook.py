import requests

BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"
WEBHOOK_URL = "https://oltinwash.pythonanywhere.com/webhook/telegram/"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={"url": WEBHOOK_URL}
)

if response.json().get('ok'):
    print('✅ Webhook установлен успешно!')
else:
    print(f'❌ Ошибка: {response.json()}')
