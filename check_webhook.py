import requests

BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"

response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
print(response.json())
