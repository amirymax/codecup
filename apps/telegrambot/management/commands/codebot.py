"""Запуск Telegram-бота длинным опросом: python3 manage.py codebot"""

from __future__ import annotations

import logging
import signal
import time
from typing import Any

import httpx
from django.core.management.base import BaseCommand, CommandError

from apps.telegrambot.client import TelegramClient, TelegramError
from apps.telegrambot.services import handle_update

logger = logging.getLogger(__name__)

# Пауза после сетевой ошибки, чтобы не долбить API в цикле.
RETRY_DELAY_SECONDS = 3


class Command(BaseCommand):
    help = "Запустить Telegram-бота (длинный опрос). Для продакшна есть вебхук."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Сколько секунд Telegram держит соединение без апдейтов (по умолчанию 30).",
        )
        parser.add_argument(
            "--keep-webhook",
            action="store_true",
            help="Не снимать вебхук перед запуском (по умолчанию снимается).",
        )

    def handle(self, *args, **options):
        client = TelegramClient()
        if not client.is_configured:
            raise CommandError("TELEGRAM_BOT_TOKEN не задан — заполните .env")

        try:
            bot = client.get_me()
        except (TelegramError, httpx.HTTPError) as exc:
            raise CommandError(f"Не удалось подключиться к Telegram: {exc}") from exc

        # Telegram не отдаёт апдейты опросом, пока установлен вебхук:
        # getUpdates ответит 409. Поэтому по умолчанию снимаем его.
        if not options["keep_webhook"]:
            self._drop_webhook(client)

        self._install_signal_handlers()

        self.stdout.write(self.style.SUCCESS(f"Бот @{bot['username']} запущен."))
        self.stdout.write(f"  Ссылка для входа: https://t.me/{bot['username']}?start=<код>")
        self.stdout.write("  Остановка — Ctrl+C\n")
        # Под systemd и в Docker вывод уходит в файл и буферизуется:
        # без сброса бот кажется зависшим, хотя уже работает.
        self.stdout.flush()

        self._poll(client, timeout=options["timeout"])

        self.stdout.write(self.style.SUCCESS("Бот остановлен."))
        self.stdout.flush()

    # --- цикл опроса ----------------------------------------------------

    def _poll(self, client: TelegramClient, timeout: int) -> None:
        offset: int | None = None

        while self.running:
            try:
                updates = client.get_updates(offset=offset, timeout=timeout)
            except (TelegramError, httpx.HTTPError) as exc:
                # Обрыв связи не должен ронять бота: ждём и пробуем снова.
                logger.warning("Опрос Telegram не удался: %s", exc)
                self._sleep(RETRY_DELAY_SECONDS)
                continue

            for update in updates:
                # Сдвигаем offset до обработки: иначе апдейт, на котором
                # обработчик упал, будет приходить снова и снова.
                offset = update["update_id"] + 1
                self._process(update)

    def _process(self, update: dict[str, Any]) -> None:
        try:
            handle_update(update)
        except Exception:
            logger.exception("Ошибка обработки апдейта %s", update.get("update_id"))

    # --- служебное ------------------------------------------------------

    def _drop_webhook(self, client: TelegramClient) -> None:
        try:
            info = client.get_webhook_info()
            if info.get("url"):
                client.delete_webhook()
                self.stdout.write(self.style.WARNING(f"Вебхук снят: {info['url']}"))
        except (TelegramError, httpx.HTTPError) as exc:
            logger.warning("Не удалось проверить вебхук: %s", exc)

    def _install_signal_handlers(self) -> None:
        """Ctrl+C и SIGTERM должны останавливать бота, а не рвать его."""

        def stop(signum, frame):
            if self.running:
                self.running = False
                self.stdout.write("\nОстанавливаюсь, дождитесь текущего запроса…")

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

    def _sleep(self, seconds: float) -> None:
        """Прерываемая пауза: сигнал не должен ждать её окончания."""
        deadline = time.monotonic() + seconds
        while self.running and time.monotonic() < deadline:
            time.sleep(0.2)
