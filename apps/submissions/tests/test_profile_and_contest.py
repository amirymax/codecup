"""Профиль участника и данные заявки на странице контеста."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.models import Contest
from apps.contests.tests.factories import ContestFactory
from apps.submissions.models import SubmissionStatus
from apps.users.tests.factories import UserFactory

from .factories import SubmissionFactory, SubmittedFactory

pytestmark = pytest.mark.django_db


# --- счётчик участников ----------------------------------------------------


def test_participants_count_ignores_drafts(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    SubmittedFactory(contest=contest)
    SubmissionFactory(contest=contest)  # черновик

    body = client.get(reverse("contest-detail", args=[contest.slug])).json()

    assert body["participants_count"] == 2


def test_participants_count_appears_in_the_list(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)

    body = client.get(reverse("contest-list")).json()["results"][0]

    assert body["participants_count"] == 1


def test_participants_count_appears_on_the_landing(client: APIClient) -> None:
    contest = ContestFactory(is_featured=True)
    SubmittedFactory(contest=contest)

    body = client.get(reverse("contest-featured")).json()["contest"]

    assert body["participants_count"] == 1


def test_contest_list_does_not_run_a_query_per_contest(
    client: APIClient, django_capture_on_commit_callbacks
) -> None:
    """Счётчик приходит аннотацией, иначе список делал бы N+1 запросов.

    Проверяем не абсолютное число запросов, а то, что оно не растёт вместе с
    числом контестов, — именно это и означает отсутствие N+1.
    """
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def queries_for(contest_count: int) -> int:
        Contest.objects.all().delete()
        for _ in range(contest_count):
            SubmittedFactory(contest=ContestFactory())
        with CaptureQueriesContext(connection) as captured:
            client.get(reverse("contest-list"))
        return len(captured)

    assert queries_for(2) == queries_for(10)


# --- заявка на странице контеста -------------------------------------------


def test_contest_page_shows_my_submission_when_signed_in(client, participant) -> None:
    """Кнопка меняется на «Редактировать заявку», когда решение отправлено."""
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=participant)

    body = client.get(reverse("contest-detail", args=[contest.slug])).json()

    assert body["my_submission"]["display_status"] == "submitted"


def test_contest_page_has_no_submission_for_a_guest(client: APIClient) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=UserFactory())

    body = client.get(reverse("contest-detail", args=[contest.slug])).json()

    assert body["my_submission"] is None


def test_contest_page_does_not_show_someone_elses_submission(client, participant) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=UserFactory())

    body = client.get(reverse("contest-detail", args=[contest.slug])).json()

    assert body["my_submission"] is None


# --- профиль ---------------------------------------------------------------


def test_public_profile_reports_submissions_and_wins(client: APIClient) -> None:
    user = UserFactory(username="sarah_dev")
    SubmittedFactory(user=user, is_winner=True)
    SubmittedFactory(user=user)
    SubmissionFactory(user=user)  # черновик не считается

    body = client.get(reverse("public-profile", args=["sarah_dev"])).json()

    assert body["user"]["username"] == "sarah_dev"
    assert body["submissions_count"] == 2
    assert body["wins_count"] == 1
    assert len(body["submissions"]) == 2


def test_public_profile_shows_the_repository_without_the_scheme(client: APIClient) -> None:
    user = UserFactory(username="sarah_dev")
    SubmittedFactory(user=user, github_url="https://github.com/sarahdev/ai-lint-agent")

    body = client.get(reverse("public-profile", args=["sarah_dev"])).json()

    assert body["submissions"][0]["repo_name"] == "github.com/sarahdev/ai-lint-agent"


def test_missing_profile_returns_not_found(client: APIClient) -> None:
    response = client.get(reverse("public-profile", args=["нет-такого"]))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_my_submission_list_includes_drafts(client: APIClient, participant) -> None:
    """В своём профиле черновик виден — его нужно дописать."""
    SubmissionFactory(user=participant)
    SubmittedFactory(user=participant)

    body = client.get(reverse("my-submission-list")).json()

    assert body["count"] == 2
    assert {item["display_status"] for item in body["results"]} == {"draft", "submitted"}


def test_my_submission_list_shows_only_my_own(client: APIClient, participant) -> None:
    SubmittedFactory(user=participant)
    SubmittedFactory(user=UserFactory())

    assert client.get(reverse("my-submission-list")).json()["count"] == 1


def test_my_submission_list_requires_login(client: APIClient) -> None:
    assert client.get(reverse("my-submission-list")).status_code == 401


def test_winner_badge_is_visible_on_the_profile(client: APIClient, participant) -> None:
    SubmittedFactory(user=participant, is_winner=True, status=SubmissionStatus.REVIEWED)

    body = client.get(reverse("my-submission-list")).json()

    assert body["results"][0]["display_status"] == "winner"
