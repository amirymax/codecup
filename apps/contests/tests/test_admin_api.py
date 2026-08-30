"""Админское API контестов: создание, правка, публикация, доступ."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.contests.models import Contest, ContestStatus

from .factories import ContestFactory, DraftContestFactory

pytestmark = pytest.mark.django_db


def _payload(**overrides) -> dict:
    return {
        "title": "Создайте инструмент на базе ИИ",
        "description": "Соберите рабочий инструмент для разработчиков.",
        "requirements": ["Публичный репозиторий GitHub", "Живая демо-ссылка"],
        "prize_pool": "5000.00",
        "deadline": (timezone.now() + timedelta(days=7)).isoformat(),
        "status": ContestStatus.DRAFT,
    } | overrides


# --- доступ ----------------------------------------------------------------


def test_anonymous_cannot_list_contests(client: APIClient) -> None:
    assert client.get(reverse("admin-contest-list")).status_code == 401


def test_participant_cannot_create_a_contest(client: APIClient, participant) -> None:
    response = client.post(reverse("admin-contest-list"), _payload(), format="json")

    assert response.status_code == 403
    assert not Contest.objects.exists()


def test_participant_cannot_publish(client: APIClient, participant) -> None:
    contest = DraftContestFactory()

    url = reverse("admin-contest-publish", args=[contest.pk])

    assert client.post(url).status_code == 403


# --- создание --------------------------------------------------------------


def test_admin_creates_a_contest_as_a_draft(client: APIClient, admin) -> None:
    response = client.post(reverse("admin-contest-list"), _payload(), format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["state"] == "draft"
    assert body["display_number"] == "#01"
    assert body["slug"] == "sozdayte-instrument-na-baze-ii"
    assert Contest.objects.get().created_by == admin


def test_admin_sees_drafts_in_the_admin_list(client: APIClient, admin) -> None:
    DraftContestFactory()

    assert client.get(reverse("admin-contest-list")).json()["count"] == 1


def test_requirements_are_trimmed(client: APIClient, admin) -> None:
    payload = _payload(requirements=["  Репозиторий GitHub  ", "Демо-ссылка"])

    response = client.post(reverse("admin-contest-list"), payload, format="json")

    assert response.json()["requirements"] == ["Репозиторий GitHub", "Демо-ссылка"]


@pytest.mark.parametrize("bad", [["  "], [42], "не список"])
def test_invalid_requirements_are_rejected(client: APIClient, admin, bad) -> None:
    response = client.post(reverse("admin-contest-list"), _payload(requirements=bad), format="json")

    assert response.status_code == 400
    assert "requirements" in response.json()["error"]["details"]


def test_a_draft_may_have_a_deadline_in_the_past(client: APIClient, admin) -> None:
    """Черновик готовят заранее — дату можно выставить позже."""
    payload = _payload(deadline=(timezone.now() - timedelta(days=1)).isoformat())

    assert client.post(reverse("admin-contest-list"), payload, format="json").status_code == 201


def test_publishing_with_a_past_deadline_is_rejected(client: APIClient, admin) -> None:
    payload = _payload(
        status=ContestStatus.PUBLISHED,
        deadline=(timezone.now() - timedelta(days=1)).isoformat(),
    )

    response = client.post(reverse("admin-contest-list"), payload, format="json")

    assert response.status_code == 400
    assert "deadline" in response.json()["error"]["details"]


def test_start_must_come_before_the_deadline(client: APIClient, admin) -> None:
    payload = _payload(
        starts_at=(timezone.now() + timedelta(days=30)).isoformat(),
        deadline=(timezone.now() + timedelta(days=7)).isoformat(),
    )

    response = client.post(reverse("admin-contest-list"), payload, format="json")

    assert response.status_code == 400
    assert "starts_at" in response.json()["error"]["details"]


# --- правка и публикация ---------------------------------------------------


def test_admin_edits_a_contest(client: APIClient, admin) -> None:
    contest = DraftContestFactory()

    response = client.patch(
        reverse("admin-contest-detail", args=[contest.pk]),
        {"title": "Новое название"},
        format="json",
    )

    assert response.status_code == 200
    contest.refresh_from_db()
    assert contest.title == "Новое название"


def test_publish_makes_a_draft_public(client: APIClient, admin) -> None:
    contest = DraftContestFactory()

    response = client.post(reverse("admin-contest-publish", args=[contest.pk]))

    assert response.status_code == 200
    assert response.json()["state"] == "live"
    assert client.get(reverse("contest-detail", args=[contest.slug])).status_code == 200


def test_admin_deletes_a_contest(client: APIClient, admin) -> None:
    contest = ContestFactory()

    assert client.delete(reverse("admin-contest-detail", args=[contest.pk])).status_code == 204
    assert not Contest.objects.exists()


def test_publishing_a_missing_contest_returns_not_found(client: APIClient, admin) -> None:
    response = client.post(reverse("admin-contest-publish", args=[9999]))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
