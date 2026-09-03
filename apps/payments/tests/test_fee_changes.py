"""Взнос поменяли — заявка и чек в Telegram должны показывать новую цену."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payments.models import EntryPayment, PaymentStatus
from apps.users.tests.factories import AdminFactory

from .factories import PaidContestFactory, PaymentFactory

pytestmark = pytest.mark.django_db

PNG = b"\x89PNG\r\n\x1a\n" + b"cheque" * 8
NEW_FEE = Decimal("250.00")


def _upload(client: APIClient, slug: str):
    return client.post(
        reverse("upload-receipt", args=[slug]),
        {"receipt": ContentFile(PNG, name="cheque.png")},
        format="multipart",
    )


def test_a_receipt_sent_after_a_price_change_carries_the_new_amount(
    client: APIClient, participant
) -> None:
    """Заявка появилась по старой цене, чек прислан уже по новой."""
    contest = PaidContestFactory()
    client.post(reverse("receipt-via-bot", args=[contest.slug]))

    contest.entry_fee = NEW_FEE
    contest.save(update_fields=["entry_fee"])
    _upload(client, contest.slug)

    assert EntryPayment.objects.get().amount == NEW_FEE


def test_the_admin_sees_the_new_amount_in_telegram(
    client: APIClient, participant, settings, no_telegram_calls
) -> None:
    admin = AdminFactory(telegram_username="fee_admin")
    settings.TELEGRAM_ADMIN_USERNAME = "fee_admin"
    contest = PaidContestFactory()
    client.post(reverse("receipt-via-bot", args=[contest.slug]))

    contest.entry_fee = NEW_FEE
    contest.save(update_fields=["entry_fee"])
    _upload(client, contest.slug)

    _, sent = no_telegram_calls[-1]
    assert sent["chat_id"] == admin.telegram_id
    assert "250.00" in sent["caption"]


def test_opening_participation_refreshes_a_stale_amount(client: APIClient, participant) -> None:
    contest = PaidContestFactory()
    client.post(reverse("receipt-via-bot", args=[contest.slug]))
    contest.entry_fee = NEW_FEE
    contest.save(update_fields=["entry_fee"])

    client.post(reverse("receipt-via-bot", args=[contest.slug]))

    assert EntryPayment.objects.get().amount == NEW_FEE


def test_an_accepted_payment_keeps_the_amount_that_was_paid(admin_user) -> None:
    """Принятый взнос — история, и она не переписывается задним числом."""
    payment = PaymentFactory(status=PaymentStatus.PENDING)
    payment.accept(admin_user)
    paid = payment.amount

    payment.contest.entry_fee = NEW_FEE
    payment.contest.save(update_fields=["entry_fee"])
    payment.sync_amount_with_contest()

    payment.refresh_from_db()
    assert payment.amount == paid


def test_a_currency_change_travels_with_the_fee(client: APIClient, participant) -> None:
    contest = PaidContestFactory()
    client.post(reverse("receipt-via-bot", args=[contest.slug]))

    contest.entry_fee = NEW_FEE
    contest.currency = "USD"
    contest.save(update_fields=["entry_fee", "currency"])
    _upload(client, contest.slug)

    payment = EntryPayment.objects.get()
    assert (payment.amount, payment.currency) == (NEW_FEE, "USD")
