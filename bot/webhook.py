```python
import asyncio

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from aiogram.types import Update

from .main import bot, dp


# Aiogram uchun doimiy event loop
_loop = asyncio.new_event_loop()


@csrf_exempt
def telegram_webhook(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "error": "Only POST requests are allowed"
            },
            status=405
        )

    # Telegram webhook secret tekshirish
    secret = getattr(
        settings,
        "BOT_WEBHOOK_SECRET",
        ""
    )

    if secret:

        telegram_secret = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if telegram_secret != secret:

            return JsonResponse(
                {
                    "ok": False,
                    "error": "Forbidden"
                },
                status=403
            )

    try:

        # Telegram JSON
        update_data = request.body.decode("utf-8")

        # Aiogram Update obyektini yaratish
        update = Update.model_validate_json(
            update_data,
            context={
                "bot": bot
            }
        )

        # Aiogram handlerlarini ishga tushirish
        _loop.run_until_complete(
            dp.feed_update(
                bot,
                update
            )
        )

        return JsonResponse(
            {
                "ok": True
            }
        )

    except Exception as e:

        print(
            f"Telegram webhook error: "
            f"{type(e).__name__}: {e}"
        )

        return JsonResponse(
            {
                "ok": False,
                "error": "Webhook processing failed"
            },
            status=500
        )
```
