import asyncio
import os

from django.core.management.base import BaseCommand, CommandError

from aiogram import Bot


class Command(BaseCommand):
    help = 'Configure the Telegram webhook for the deployed application.'

    def handle(self, *args, **options):
        token = os.getenv('BOT_TOKEN', '').strip()
        if not token:
            raise CommandError('BOT_TOKEN environment variable is missing.')

        external_url = os.getenv('RENDER_EXTERNAL_URL', '').strip().rstrip('/')
        webhook_url = os.getenv('BOT_WEBHOOK_URL', '').strip().rstrip('/')
        if not webhook_url:
            if not external_url:
                raise CommandError('Set RENDER_EXTERNAL_URL or BOT_WEBHOOK_URL before deployment.')
            webhook_url = f'{external_url}/telegram/webhook/'

        secret = os.getenv('BOT_WEBHOOK_SECRET', '').strip()
        if not secret:
            raise CommandError('BOT_WEBHOOK_SECRET environment variable is missing.')

        async def configure():
            bot = Bot(token=token)
            try:
                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=secret,
                    drop_pending_updates=False,
                    allowed_updates=['message', 'callback_query'],
                )
                info = await bot.get_webhook_info()
                return info.url
            finally:
                await bot.session.close()

        final_url = asyncio.run(configure())
        self.stdout.write(self.style.SUCCESS(f'Telegram webhook configured: {final_url}'))
