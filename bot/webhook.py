import json

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from aiogram import types

from .main import bot, dp


@csrf_exempt
async def telegram_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    secret = getattr(settings, 'BOT_WEBHOOK_SECRET', '')
    if secret and request.headers.get('X-Telegram-Bot-Api-Secret-Token') != secret:
        return HttpResponse('Forbidden', status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        update = types.Update.model_validate(payload)
        await dp.feed_update(bot, update)
    except Exception:
        return HttpResponse('Bad Request', status=400)

    return HttpResponse('OK')
