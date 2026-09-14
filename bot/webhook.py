import asyncio

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from aiogram import Bot
from aiogram.types import Update

from .main import dp, BOT_TOKEN


@csrf_exempt
def telegram_webhook(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "error": "Only POST requests are allowed",
            },
            status=405,
        )

    secret = getattr(
        settings,
        "BOT_WEBHOOK_SECRET",
        "",
    )

    if secret:
        telegram_secret = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if telegram_secret != secret:
            return JsonResponse(
                {
                    "ok": False,
                    "error": "Forbidden",
                },
                status=403,
            )

    try:

        update_data = request.body.decode("utf-8")

        update = Update.model_validate_json(
            update_data,
            context={"bot": Bot},
        )

        async def process_update():

            bot = Bot(
                token=BOT_TOKEN,
            )

            try:
                await dp.feed_update(
                    bot,
                    update,
                )
            finally:
                await bot.session.close()

        asyncio.run(process_update())

        return JsonResponse(
            {
                "ok": True,
            }
        )

    except Exception as e:

        print(
            "Telegram webhook error: "
            f"{type(e).__name__}: {e}"
        )

        return JsonResponse(
            {
                "ok": False,
                "error": "Webhook processing failed",
            },
            status=500,
        )

     
