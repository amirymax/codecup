"""Чек об оплате виден только администратору."""

from __future__ import annotations

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APIClient

from .factories import PaymentFactory

pytestmark = pytest.mark.django_db

PNG = b"\x89PNG\r\n\x1a\n" + b"cheque" * 8


def _payment_with_receipt():
    payment = PaymentFactory()
    payment.receipt.save("cheque.png", ContentFile(PNG), save=True)
    return payment


def test_an_admin_can_open_the_receipt(client: APIClient, admin) -> None:
    payment = _payment_with_receipt()

    response = client.get(reverse("admin-payment-receipt", args=[payment.id]))

    assert response.status_code == 200
    assert b"".join(response.streaming_content) == PNG
    assert response["Content-Type"] == "image/png"


def test_a_participant_cannot_open_someone_elses_receipt(client: APIClient, participant) -> None:
    payment = _payment_with_receipt()

    assert client.get(reverse("admin-payment-receipt", args=[payment.id])).status_code == 403


def test_a_guest_cannot_open_a_receipt(client: APIClient) -> None:
    payment = _payment_with_receipt()

    assert client.get(reverse("admin-payment-receipt", args=[payment.id])).status_code == 401


def test_a_payment_without_a_receipt_is_not_found(client: APIClient, admin) -> None:
    payment = PaymentFactory()

    assert client.get(reverse("admin-payment-receipt", args=[payment.id])).status_code == 404


def test_in_production_the_file_is_handed_to_nginx(client: APIClient, admin, settings) -> None:
    """Django проверяет права, байты отдаёт nginx по внутреннему редиректу."""
    settings.USE_X_ACCEL_REDIRECT = True
    payment = _payment_with_receipt()

    response = client.get(reverse("admin-payment-receipt", args=[payment.id]))

    assert response.status_code == 200
    assert response["X-Accel-Redirect"].startswith("/protected-media/receipts/")
    assert response.content == b"", "тело подставляет nginx"


def test_the_admin_list_links_to_the_protected_endpoint(client: APIClient, admin) -> None:
    """Прямая ссылка на media открыла бы чек кому угодно."""
    payment = _payment_with_receipt()

    body = client.get(reverse("admin-payment-list")).json()

    url = body["results"][0]["receipt_url"]
    assert url.endswith(f"/api/admin/payments/{payment.id}/receipt/")
    assert "/media/" not in url
