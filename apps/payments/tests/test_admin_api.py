"""Очередь взносов в админ-панели."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payments.models import PaymentStatus

from .factories import PaymentFactory

pytestmark = pytest.mark.django_db


def _decide(client: APIClient, payment, **body):
    return client.post(reverse("admin-payment-decision", args=[payment.id]), body, format="json")


def test_participant_cannot_see_the_queue(client: APIClient, participant) -> None:
    assert client.get(reverse("admin-payment-list")).status_code == 403


def test_anonymous_cannot_see_the_queue(client: APIClient) -> None:
    assert client.get(reverse("admin-payment-list")).status_code == 401


def test_queue_can_be_filtered_by_status(client: APIClient, admin) -> None:
    PaymentFactory(status=PaymentStatus.PENDING)
    PaymentFactory(status=PaymentStatus.ACCEPTED)

    response = client.get(reverse("admin-payment-list"), {"status": "pending"})

    assert response.json()["count"] == 1


def test_admin_accepts_a_payment(client: APIClient, admin, no_telegram_calls) -> None:
    payment = PaymentFactory(status=PaymentStatus.PENDING)

    response = _decide(client, payment, decision="accept")

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.ACCEPTED
    assert payment.reviewed_by == admin


def test_admin_rejects_with_a_reason(client: APIClient, admin, no_telegram_calls) -> None:
    payment = PaymentFactory(status=PaymentStatus.PENDING)

    response = _decide(client, payment, decision="reject", reason="Сумма не совпадает.")

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.REJECTED
    assert payment.rejection_reason == "Сумма не совпадает."


def test_rejection_requires_a_reason(client: APIClient, admin, no_telegram_calls) -> None:
    """Участник должен понимать, что исправить в новом чеке."""
    payment = PaymentFactory(status=PaymentStatus.PENDING)

    response = _decide(client, payment, decision="reject")

    assert response.status_code == 400
    assert "reason" in response.json()["error"]["details"]


def test_participant_cannot_decide(client: APIClient, participant, no_telegram_calls) -> None:
    payment = PaymentFactory(status=PaymentStatus.PENDING)

    assert _decide(client, payment, decision="accept").status_code == 403


def test_a_rejected_payment_can_be_accepted_later(client, admin, no_telegram_calls) -> None:
    """Участник присылает новый чек в ту же запись — решение можно поменять."""
    payment = PaymentFactory(status=PaymentStatus.REJECTED, rejection_reason="Не тот файл")

    _decide(client, payment, decision="accept")

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.ACCEPTED
    assert payment.rejection_reason == ""
