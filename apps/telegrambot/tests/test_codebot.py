"""Команда codebot: цикл длинного опроса.

Сеть здесь не используется — клиент подменяется. Проверяется именно логика
цикла: сдвиг offset, устойчивость к ошибкам и снятие вебхука.
"""

from __future__ import annotations

from contextlib import suppress

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.telegrambot.management.commands import codebot as codebot_module
from apps.users.models import AuthTokenStatus, TelegramAuthToken
from apps.users.tests.factories import callback_update, start_update

pytestmark = pytest.mark.django_db


class FakeClient:
    """Телеграм, отдающий заранее заданные пачки апдейтов."""

    def __init__(self, batches, webhook_url=""):
        self.batches = list(batches)
        self.webhook_url = webhook_url
        self.offsets: list[int | None] = []
        self.webhook_deleted = False
        self.is_configured = True

    def get_me(self):
        return {"username": "CodeCupBot"}

    def get_webhook_info(self):
        return {"url": self.webhook_url}

    def delete_webhook(self):
        self.webhook_deleted = True
        return {}

    def get_updates(self, offset, timeout):
        self.offsets.append(offset)
        if not self.batches:
            raise KeyboardInterrupt  # выходим из цикла в тесте
        return self.batches.pop(0)


def _run(client, **options) -> None:
    """Запускает команду с подменённым клиентом и останавливает её."""
    command = codebot_module.Command()
    command.stdout = type("Sink", (), {"write": lambda self, *a, **k: None})()
    command.style = type("Style", (), {"SUCCESS": str, "WARNING": str, "ERROR": str})()

    # FakeClient бросает KeyboardInterrupt, когда апдейты кончились — так
    # цикл завершается ровно тем же путём, что и по Ctrl+C.
    with suppress(KeyboardInterrupt):
        command.handle(timeout=1, keep_webhook=False, **options)


@pytest.fixture
def patched(monkeypatch):
    def install(client):
        monkeypatch.setattr(codebot_module, "TelegramClient", lambda *a, **k: client)
        return client

    return install


def test_updates_are_handled_through_the_same_code_as_the_webhook(patched) -> None:
    """Опрос и вебхук обязаны вести себя одинаково — обработчик у них общий."""
    token, _ = TelegramAuthToken.issue()
    client = patched(FakeClient([[callback_update("confirm", token.nonce)]]))

    _run(client)

    token.refresh_from_db()
    assert token.status == AuthTokenStatus.CONFIRMED


def test_offset_advances_past_processed_updates(patched) -> None:
    client = patched(FakeClient([[start_update(), {"update_id": 5, "message": {}}], []]))

    _run(client)

    # Первый запрос без offset, следующий — за последним update_id.
    assert client.offsets[0] is None
    assert client.offsets[1] == 6


def test_a_failing_update_does_not_stop_the_bot(patched, monkeypatch) -> None:
    """Иначе одна кривая полезная нагрузка вешала бы бота до перезапуска."""
    calls = {"count": 0}

    def explode(update):
        calls["count"] += 1
        raise ValueError("сломанный апдейт")

    monkeypatch.setattr(codebot_module, "handle_update", explode)
    client = patched(FakeClient([[{"update_id": 1}, {"update_id": 2}], []]))

    _run(client)

    assert calls["count"] == 2
    assert client.offsets[-1] == 3


def test_webhook_is_removed_before_polling(patched) -> None:
    """Telegram не отдаёт getUpdates, пока висит вебхук, — он ответит 409."""
    client = patched(FakeClient([[]], webhook_url="https://api.codecup.tech/hook/"))

    _run(client)

    assert client.webhook_deleted


def test_webhook_is_kept_when_asked(patched) -> None:
    client = patched(FakeClient([[]], webhook_url="https://api.codecup.tech/hook/"))

    command = codebot_module.Command()
    command.stdout = type("Sink", (), {"write": lambda self, *a, **k: None})()
    command.style = type("Style", (), {"SUCCESS": str, "WARNING": str, "ERROR": str})()
    with suppress(KeyboardInterrupt):
        command.handle(timeout=1, keep_webhook=True)

    assert not client.webhook_deleted


def test_missing_token_fails_with_a_clear_message(settings) -> None:
    settings.TELEGRAM_BOT_TOKEN = ""

    with pytest.raises(CommandError, match="TELEGRAM_BOT_TOKEN"):
        call_command("codebot")
