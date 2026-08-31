"""Чеки в Telegram: приём от участника и решение администратора."""

from __future__ import annotations

import logging

import httpx
from django.conf import settings
from django.core.files.base import ContentFile

from apps.payments.models import EntryPayment, PaymentStatus

from . import messages
from .client import TelegramClient, TelegramError, send_message_safely

logger = logging.getLogger(__name__)


def admin_chat_id() -> int | None:
    """Куда слать чеки.

    Ищем администратора по @username из настроек. Так ссылка не завязана на
    числовой id, который меняется, если аккаунт пересоздали.
    """
    from apps.users.models import User

    username = settings.TELEGRAM_ADMIN_USERNAME
    admin = User.objects.filter(telegram_username__iexact=username).first()
    if admin is None:
        # Запасной вариант: любой сотрудник, который заходил через Telegram.
        admin = User.objects.filter(is_staff=True, telegram_id__isnull=False).first()
    if admin is None:
        logger.error("Некому отправить чек: администратор @%s не найден", username)
        return None
    return admin.telegram_id


def forward_receipt_to_admin(payment: EntryPayment) -> None:
    """Пересылает чек администратору с кнопками решения."""
    chat_id = admin_chat_id()
    if chat_id is None:
        return

    caption = messages.receipt_for_admin(payment)
    keyboard = messages.decision_keyboard(payment.id)
    client = TelegramClient()

    try:
        if payment.telegram_file_id:
            client.call(
                "sendPhoto" if payment.receipt_is_photo else "sendDocument",
                chat_id=chat_id,
                **{"photo" if payment.receipt_is_photo else "document": payment.telegram_file_id},
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        elif payment.receipt:
            client.call(
                "sendDocument",
                chat_id=chat_id,
                document=_absolute_receipt_url(payment),
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            client.send_message(chat_id, caption, reply_markup=keyboard)
    except (TelegramError, httpx.HTTPError, OSError):
        # Не смогли переслать файл — админ всё равно должен узнать о чеке.
        logger.exception("Не удалось переслать чек %s", payment.id)
        send_message_safely(chat_id, caption, reply_markup=keyboard)


def download_receipt(payment: EntryPayment) -> bool:
    """Скачивает присланный в бот файл к себе.

    Без этого чек существует только в переписке администратора, и в
    админ-панели его посмотреть нельзя. Если скачать не удалось, остаётся
    telegram_file_id — файл всё равно виден в чате.
    """
    if not payment.telegram_file_id or payment.receipt:
        return False

    client = TelegramClient()
    try:
        info = client.call("getFile", file_id=payment.telegram_file_id)
        remote_path = info["file_path"]
        url = f"{settings.TELEGRAM_API_URL}/file/bot{client.token}/{remote_path}"
        response = httpx.get(url, timeout=settings.TELEGRAM_REQUEST_TIMEOUT)
        response.raise_for_status()
    except (TelegramError, httpx.HTTPError, KeyError):
        logger.warning("Не удалось скачать чек %s из Telegram", payment.id)
        return False

    filename = remote_path.rsplit("/", 1)[-1]
    payment.receipt.save(filename, ContentFile(response.content), save=True)
    return True


def notify_participant(payment: EntryPayment) -> None:
    """Сообщает участнику решение по взносу."""
    if not payment.user.telegram_id:
        return

    if payment.status == PaymentStatus.ACCEPTED:
        text = messages.payment_accepted(payment)
    elif payment.status == PaymentStatus.REJECTED:
        text = messages.payment_rejected(payment)
    else:
        return

    send_message_safely(payment.user.telegram_id, text)


def _absolute_receipt_url(payment: EntryPayment) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}{payment.receipt.url}"
