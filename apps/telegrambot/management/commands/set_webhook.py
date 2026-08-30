from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegrambot.client import TelegramClient, TelegramError


class Command(BaseCommand):
    help = "Зарегистрировать вебхук в Telegram (локально — через ngrok/cloudflared)."

    def add_arguments(self, parser):
        parser.add_argument(
            "base_url",
            help="Публичный адрес backend, например https://example.trycloudflare.com",
        )

    def handle(self, *args, **options):
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        if not secret:
            raise CommandError("Задайте TELEGRAM_WEBHOOK_SECRET в .env")

        base_url = options["base_url"].rstrip("/")
        url = f"{base_url}/api/telegram/webhook/{secret}/"

        client = TelegramClient()
        try:
            bot = client.get_me()
            client.set_webhook(url, secret_token=secret)
        except TelegramError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Вебхук установлен для @{bot['username']}"))
        self.stdout.write(f"  {url}")
