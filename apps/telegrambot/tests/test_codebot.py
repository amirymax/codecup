"""Команда codebot: цикл опроса и его устойчивость.

Сеть здесь не задействована — клиент подменяется заглушкой, поэтому тесты
проходят и без токена бота.
"""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError

from apps.telegrambot.management.commands import codebot as codebot_module
from apps.users.models import AuthTokenStatus, TelegramAuthToken, User
from apps.users.tests.factories import callback_update, start_update

pytestmark = pytest.mark.django_db


class FakeClient:
    """Заглушка Bot API: отдаёт заранее заданные пачки апдейтов."""

    def __init__(self, batches, *, fail_times=0):
        self.batches = list(batches)
        self.fail_times = fail_times
        self.calls: list[tuple[str, dict]] = []
        self.offsets: list[int | None] = []
        self.webhook_deleted = False
        self.command = None

    is_configured = True

    def get_me(self):
        return {"username": "Code_Cup_Bot"}

    def get_webhook_info(self):
        return {"url": "https://example.test/hook"}

    def delete_webhook(self):
        self.webhook_deleted = True
        return {}

    def get_updates(self, offset, timeout):
        self.offsets.append(offset)

        if self.fail_times > 0:
            self.fail_times -= 1
            import httpx

            raise httpx.ConnectError("сеть недоступна")

        if not self.batches:
            # Апдейты кончились — просим команду завершиться.
            self.command.running = False
            return []
        return self.batches.pop(0)

    # методы, которые дёргает обработчик апдейтов
    def call(self, method, **payload):
        self.calls.append((method, payload))
        return {"message_id": 1}


@pytest.fixture
def run_bot(monkeypatch):
    """Запускает codebot с подменённым клиентом и возвращает заглушку."""

    def run(batches, **options):
        fake = FakeClient(batches, fail_times=options.pop("fail_times", 0))

        monkeypatch.setattr(codebot_module, "TelegramClient", lambda: fake)
        monkeypatch.setattr("apps.telegrambot.client.TelegramClient.call", fake.call)
        monkeypatch.setattr(codebot_module.Command, "_sleep", lambda self, seconds: None)

        original_handle = codebot_module.Command.handle

        def handle(command_self, *args, **kwargs):
            fake.command = command_self
            return original_handle(command_self, *args, **kwargs)

        monkeypatch.setattr(codebot_module.Command, "handle", handle)
        call_command("codebot", **options)
        return fake

    return run


def _issue() -> TelegramAuthToken:
    token, _ = TelegramAuthToken.issue()
    return token


# --- запуск ----------------------------------------------------------------


def test_refuses_to_start_without_a_token(monkeypatch, settings) -> None:
    settings.TELEGRAM_BOT_TOKEN = ""

    with pytest.raises(CommandError, match="TELEGRAM_BOT_TOKEN"):
        call_command("codebot")


def test_removes_the_webhook_before_polling(run_bot) -> None:
    """Telegram не отдаёт апдейты опросом, пока установлен вебхук."""
    fake = run_bot([])

    assert fake.webhook_deleted


def test_keep_webhook_leaves_it_alone(run_bot) -> None:
    fake = run_bot([], keep_webhook=True)

    assert not fake.webhook_deleted


# --- обработка апдейтов ----------------------------------------------------


def test_start_with_a_nonce_prompts_for_confirmation(run_bot) -> None:
    token = _issue()

    fake = run_bot([[{**start_update(token.nonce), "update_id": 1}]])

    sent = [payload for method, payload in fake.calls if method == "sendMessage"]
    assert sent
    assert sent[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == (
        f"confirm:{token.nonce}"
    )


def test_confirming_through_polling_logs_the_user_in(run_bot) -> None:
    """Тот же результат, что и через вебхук: обработчик у них общий."""
    token = _issue()

    run_bot(
        [
            [{**start_update(token.nonce), "update_id": 1}],
            [{**callback_update("confirm", token.nonce), "update_id": 2}],
        ]
    )

    token.refresh_from_db()
    assert token.status == AuthTokenStatus.CONFIRMED
    assert token.user == User.objects.get()


# --- устойчивость ----------------------------------------------------------


def test_offset_advances_past_a_failing_update(run_bot, monkeypatch) -> None:
    """Иначе «ядовитый» апдейт возвращался бы бесконечно."""

    def boom(update):
        raise ValueError("сломанный апдейт")

    monkeypatch.setattr(codebot_module, "handle_update", boom)

    fake = run_bot([[{**start_update(), "update_id": 7}]])

    # Следующий запрос ушёл уже со сдвинутым offset.
    assert fake.offsets[-1] == 8


def test_network_errors_are_retried_not_fatal(run_bot) -> None:
    token = _issue()

    fake = run_bot([[{**start_update(token.nonce), "update_id": 1}]], fail_times=2)

    # Два обрыва, затем успешный запрос — и апдейт всё-таки обработан.
    assert len(fake.offsets) >= 3
    assert any(method == "sendMessage" for method, _ in fake.calls)


def test_every_update_gets_a_fresh_database_connection(run_bot, monkeypatch) -> None:
    """В цикле опроса нет запроса-ответа, поэтому соединение обновляем сами.

    Иначе одно соединение висит сутками, умирает по таймауту на той стороне,
    и дальше каждый апдейт падает с «the connection is closed» — при живом на
    вид процессе, который systemd не станет перезапускать.
    """
    events: list[str] = []
    monkeypatch.setattr(codebot_module, "close_old_connections", lambda: events.append("db"))
    monkeypatch.setattr(codebot_module, "handle_update", lambda update: events.append("update"))

    run_bot([[{"update_id": 1}, {"update_id": 2}]])

    assert events == ["db", "update", "db", "db", "update", "db"]


def test_connection_is_released_even_when_the_update_fails(run_bot, monkeypatch) -> None:
    """Иначе умершее соединение осталось бы висеть до конца жизни процесса."""
    events: list[str] = []
    monkeypatch.setattr(codebot_module, "close_old_connections", lambda: events.append("db"))

    def boom(update):
        raise OperationalError("the connection is closed")

    monkeypatch.setattr(codebot_module, "handle_update", boom)

    run_bot([[{**start_update(), "update_id": 7}]])

    assert events == ["db", "db"]


def test_first_request_starts_without_an_offset(run_bot) -> None:
    fake = run_bot([])

    assert fake.offsets[0] is None
