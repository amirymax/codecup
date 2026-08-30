"""Счётчики админ-панели и список пользователей."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.tests.factories import ContestFactory, DraftContestFactory, EndedContestFactory
from apps.submissions.models import SubmissionStatus
from apps.submissions.tests.factories import SubmissionFactory, SubmittedFactory

from .factories import AdminFactory, UserFactory

pytestmark = pytest.mark.django_db


# --- доступ ----------------------------------------------------------------


def test_anonymous_cannot_read_stats(client: APIClient) -> None:
    assert client.get(reverse("admin-stats")).status_code == 401


def test_participant_cannot_read_stats(client: APIClient, participant) -> None:
    assert client.get(reverse("admin-stats")).status_code == 403


def test_participant_cannot_list_users(client: APIClient, participant) -> None:
    assert client.get(reverse("admin-user-list")).status_code == 403


# --- плитки ----------------------------------------------------------------


def test_stats_match_the_four_tiles_on_the_dashboard(client: APIClient, admin) -> None:
    live = ContestFactory()
    EndedContestFactory()
    DraftContestFactory()

    UserFactory()
    SubmittedFactory(contest=live)
    SubmittedFactory(contest=live, status=SubmissionStatus.REVIEWED)
    SubmissionFactory(contest=live)  # черновик

    body = client.get(reverse("admin-stats")).json()

    assert body["active_contests"] == 1
    assert body["submissions"] == 2  # черновик не в счёт
    assert body["pending_review"] == 1  # только submitted
    assert body["total_users"] >= 2


def test_stats_are_zero_on_an_empty_installation(client: APIClient, admin) -> None:
    body = client.get(reverse("admin-stats")).json()

    assert body["active_contests"] == 0
    assert body["submissions"] == 0
    assert body["pending_review"] == 0


def test_inactive_users_are_not_counted(client: APIClient, admin) -> None:
    UserFactory(is_active=False)

    before = client.get(reverse("admin-stats")).json()["total_users"]
    UserFactory()

    assert client.get(reverse("admin-stats")).json()["total_users"] == before + 1


def test_an_ended_contest_is_not_active(client: APIClient, admin) -> None:
    EndedContestFactory()

    assert client.get(reverse("admin-stats")).json()["active_contests"] == 0


# --- пользователи ----------------------------------------------------------


def test_user_list_reports_submissions_and_wins(client: APIClient, admin) -> None:
    user = UserFactory(username="sarah_dev")
    SubmittedFactory(user=user, is_winner=True)
    SubmittedFactory(user=user)
    SubmissionFactory(user=user)  # черновик

    rows = client.get(reverse("admin-user-list"), {"search": "sarah"}).json()["results"]

    assert len(rows) == 1
    assert rows[0]["submissions_count"] == 2
    assert rows[0]["wins_count"] == 1


def test_user_list_can_be_searched_by_telegram_id(client: APIClient, admin) -> None:
    UserFactory(telegram_id=987654)

    rows = client.get(reverse("admin-user-list"), {"search": "987654"}).json()["results"]

    assert len(rows) == 1


def test_user_list_can_be_filtered_to_admins(client: APIClient, admin) -> None:
    UserFactory()
    AdminFactory()

    rows = client.get(reverse("admin-user-list"), {"is_staff": "true"}).json()["results"]

    assert all(row["is_staff"] for row in rows)
    assert len(rows) == 2  # включая того, кто смотрит


def test_user_list_does_not_double_count_with_both_annotations(client, admin) -> None:
    """Два Count в одном запросе без distinct дали бы перемноженные числа."""
    user = UserFactory()
    SubmittedFactory(user=user, is_winner=True)
    SubmittedFactory(user=user, is_winner=True)

    row = next(
        r
        for r in client.get(reverse("admin-user-list")).json()["results"]
        if r["username"] == user.username
    )

    assert row["submissions_count"] == 2
    assert row["wins_count"] == 2
