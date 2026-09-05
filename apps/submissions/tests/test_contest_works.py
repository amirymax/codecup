"""Работы участников контеста: закрыты до дедлайна, потом открыты всем."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.models import ContestStatus
from apps.contests.tests.factories import ContestFactory, EndedContestFactory

from .factories import SubmissionFactory, SubmittedFactory

pytestmark = pytest.mark.django_db


def _works(client: APIClient, contest) -> list[dict]:
    response = client.get(reverse("contest-works", args=[contest.slug]))
    assert response.status_code == 200
    return response.json()["results"]


def test_a_guest_sees_the_submitted_works(client: APIClient) -> None:
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest)
    SubmittedFactory(contest=contest)

    assert len(_works(client, contest)) == 2


def test_a_work_carries_the_links_people_come_to_see(client: APIClient) -> None:
    contest = EndedContestFactory()
    work = SubmittedFactory(contest=contest)

    row = _works(client, contest)[0]

    assert row["github_url"] == work.github_url
    assert row["live_url"] == work.live_url
    assert row["username"] == work.user.username
    assert row["display_name"] == work.user.display_name


def test_drafts_stay_out_of_the_list(client: APIClient) -> None:
    """Работа появляется, когда её отправили, а не когда начали писать."""
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest)
    SubmissionFactory(contest=contest)

    assert len(_works(client, contest)) == 1


def test_the_reviewer_notes_are_never_exposed(client: APIClient) -> None:
    """Балл — часть итогов, заметки проверяющего — нет."""
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest, score=7, reviewer_notes="Слабая архитектура")

    row = _works(client, contest)[0]

    assert "reviewer_notes" not in row


def test_the_score_includes_the_video_bonus(client: APIClient) -> None:
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest, score=70, video_url="https://youtu.be/demo")

    row = _works(client, contest)[0]

    assert row["total_score"] == 80
    assert row["video_bonus"] == 10


def test_an_unreviewed_work_has_no_score(client: APIClient) -> None:
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest)

    assert _works(client, contest)[0]["total_score"] is None


def test_winners_come_first(client: APIClient) -> None:
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest, score=90)
    winner = SubmittedFactory(contest=contest, is_winner=True, score=10)

    assert _works(client, contest)[0]["username"] == winner.user.username


def test_the_list_is_ordered_by_score(client: APIClient) -> None:
    contest = EndedContestFactory()
    weaker = SubmittedFactory(contest=contest, score=40)
    stronger = SubmittedFactory(contest=contest, score=70)

    order = [row["username"] for row in _works(client, contest)]

    assert order == [stronger.user.username, weaker.user.username]


def test_the_video_bonus_counts_towards_the_place(client: APIClient) -> None:
    """Те же 10 баллов, что и на экране проверки, иначе порядок разошёлся бы."""
    contest = EndedContestFactory()
    without_video = SubmittedFactory(contest=contest, score=45)
    with_video = SubmittedFactory(contest=contest, score=40, video_url="https://youtu.be/demo")

    order = [row["username"] for row in _works(client, contest)]

    assert order == [with_video.user.username, without_video.user.username]


def test_unreviewed_works_go_below_the_scored_ones(client: APIClient) -> None:
    contest = EndedContestFactory()
    unreviewed = SubmittedFactory(contest=contest)
    scored = SubmittedFactory(contest=contest, score=1)

    order = [row["username"] for row in _works(client, contest)]

    assert order == [scored.user.username, unreviewed.user.username]


def test_works_of_another_contest_are_not_mixed_in(client: APIClient) -> None:
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest)
    SubmittedFactory(contest=EndedContestFactory())

    assert len(_works(client, contest)) == 1


def test_an_unpublished_contest_has_no_public_works(client: APIClient) -> None:
    contest = EndedContestFactory(status=ContestStatus.DRAFT)
    SubmittedFactory(contest=contest)

    assert client.get(reverse("contest-works", args=[contest.slug])).status_code == 404


def test_while_the_contest_runs_the_works_stay_closed(client: APIClient) -> None:
    """Иначе работу можно списать у того, кто прислал раньше."""
    contest = ContestFactory()
    SubmittedFactory(contest=contest)

    response = client.get(reverse("contest-works", args=[contest.slug]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "works_hidden_until_deadline"
