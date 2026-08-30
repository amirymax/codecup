"""Обработка апдейтов Telegram.

Разделено с view намеренно: тесты гоняют эти функции на реальных payload-ах
Bot API, не поднимая HTTP-слой.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from apps.users.models import AuthTokenStatus, TelegramAuthToken, User

from . import messages
from .client import send_message_safely

logger = logging.getLogger(__name__)


def handle_update(update: dict[str, Any]) -> None:
    if "message" in update:
        _handle_message(update["message"])
    elif "callback_query" in update:
        _handle_callback_query(update["callback_query"])


def _handle_message(message: dict[str, Any]) -> None:
    text = (message.get("text") or "").strip()
    chat_id = message["chat"]["id"]

    if not text.startswith("/start"):
        return

    payload = text[len("/start") :].strip()
    if not payload:
        send_message_safely(chat_id, messages.WELCOME)
        return

    token = TelegramAuthToken.objects.filter(nonce=payload).first()
    if token is None or not token.is_confirmable:
        send_message_safely(chat_id, messages.LINK_EXPIRED)
        return

    send_message_safely(
        chat_id,
        messages.CONFIRM_PROMPT,
        reply_markup=messages.confirm_keyboard(token.nonce),
    )


def _handle_callback_query(query: dict[str, Any]) -> None:
    from .client import TelegramClient, TelegramError

    data = query.get("data") or ""
    action, _, nonce = data.partition(":")
    if action not in {"confirm", "cancel"} or not nonce:
        return

    message = query.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    client = TelegramClient()

    def answer(text: str) -> None:
        try:
            client.answer_callback_query(query["id"], text)
        except TelegramError:
            logger.exception("Не удалось ответить на callback_query")

    def replace_prompt(text: str) -> None:
        """Заменяет сообщение с кнопками, чтобы нельзя было нажать дважды."""
        if chat_id is None or "message_id" not in message:
            return
        try:
            client.edit_message_text(chat_id, message["message_id"], text)
        except TelegramError:
            logger.exception("Не удалось обновить сообщение подтверждения")

    with transaction.atomic():
        token = TelegramAuthToken.objects.select_for_update().filter(nonce=nonce).first()
        if token is None or not token.is_confirmable:
            already = token is not None and token.status in {
                AuthTokenStatus.CONFIRMED,
                AuthTokenStatus.CONSUMED,
            }
            answer(messages.CALLBACK_EXPIRED)
            replace_prompt(messages.ALREADY_HANDLED if already else messages.LINK_EXPIRED)
            return

        if action == "cancel":
            token.cancel()
            answer(messages.CALLBACK_CANCELLED)
            replace_prompt(messages.LOGIN_CANCELLED)
            return

        user, _ = User.objects.get_or_create_from_telegram(query["from"])
        token.confirm(user)

    answer(messages.CALLBACK_CONFIRMED)
    replace_prompt(messages.LOGIN_CONFIRMED)
