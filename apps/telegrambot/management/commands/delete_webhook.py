from django.core.management.base import BaseCommand, CommandError

from apps.telegrambot.client import TelegramClient, TelegramError


class Command(BaseCommand):
    help = "Удалить вебхук в Telegram."

    def handle(self, *args, **options):
        try:
            TelegramClient().delete_webhook()
        except TelegramError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Вебхук удалён."))
