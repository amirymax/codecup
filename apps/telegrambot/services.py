"""Обработка апдейтов Telegram.

Разделено с view намеренно: тесты гоняют эти функции на реальных payload-ах
Bot API, не поднимая HTTP-слой.
"""

from __future__ import annotations

import logging
from contextlib import suppress
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

    # Фото или файл от того, кто обещал прислать чек, — это чек.
    if "photo" in message or "document" in message:
        _handle_receipt(message)
        return

    # Ответ на запрос причины отказа — это решение администратора, а не
    # обычное сообщение, поэтому проверяем до всего остального.
    reply_to = (message.get("reply_to_message") or {}).get("message_id")
    if reply_to and _handle_rejection_reason(message, reply_to, text):
        return

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
    action, _, payload = data.partition(":")

    if action in {"pay_ok", "pay_no"} and payload:
        _handle_payment_decision(query, action, payload)
        return

    nonce = payload
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


def _handle_receipt(message: dict[str, Any]) -> None:
    """Фото или документ от участника, от которого ждут чек."""
    from apps.payments.models import EntryPayment, PaymentStatus
    from apps.telegrambot.payments import download_receipt, forward_receipt_to_admin
    from apps.users.models import User

    chat_id = message["chat"]["id"]
    sender = message.get("from") or {}

    user = User.objects.filter(telegram_id=sender.get("id")).first()
    if user is None:
        send_message_safely(chat_id, messages.RECEIPT_NOT_EXPECTED)
        return

    payment = (
        EntryPayment.objects.filter(user=user, expects_receipt_in_bot=True)
        .select_related("contest")
        .order_by("-created_at")
        .first()
    )
    if payment is None:
        # Чек уже прислан с сайта — второй не нужен, и человеку это лучше
        # объяснить, чем отвечать «мы от вас чек не ждём».
        pending = EntryPayment.objects.filter(user=user, status=PaymentStatus.PENDING).exists()
        send_message_safely(
            chat_id,
            messages.RECEIPT_ALREADY_PENDING if pending else messages.RECEIPT_NOT_EXPECTED,
        )
        return

    file_id, kind = _extract_file(message)
    if not file_id:
        send_message_safely(chat_id, messages.RECEIPT_WRONG_FORMAT)
        return

    payment.attach_receipt(telegram_file_id=file_id, kind=kind)
    send_message_safely(chat_id, messages.RECEIPT_RECEIVED)
    # Копию кладём к себе, чтобы чек был виден и в админ-панели, а не только
    # в переписке администратора.
    download_receipt(payment)
    forward_receipt_to_admin(payment)


def _extract_file(message: dict[str, Any]) -> tuple[str, str]:
    """id файла и его тип. Из фото берём самый крупный размер."""
    if photos := message.get("photo"):
        return photos[-1]["file_id"], "photo"

    document = message.get("document") or {}
    mime = (document.get("mime_type") or "").lower()
    if document and (mime.startswith("image/") or mime == "application/pdf"):
        return document["file_id"], "document"

    return "", ""


def _handle_payment_decision(query: dict[str, Any], action: str, payment_id: str) -> None:
    """Кнопки «Принять» и «Отклонить» под пересланным чеком."""
    from apps.payments.models import EntryPayment
    from apps.telegrambot.payments import close_admin_decision_message, notify_participant
    from apps.users.models import User

    from .client import TelegramClient, TelegramError

    client = TelegramClient()
    reviewer = User.objects.filter(telegram_id=(query.get("from") or {}).get("id")).first()

    def answer(text: str) -> None:
        with suppress(TelegramError):
            client.answer_callback_query(query["id"], text)

    # Решать может только сотрудник: кнопку могли переслать кому угодно.
    if reviewer is None or not reviewer.is_staff:
        answer(messages.CALLBACK_EXPIRED)
        return

    payment = EntryPayment.objects.filter(pk=payment_id).select_related("contest", "user").first()
    if payment is None:
        answer(messages.CALLBACK_EXPIRED)
        return

    if not payment.is_under_review:
        answer(messages.REJECT_ALREADY_DECIDED)
        return

    # Отказ без объяснения участнику ничего не говорит, поэтому сначала
    # спрашиваем причину и ждём ответа на запрос.
    if action == "pay_no":
        _ask_rejection_reason(query, payment)
        answer(messages.CALLBACK_ASK_REASON)
        return

    payment.accept(reviewer)
    answer(messages.ADMIN_DECISION_ACCEPTED)

    message = query.get("message") or {}
    close_admin_decision_message(
        payment,
        chat_id=(message.get("chat") or {}).get("id"),
        message_id=message.get("message_id"),
    )

    notify_participant(payment)


def _ask_rejection_reason(query: dict[str, Any], payment) -> None:
    """Просит администратора написать причину ответом на сообщение."""
    from .client import TelegramClient, TelegramError

    chat_id = ((query.get("message") or {}).get("chat") or {}).get("id")
    if not chat_id:
        return

    try:
        sent = TelegramClient().send_message(
            chat_id,
            messages.REJECT_ASK_REASON,
            reply_markup={"force_reply": True, "input_field_placeholder": "Причина отказа"},
        )
    except TelegramError:
        logger.exception("Не удалось запросить причину отказа по чеку %s", payment.id)
        return

    if sent.get("message_id"):
        payment.wait_for_rejection_reason(sent["message_id"])


def _handle_rejection_reason(message: dict[str, Any], prompt_id: int, text: str) -> bool:
    """Ответ на запрос причины. Возвращает True, если сообщение было им."""
    from apps.payments.models import EntryPayment
    from apps.telegrambot.payments import close_admin_decision_message, notify_participant
    from apps.users.models import User

    payment = (
        EntryPayment.objects.filter(rejection_prompt_message_id=prompt_id)
        .select_related("contest", "user")
        .first()
    )
    if payment is None:
        return False

    chat_id = message["chat"]["id"]
    reviewer = User.objects.filter(telegram_id=(message.get("from") or {}).get("id")).first()
    if reviewer is None or not reviewer.is_staff:
        return False

    if not payment.is_under_review:
        # Пока админ печатал, решение приняли на сайте.
        send_message_safely(chat_id, messages.REJECT_ALREADY_DECIDED)
        return True

    reason = "" if text in messages.REJECT_REASON_SKIPPED else text
    payment.reject(reviewer, reason)

    close_admin_decision_message(payment)
    notify_participant(payment)
    send_message_safely(chat_id, messages.rejection_saved(payment))
    return True
