"""Один чек за раз: пока присланный ждёт проверки, второй не принимаем."""

from __future__ import annotations

import pytest
from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payments.models import EntryPayment, PaymentStatus
from apps.telegrambot import messages

from .factories import PaidContestFactory

pytestmark = pytest.mark.django_db

PNG = b"\x89PNG\r\n\x1a\n" + b"cheque" * 8


def _upload(client: APIClient, slug: str, name: str = "cheque.png"):
    return client.post(
        reverse("upload-receipt", args=[slug]),
        {"receipt": ContentFile(PNG, name=name)},
        format="multipart",
    )


def _photo_update(telegram_id: int) -> dict:
    return {
        "update_id": 7,
        "message": {
            "message_id": 30,
            "date": 1_700_000_000,
            "chat": {"id": telegram_id, "type": "private"},
            "from": {"id": telegram_id, "is_bot": False, "first_name": "Тест"},
            "photo": [{"file_id": "AgACsecond", "width": 800, "height": 800}],
        },
    }


def _webhook(client: APIClient, update: dict):
    return client.post(
        reverse("telegram-webhook", args=[django_settings.TELEGRAM_WEBHOOK_SECRET]),
        update,
        format="json",
        HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=django_settings.TELEGRAM_WEBHOOK_SECRET,
    )


# --- сайт -------------------------------------------------------------------


def test_second_upload_from_the_site_is_refused_while_the_first_is_checked(
    client: APIClient, participant
) -> None:
    contest = PaidContestFactory()
    assert _upload(client, contest.slug).status_code == 200

    response = _upload(client, contest.slug, "another.png")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payment_under_review"


def test_switching_to_the_bot_is_refused_while_a_receipt_is_checked(
    client: APIClient, participant
) -> None:
    """Иначе ожидание чека в боте сбросило бы уже присланный на проверку."""
    contest = PaidContestFactory()
    _upload(client, contest.slug)

    response = client.post(reverse("receipt-via-bot", args=[contest.slug]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payment_under_review"
    assert EntryPayment.objects.get().status == PaymentStatus.PENDING


def test_a_new_receipt_is_accepted_after_a_rejection(
    client: APIClient, participant, admin_user
) -> None:
    """Запрет держится только на время проверки, а не навсегда."""
    contest = PaidContestFactory()
    _upload(client, contest.slug)
    EntryPayment.objects.get().reject(admin_user, "Не видно суммы")

    assert _upload(client, contest.slug, "fixed.png").status_code == 200


# --- бот --------------------------------------------------------------------


def test_the_bot_explains_that_the_receipt_is_already_being_checked(
    client: APIClient, participant, no_telegram_calls
) -> None:
    contest = PaidContestFactory()
    _upload(client, contest.slug)
    no_telegram_calls.clear()

    _webhook(client, _photo_update(participant.telegram_id))

    texts = [payload.get("text", "") for _, payload in no_telegram_calls]
    assert messages.RECEIPT_ALREADY_PENDING in texts
    assert EntryPayment.objects.get().telegram_file_id == ""


def test_a_receipt_in_the_bot_blocks_a_later_upload_on_the_site(
    client: APIClient, participant
) -> None:
    """Обратный случай: сначала бот, потом сайт."""
    contest = PaidContestFactory()
    client.post(reverse("receipt-via-bot", args=[contest.slug]))
    _webhook(client, _photo_update(participant.telegram_id))
    assert EntryPayment.objects.get().status == PaymentStatus.PENDING

    response = _upload(client, contest.slug)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payment_under_review"
