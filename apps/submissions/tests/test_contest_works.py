"""Работы участников контеста открыты всем."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.models import ContestStatus
from apps.contests.tests.factories import ContestFactory

from .factories import SubmissionFactory, SubmittedFactory

pytestmark = pytest.mark.django_db


def _works(client: APIClient, contest) -> list[dict]:
    response = client.get(reverse("contest-works", args=[contest.slug]))
    assert response.status_code == 200
    return response.json()["results"]


def test_a_guest_sees_the_submitted_works(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    SubmittedFactory(contest=contest)

    assert len(_works(client, contest)) == 2


def test_a_work_carries_the_links_people_come_to_see(client: APIClient) -> None:
    contest = ContestFactory()
    work = SubmittedFactory(contest=contest)

    row = _works(client, contest)[0]

    assert row["github_url"] == work.github_url
    assert row["live_url"] == work.live_url
    assert row["username"] == work.user.username
    assert row["display_name"] == work.user.display_name


def test_drafts_stay_out_of_the_list(client: APIClient) -> None:
    """Работа появляется, когда её отправили, а не когда начали писать."""
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    SubmissionFactory(contest=contest)

    assert len(_works(client, contest)) == 1


def test_the_score_and_reviewer_notes_are_never_exposed(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest, score=7, reviewer_notes="Слабая архитектура")

    row = _works(client, contest)[0]

    assert "score" not in row
    assert "reviewer_notes" not in row


def test_winners_come_first(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    winner = SubmittedFactory(contest=contest, is_winner=True)

    assert _works(client, contest)[0]["username"] == winner.user.username


def test_works_of_another_contest_are_not_mixed_in(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    SubmittedFactory(contest=ContestFactory())

    assert len(_works(client, contest)) == 1


def test_an_unpublished_contest_has_no_public_works(client: APIClient) -> None:
    contest = ContestFactory(status=ContestStatus.DRAFT)
    SubmittedFactory(contest=contest)

    assert client.get(reverse("contest-works", args=[contest.slug])).status_code == 404
