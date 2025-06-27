import json
import asyncio
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from aiogram.types import Update

from telegram_bot import dp, bot


@csrf_exempt
@require_POST
def telegram_webhook(request):
    try:
        update_data = json.loads(request.body.decode('utf-8'))
        asyncio.run(process_telegram_update(update_data))
        return HttpResponse("OK")
    except Exception as e:
        print(f"Webhook error: {e}")
        return HttpResponse("Error", status=500)


async def process_telegram_update(update_data):
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)
