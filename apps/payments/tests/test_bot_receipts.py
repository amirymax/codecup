"""Чеки в боте: приём от участника и решение администратора."""

from __future__ import annotations

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payments.models import PaymentStatus
from apps.users.tests.factories import AdminFactory, UserFactory

from .factories import PaymentFactory

pytestmark = pytest.mark.django_db


def _post(client: APIClient, update: dict):
    return client.post(
        reverse("telegram-webhook", args=[settings.TELEGRAM_WEBHOOK_SECRET]),
        update,
        format="json",
        HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=settings.TELEGRAM_WEBHOOK_SECRET,
    )


def _photo_update(telegram_id: int, file_id: str = "AgACphoto") -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 20,
            "date": 1_700_000_000,
            "chat": {"id": telegram_id, "type": "private"},
            "from": {"id": telegram_id, "is_bot": False, "first_name": "Тест"},
            "photo": [
                {"file_id": "small", "width": 90, "height": 90},
                {"file_id": file_id, "width": 800, "height": 800},
            ],
        },
    }


def _document_update(telegram_id: int, mime: str = "application/pdf") -> dict:
    return {
        "update_id": 2,
        "message": {
            "message_id": 21,
            "date": 1_700_000_000,
            "chat": {"id": telegram_id, "type": "private"},
            "from": {"id": telegram_id, "is_bot": False, "first_name": "Тест"},
            "document": {"file_id": "BQACdoc", "mime_type": mime, "file_name": "cheque.pdf"},
        },
    }


def _decision_update(telegram_id: int, action: str, payment_id: int) -> dict:
    return {
        "update_id": 3,
        "callback_query": {
            "id": "cb-pay",
            "from": {"id": telegram_id, "is_bot": False, "first_name": "Админ"},
            "data": f"{action}:{payment_id}",
            "message": {
                "message_id": 22,
                "date": 1_700_000_000,
                "chat": {"id": telegram_id, "type": "private"},
            },
        },
    }


# --- участник присылает чек ------------------------------------------------


def test_a_photo_from_a_waiting_participant_becomes_the_receipt(client, no_telegram_calls) -> None:
    user = UserFactory(telegram_id=4001)
    payment = PaymentFactory(user=user, expects_receipt_in_bot=True)

    _post(client, _photo_update(4001))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
    # Из набора размеров берём самый крупный.
    assert payment.telegram_file_id == "AgACphoto"
    assert payment.receipt_kind == "photo"


def test_a_pdf_is_accepted_too(client: APIClient, no_telegram_calls) -> None:
    user = UserFactory(telegram_id=4002)
    payment = PaymentFactory(user=user, expects_receipt_in_bot=True)

    _post(client, _document_update(4002))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
    assert payment.receipt_kind == "document"


def test_an_unsupported_document_is_refused(client: APIClient, no_telegram_calls) -> None:
    user = UserFactory(telegram_id=4003)
    payment = PaymentFactory(user=user, expects_receipt_in_bot=True)

    _post(client, _document_update(4003, mime="application/x-msdownload"))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.AWAITING_RECEIPT


def test_a_file_from_someone_not_expected_is_ignored(client, no_telegram_calls) -> None:
    """Иначе случайное фото в чат превращалось бы в чек."""
    user = UserFactory(telegram_id=4004)
    payment = PaymentFactory(user=user, expects_receipt_in_bot=False)

    _post(client, _photo_update(4004))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.AWAITING_RECEIPT
    assert not payment.telegram_file_id


def test_the_receipt_is_forwarded_to_the_admin(client, no_telegram_calls) -> None:
    AdminFactory(telegram_username="AmiriCode", telegram_id=9001)
    user = UserFactory(telegram_id=4005)
    PaymentFactory(user=user, expects_receipt_in_bot=True)

    _post(client, _photo_update(4005))

    sent_to_admin = [p for method, p in no_telegram_calls if p.get("chat_id") == 9001]
    assert sent_to_admin, "чек не ушёл администратору"
    assert sent_to_admin[0]["reply_markup"]["inline_keyboard"][0][0]["callback_data"].startswith(
        "pay_ok:"
    )


# --- администратор решает --------------------------------------------------


def test_admin_accepts_from_telegram(client: APIClient, no_telegram_calls) -> None:
    admin = AdminFactory(telegram_username="AmiriCode", telegram_id=9002)
    payment = PaymentFactory(status=PaymentStatus.PENDING)

    _post(client, _decision_update(9002, "pay_ok", payment.id))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.ACCEPTED
    assert payment.reviewed_by == admin


def test_admin_rejects_from_telegram(client: APIClient, no_telegram_calls) -> None:
    AdminFactory(telegram_username="AmiriCode", telegram_id=9003)
    payment = PaymentFactory(status=PaymentStatus.PENDING)

    _post(client, _decision_update(9003, "pay_no", payment.id))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.REJECTED


def test_a_participant_cannot_approve_their_own_payment(client, no_telegram_calls) -> None:
    """Кнопку можно переслать кому угодно, поэтому право проверяется заново."""
    user = UserFactory(telegram_id=4006)
    payment = PaymentFactory(user=user, status=PaymentStatus.PENDING)

    _post(client, _decision_update(4006, "pay_ok", payment.id))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING


def test_the_participant_is_told_about_the_decision(client, no_telegram_calls) -> None:
    AdminFactory(telegram_username="AmiriCode", telegram_id=9004)
    user = UserFactory(telegram_id=4007)
    payment = PaymentFactory(user=user, status=PaymentStatus.PENDING)

    _post(client, _decision_update(9004, "pay_ok", payment.id))

    told = [p for method, p in no_telegram_calls if p.get("chat_id") == 4007]
    assert told and "принят" in told[0]["text"]


def test_a_decision_on_a_missing_payment_is_harmless(client, no_telegram_calls) -> None:
    AdminFactory(telegram_username="AmiriCode", telegram_id=9005)

    assert _post(client, _decision_update(9005, "pay_ok", 999_999)).status_code == 200


# --- копия чека у себя ------------------------------------------------------


def test_a_telegram_receipt_is_downloaded_for_the_admin_panel(client, monkeypatch) -> None:
    """Иначе чек виден только в переписке, а в панели его не открыть."""
    import httpx

    from apps.telegrambot.client import TelegramClient

    monkeypatch.setattr(
        TelegramClient, "call", lambda self, method, **kw: {"file_path": "photos/file_7.jpg"}
    )
    # request обязателен: без него raise_for_status бросает RuntimeError,
    # чего у настоящего ответа не бывает.
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *a, **k: httpx.Response(
            200, content=b"receipt-bytes", request=httpx.Request("GET", "https://api.telegram.org")
        ),
    )

    user = UserFactory(telegram_id=4100)
    payment = PaymentFactory(user=user, expects_receipt_in_bot=True)

    _post(client, _photo_update(4100))

    payment.refresh_from_db()
    assert payment.receipt
    assert payment.receipt.read() == b"receipt-bytes"


def test_a_failed_download_still_keeps_the_receipt(client, monkeypatch, no_telegram_calls) -> None:
    """Сеть подвела — чек всё равно принят, file_id остаётся."""
    import httpx

    from apps.telegrambot.client import TelegramClient

    def boom(self, method, **kw):
        raise httpx.ConnectError("нет сети")

    monkeypatch.setattr(TelegramClient, "call", boom)

    user = UserFactory(telegram_id=4101)
    payment = PaymentFactory(user=user, expects_receipt_in_bot=True)

    _post(client, _photo_update(4101))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
    assert payment.telegram_file_id == "AgACphoto"
    assert not payment.receipt
