"""Реквизиты для оплаты, которые администратор правит с сайта."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payments.models import PaymentSettings

from .factories import PaidContestFactory

pytestmark = pytest.mark.django_db

CARD = "Карта: 1111 2222 3333 4444\nПолучатель: CodeCup"


def test_admin_sees_the_fallback_text_until_something_is_saved(
    client: APIClient, admin, settings
) -> None:
    """Пустая база — не пустое поле: админ правит то, что видит участник."""
    settings.PAYMENT_REQUISITES = "Реквизиты пока не заданы."

    body = client.get(reverse("admin-payment-requisites")).json()

    assert body["requisites"] == "Реквизиты пока не заданы."


def test_admin_changes_requisites_and_participants_see_them(client: APIClient, admin) -> None:
    contest = PaidContestFactory()

    response = client.put(reverse("admin-payment-requisites"), {"requisites": CARD}, format="json")

    assert response.status_code == 200
    assert response.json()["requisites"] == CARD

    shown = client.get(reverse("participation", args=[contest.slug])).json()
    assert shown["requisites"] == CARD


def test_saving_twice_keeps_a_single_row(client: APIClient, admin) -> None:
    """Второй набор реквизитов означал бы, что часть участников платит не туда."""
    client.put(reverse("admin-payment-requisites"), {"requisites": CARD}, format="json")
    client.put(reverse("admin-payment-requisites"), {"requisites": "Другие"}, format="json")

    assert PaymentSettings.objects.count() == 1
    assert PaymentSettings.load().requisites == "Другие"


def test_participant_cannot_read_or_change_requisites(client: APIClient, participant) -> None:
    assert client.get(reverse("admin-payment-requisites")).status_code == 403
    assert (
        client.put(
            reverse("admin-payment-requisites"), {"requisites": CARD}, format="json"
        ).status_code
        == 403
    )


def test_guest_cannot_read_requisites(client: APIClient) -> None:
    assert client.get(reverse("admin-payment-requisites")).status_code == 401


def test_blank_requisites_fall_back_to_the_default_text(client: APIClient, admin, settings) -> None:
    settings.PAYMENT_REQUISITES = "Напишите администратору."
    contest = PaidContestFactory()
    client.put(reverse("admin-payment-requisites"), {"requisites": ""}, format="json")

    shown = client.get(reverse("participation", args=[contest.slug])).json()

    assert shown["requisites"] == "Напишите администратору."
