"""Граница вебхука: что принимаем, что отвергаем, что отвечаем Telegram."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.telegrambot import messages
from apps.users.models import AuthTokenStatus, TelegramAuthToken, User
from apps.users.tests.factories import callback_update, start_update

pytestmark = pytest.mark.django_db

SECRET = "webhook-secret"


def _post(client: APIClient, update: dict, *, path_secret=None, header_secret=SECRET):
    url = reverse("telegram-webhook", args=[path_secret or SECRET])
    headers = {}
    if header_secret is not None:
        headers["HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN"] = header_secret
    return client.post(url, update, format="json", **headers)


def _issue() -> TelegramAuthToken:
    token, _ = TelegramAuthToken.issue()
    return token


def _texts(calls) -> list[str]:
    return [payload.get("text", "") for method, payload in calls if method == "sendMessage"]


# --- проверка секрета ------------------------------------------------------


def test_wrong_secret_in_the_path_is_rejected(client: APIClient) -> None:
    assert _post(client, start_update(), path_secret="wrong").status_code == 403


def test_missing_secret_header_is_rejected(client: APIClient) -> None:
    assert _post(client, start_update(), header_secret=None).status_code == 403


def test_wrong_secret_header_is_rejected(client: APIClient) -> None:
    assert _post(client, start_update(), header_secret="wrong").status_code == 403


def test_webhook_is_disabled_when_no_secret_is_configured(client, settings) -> None:
    settings.TELEGRAM_WEBHOOK_SECRET = ""

    assert _post(client, start_update()).status_code == 403


# --- /start ----------------------------------------------------------------


def test_bare_start_greets_the_user(client: APIClient, no_telegram_calls) -> None:
    _post(client, start_update())

    assert messages.WELCOME in _texts(no_telegram_calls)


def test_start_with_a_valid_nonce_offers_the_confirm_button(client, no_telegram_calls) -> None:
    token = _issue()

    _post(client, start_update(token.nonce))

    method, payload = no_telegram_calls[-1]
    assert method == "sendMessage"
    assert payload["text"] == messages.CONFIRM_PROMPT
    buttons = payload["reply_markup"]["inline_keyboard"]
    assert buttons[0][0]["callback_data"] == f"confirm:{token.nonce}"
    assert buttons[1][0]["callback_data"] == f"cancel:{token.nonce}"


def test_start_with_an_unknown_nonce_says_the_link_expired(client, no_telegram_calls) -> None:
    _post(client, start_update("нет-такого-кода"))

    assert messages.LINK_EXPIRED in _texts(no_telegram_calls)


def test_non_start_messages_are_ignored(client: APIClient, no_telegram_calls) -> None:
    update = start_update()
    update["message"]["text"] = "просто сообщение"

    assert _post(client, update).status_code == 200
    assert no_telegram_calls == []


# --- нажатия кнопок --------------------------------------------------------


def test_confirm_creates_the_user_and_marks_the_token(client, no_telegram_calls) -> None:
    token = _issue()

    _post(client, callback_update("confirm", token.nonce))

    token.refresh_from_db()
    assert token.status == AuthTokenStatus.CONFIRMED
    assert token.user == User.objects.get()
    assert any(method == "answerCallbackQuery" for method, _ in no_telegram_calls)


def test_confirm_replaces_the_prompt_so_it_cannot_be_pressed_twice(client, no_telegram_calls):
    token = _issue()

    _post(client, callback_update("confirm", token.nonce))

    edits = [p for method, p in no_telegram_calls if method == "editMessageText"]
    assert edits and edits[-1]["text"] == messages.LOGIN_CONFIRMED


def test_second_confirm_does_not_reopen_a_consumed_token(client, no_telegram_calls) -> None:
    token = _issue()
    _post(client, callback_update("confirm", token.nonce))
    token.refresh_from_db()
    token.consume()

    _post(client, callback_update("confirm", token.nonce))

    token.refresh_from_db()
    assert token.status == AuthTokenStatus.CONSUMED


def test_cancel_marks_the_token_and_creates_no_user(client, no_telegram_calls) -> None:
    token = _issue()

    _post(client, callback_update("cancel", token.nonce))

    token.refresh_from_db()
    assert token.status == AuthTokenStatus.CANCELLED
    assert not User.objects.exists()


def test_unknown_callback_action_is_ignored(client: APIClient, no_telegram_calls) -> None:
    token = _issue()

    _post(client, callback_update("подозрительно", token.nonce))

    token.refresh_from_db()
    assert token.status == AuthTokenStatus.PENDING


# --- устойчивость ----------------------------------------------------------


def test_malformed_update_still_returns_200(client: APIClient) -> None:
    """Ошибка не должна заставлять Telegram повторять апдейт бесконечно."""
    assert _post(client, {"update_id": 1, "message": {}}).status_code == 200


def test_empty_update_is_accepted(client: APIClient) -> None:
    assert _post(client, {"update_id": 1}).status_code == 200


def test_bot_api_failure_does_not_break_the_webhook(client, monkeypatch) -> None:
    from apps.telegrambot.client import TelegramClient, TelegramError

    def boom(self, method, **payload):
        raise TelegramError("Bot API недоступен")

    monkeypatch.setattr(TelegramClient, "call", boom)

    assert _post(client, start_update()).status_code == 200
