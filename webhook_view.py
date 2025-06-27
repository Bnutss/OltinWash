import json
import asyncio
import os
import django
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OltinWash.settings')
django.setup()

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        from aiogram.types import Update
        from telegram_bot import dp, bot

        update_data = json.loads(request.body.decode('utf-8'))
        logger.info(f"Received update: {update_data}")

        def run_async_update():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def process_update():
                    update = Update.model_validate(update_data)
                    await dp.feed_update(bot, update)

                loop.run_until_complete(process_update())
                loop.close()

            except Exception as e:
                logger.error(f"Error processing update: {e}")
                import traceback
                traceback.print_exc()

        import threading
        thread = threading.Thread(target=run_async_update)
        thread.start()

        return HttpResponse("OK")

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)
