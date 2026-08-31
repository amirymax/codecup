"""Оплата участия: состояние, чеки и допуск к отправке решения."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.tests.factories import ContestFactory
from apps.payments.models import EntryPayment, PaymentStatus
from apps.submissions.models import Submission

from .factories import PaidContestFactory, PaymentFactory

pytestmark = pytest.mark.django_db

SUBMISSION = {
    "github_url": "https://github.com/dev/project",
    "live_url": "https://project.vercel.app",
    "description": (
        "Инструмент для разработчиков с использованием ИИ, который помогает "
        "быстрее находить ошибки в коде и предлагает готовые исправления."
    ),
}


def _receipt(name="cheque.png", content_type="image/png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n" + b"0" * 64, content_type=content_type)


# --- состояние участия -----------------------------------------------------


def test_free_contest_needs_no_payment(client: APIClient) -> None:
    contest = ContestFactory()

    body = client.get(reverse("participation", args=[contest.slug])).json()

    assert body["is_paid"] is False
    assert body["can_submit"] is True
    assert body["requisites"] == ""


def test_paid_contest_shows_fee_and_requisites(client: APIClient, settings) -> None:
    settings.PAYMENT_REQUISITES = "Карта 0000 1111 2222 3333"
    contest = PaidContestFactory()

    body = client.get(reverse("participation", args=[contest.slug])).json()

    assert body["is_paid"] is True
    assert Decimal(body["entry_fee"]) == Decimal("150.00")
    assert body["currency"] == "TJS"
    assert body["requisites"] == "Карта 0000 1111 2222 3333"
    assert body["can_submit"] is False


# --- допуск к отправке решения ---------------------------------------------


def test_paid_contest_refuses_a_submission_without_payment(client, participant) -> None:
    contest = PaidContestFactory()

    response = client.post(
        reverse("submit-solution", args=[contest.slug]), SUBMISSION, format="json"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "entry_fee_required"
    assert not Submission.objects.exists()


def test_a_pending_receipt_is_not_enough(client: APIClient, participant) -> None:
    contest = PaidContestFactory()
    PaymentFactory(contest=contest, user=participant, status=PaymentStatus.PENDING)

    response = client.post(
        reverse("submit-solution", args=[contest.slug]), SUBMISSION, format="json"
    )

    assert response.status_code == 409


def test_accepted_payment_opens_submissions(client: APIClient, participant) -> None:
    contest = PaidContestFactory()
    PaymentFactory(contest=contest, user=participant, status=PaymentStatus.ACCEPTED)

    response = client.post(
        reverse("submit-solution", args=[contest.slug]), SUBMISSION, format="json"
    )

    assert response.status_code == 200


def test_a_rejected_payment_still_blocks(client: APIClient, participant) -> None:
    contest = PaidContestFactory()
    PaymentFactory(contest=contest, user=participant, status=PaymentStatus.REJECTED)

    assert (
        client.post(
            reverse("submit-solution", args=[contest.slug]), SUBMISSION, format="json"
        ).status_code
        == 409
    )


def test_free_contest_is_unaffected(client: APIClient, participant) -> None:
    contest = ContestFactory()

    response = client.post(
        reverse("submit-solution", args=[contest.slug]), SUBMISSION, format="json"
    )

    assert response.status_code == 200


# --- чек с сайта -----------------------------------------------------------


def test_uploading_a_receipt_queues_it_for_review(client, participant, no_telegram_calls) -> None:
    contest = PaidContestFactory()

    response = client.post(
        reverse("upload-receipt", args=[contest.slug]),
        {"receipt": _receipt()},
        format="multipart",
    )

    assert response.status_code == 200
    payment = EntryPayment.objects.get()
    assert payment.status == PaymentStatus.PENDING
    assert payment.receipt


def test_the_amount_is_fixed_when_the_receipt_is_sent(client, participant, no_telegram_calls):
    """Если админ потом поменяет взнос, уже отправленный чек не подорожает."""
    contest = PaidContestFactory(entry_fee=Decimal("150.00"))

    client.post(
        reverse("upload-receipt", args=[contest.slug]), {"receipt": _receipt()}, format="multipart"
    )
    contest.entry_fee = Decimal("900.00")
    contest.save(update_fields=["entry_fee"])

    assert EntryPayment.objects.get().amount == Decimal("150.00")


@pytest.mark.parametrize(
    ("name", "content_type"),
    [("virus.exe", "application/x-msdownload"), ("notes.txt", "text/plain")],
)
def test_only_images_and_pdf_are_accepted(client, participant, name, content_type) -> None:
    contest = PaidContestFactory()

    response = client.post(
        reverse("upload-receipt", args=[contest.slug]),
        {"receipt": _receipt(name, content_type)},
        format="multipart",
    )

    assert response.status_code == 400


def test_an_oversized_receipt_is_refused(client, participant, settings) -> None:
    settings.RECEIPT_MAX_BYTES = 10
    contest = PaidContestFactory()

    response = client.post(
        reverse("upload-receipt", args=[contest.slug]),
        {"receipt": _receipt()},
        format="multipart",
    )

    assert response.status_code == 400


def test_a_free_contest_takes_no_receipts(client: APIClient, participant) -> None:
    contest = ContestFactory()

    response = client.post(
        reverse("upload-receipt", args=[contest.slug]),
        {"receipt": _receipt()},
        format="multipart",
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "contest_is_free"


def test_uploading_requires_login(client: APIClient) -> None:
    contest = PaidContestFactory()

    response = client.post(
        reverse("upload-receipt", args=[contest.slug]),
        {"receipt": _receipt()},
        format="multipart",
    )

    assert response.status_code == 401


# --- чек через бота --------------------------------------------------------


def test_choosing_the_bot_route_marks_the_payment_as_waiting(client, participant) -> None:
    contest = PaidContestFactory()

    response = client.post(reverse("receipt-via-bot", args=[contest.slug]))

    assert response.status_code == 200
    payment = EntryPayment.objects.get()
    assert payment.expects_receipt_in_bot
    assert payment.status == PaymentStatus.AWAITING_RECEIPT
    assert "t.me" in response.json()["bot_url"]


def test_an_accepted_payment_cannot_be_paid_again(client, participant) -> None:
    contest = PaidContestFactory()
    PaymentFactory(contest=contest, user=participant, status=PaymentStatus.ACCEPTED)

    response = client.post(reverse("receipt-via-bot", args=[contest.slug]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payment_already_accepted"
