"""Публичное API контестов."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.contests.models import ContestStatus, NotifySubscription

from .factories import ContestFactory, DraftContestFactory, EndedContestFactory

pytestmark = pytest.mark.django_db


def _titles(response) -> list[str]:
    return [item["title"] for item in response.json()["results"]]


# --- список ----------------------------------------------------------------


def test_list_returns_only_published_contests(client: APIClient) -> None:
    live = ContestFactory()
    ended = EndedContestFactory()
    DraftContestFactory()
    ContestFactory(status=ContestStatus.ARCHIVED)

    response = client.get(reverse("contest-list"))

    assert response.status_code == 200
    assert set(_titles(response)) == {live.title, ended.title}


def test_list_can_be_filtered_to_live(client: APIClient) -> None:
    live = ContestFactory()
    EndedContestFactory()

    response = client.get(reverse("contest-list"), {"state": "live"})

    assert _titles(response) == [live.title]


def test_list_can_be_filtered_to_ended(client: APIClient) -> None:
    ContestFactory()
    ended = EndedContestFactory()

    response = client.get(reverse("contest-list"), {"state": "ended"})

    assert _titles(response) == [ended.title]


def test_unknown_state_filter_falls_back_to_all_published(client: APIClient) -> None:
    ContestFactory()
    EndedContestFactory()

    assert len(_titles(client.get(reverse("contest-list"), {"state": "чепуха"}))) == 2


def test_featured_contest_comes_first_in_the_list(client: APIClient) -> None:
    ContestFactory(title="Обычный")
    featured = ContestFactory(title="Главный", is_featured=True)

    assert _titles(client.get(reverse("contest-list")))[0] == featured.title


# --- контест на главной ----------------------------------------------------


def test_featured_returns_the_flagged_live_contest(client: APIClient) -> None:
    ContestFactory(title="Обычный")
    featured = ContestFactory(title="Главный", is_featured=True)

    response = client.get(reverse("contest-featured"))

    assert response.json()["contest"]["title"] == featured.title


def test_featured_falls_back_to_the_soonest_deadline(client: APIClient) -> None:
    ContestFactory(title="Позже", deadline=timezone.now() + timedelta(days=10))
    soonest = ContestFactory(title="Раньше", deadline=timezone.now() + timedelta(days=2))

    assert client.get(reverse("contest-featured")).json()["contest"]["title"] == soonest.title


def test_featured_is_null_when_nothing_is_running(client: APIClient) -> None:
    """Это состояние «Сейчас нет активного контеста» на главной."""
    EndedContestFactory()
    DraftContestFactory()

    response = client.get(reverse("contest-featured"))

    assert response.status_code == 200
    assert response.json() == {"contest": None}


def test_featured_ignores_an_ended_flagged_contest(client: APIClient) -> None:
    EndedContestFactory(is_featured=True)

    assert client.get(reverse("contest-featured")).json()["contest"] is None


# --- страница контеста -----------------------------------------------------


def test_detail_returns_the_full_contest(client: APIClient) -> None:
    contest = ContestFactory(requirements=["Репозиторий GitHub", "Демо-ссылка"])

    response = client.get(reverse("contest-detail", args=[contest.slug]))

    body = response.json()
    assert body["title"] == contest.title
    assert body["requirements"] == ["Репозиторий GitHub", "Демо-ссылка"]
    assert body["state"] == "live"
    assert body["display_number"] == "#01"
    assert body["accepts_submissions"] is True


def test_seconds_left_counts_down_to_the_deadline(client: APIClient) -> None:
    contest = ContestFactory(deadline=timezone.now() + timedelta(hours=1))

    seconds_left = client.get(reverse("contest-detail", args=[contest.slug])).json()["seconds_left"]

    assert 3540 <= seconds_left <= 3600


def test_seconds_left_never_goes_negative(client: APIClient) -> None:
    contest = EndedContestFactory()

    assert client.get(reverse("contest-detail", args=[contest.slug])).json()["seconds_left"] == 0


def test_draft_is_not_reachable_by_direct_link(client: APIClient) -> None:
    contest = DraftContestFactory()

    response = client.get(reverse("contest-detail", args=[contest.slug]))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_missing_contest_returns_the_error_envelope(client: APIClient) -> None:
    response = client.get("/api/contests/net-takogo/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


# --- «уведомить меня» ------------------------------------------------------


def test_participant_can_subscribe_to_announcements(client: APIClient, participant) -> None:
    response = client.post(reverse("notify-subscribe"))

    assert response.status_code == 204
    assert NotifySubscription.objects.filter(user=participant).exists()


def test_subscribing_twice_is_harmless(client: APIClient, participant) -> None:
    client.post(reverse("notify-subscribe"))
    client.post(reverse("notify-subscribe"))

    assert NotifySubscription.objects.count() == 1


def test_participant_can_unsubscribe(client: APIClient, participant) -> None:
    client.post(reverse("notify-subscribe"))

    assert client.delete(reverse("notify-subscribe")).status_code == 204
    assert not NotifySubscription.objects.exists()


def test_subscribing_requires_login(client: APIClient) -> None:
    assert client.post(reverse("notify-subscribe")).status_code == 401
