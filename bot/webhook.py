from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aiogram.types import Update

from .main import bot, dp


@csrf_exempt
async def telegram_webhook(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "error": "Only POST requests are allowed"
            },
            status=405
        )

    try:

        update_data = request.body.decode("utf-8")

        update = Update.model_validate_json(
            update_data,
            context={"bot": bot}
        )

        await dp.feed_update(
            bot,
            update
        )

        return JsonResponse(
            {"ok": True}
        )

    except Exception as e:

        print(
            f"Telegram webhook error: {type(e).__name__}: {e}"
        )

        return JsonResponse(
            {
                "ok": False,
                "error": "Webhook processing failed"
            },
            status=500
        )
