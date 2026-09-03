"""Чек уходит администратору в Telegram файлом, а не одним текстом."""

from __future__ import annotations

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.telegrambot.payments import forward_receipt_to_admin
from apps.users.tests.factories import AdminFactory

from .factories import PaidContestFactory, PaymentFactory

pytestmark = pytest.mark.django_db

PNG = b"\x89PNG\r\n\x1a\n" + b"cheque" * 8
PDF = b"%PDF-1.4 cheque"


@pytest.fixture
def notified_admin(settings):
    """Администратор, которому бот шлёт чеки."""
    admin = AdminFactory(telegram_username="payments_admin")
    settings.TELEGRAM_ADMIN_USERNAME = "payments_admin"
    return admin


def _payment_with_file(name: str, content: bytes):
    payment = PaymentFactory()
    payment.receipt.save(name, ContentFile(content), save=True)
    return payment


def test_receipt_uploaded_on_the_site_reaches_the_admin_as_a_file(
    notified_admin, no_telegram_calls
) -> None:
    """Раньше сюда уходила ссылка на домен фронтенда, где media нет."""
    payment = _payment_with_file("cheque.png", PNG)

    forward_receipt_to_admin(payment)

    method, sent = no_telegram_calls[-1]
    assert method == "sendPhoto"
    assert sent["content"] == PNG
    assert sent["chat_id"] == notified_admin.telegram_id


def test_a_pdf_receipt_goes_as_a_document(notified_admin, no_telegram_calls) -> None:
    payment = _payment_with_file("cheque.pdf", PDF)

    forward_receipt_to_admin(payment)

    method, sent = no_telegram_calls[-1]
    assert method == "sendDocument"
    assert sent["content"] == PDF


def test_the_file_carries_the_caption_and_the_decision_buttons(
    notified_admin, no_telegram_calls
) -> None:
    """Иначе админу нечем принять или отклонить взнос прямо в чате."""
    payment = _payment_with_file("cheque.png", PNG)

    forward_receipt_to_admin(payment)

    _, sent = no_telegram_calls[-1]
    assert payment.user.display_name in sent["caption"]
    assert sent["reply_markup"]["inline_keyboard"]


def test_receipt_sent_through_the_bot_is_forwarded_by_file_id(
    notified_admin, no_telegram_calls
) -> None:
    payment = PaymentFactory(telegram_file_id="AgACphoto", receipt_kind="photo")

    forward_receipt_to_admin(payment)

    method, sent = no_telegram_calls[-1]
    assert method == "sendPhoto"
    assert sent["photo"] == "AgACphoto"


def test_without_any_receipt_the_admin_still_gets_a_message(
    notified_admin, no_telegram_calls
) -> None:
    payment = PaymentFactory()

    forward_receipt_to_admin(payment)

    method, _ = no_telegram_calls[-1]
    assert method == "sendMessage"


def test_uploading_from_the_site_sends_the_file_right_away(
    client: APIClient, participant, notified_admin, no_telegram_calls
) -> None:
    """Проверка всего пути: участник загрузил чек — админ получил файл."""
    contest = PaidContestFactory()

    response = client.post(
        reverse("upload-receipt", args=[contest.slug]),
        {"receipt": ContentFile(PNG, name="cheque.png")},
        format="multipart",
    )

    assert response.status_code == 200
    method, sent = no_telegram_calls[-1]
    assert method == "sendPhoto"
    assert sent["content"] == PNG
