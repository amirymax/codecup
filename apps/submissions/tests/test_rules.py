"""Правила, которые обязаны держаться на сервере.

Проверки в макетах живут на клиенте и на них нельзя полагаться: запрос можно
отправить в обход интерфейса.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.tests.factories import (
    ContestFactory,
    DraftContestFactory,
    EndedContestFactory,
)
from apps.submissions.models import Submission, SubmissionStatus
from apps.users.tests.factories import UserFactory

from .factories import SubmissionFactory, SubmittedFactory

pytestmark = pytest.mark.django_db

VALID = {
    "github_url": "https://github.com/sarahdev/ai-lint-agent",
    "live_url": "https://ai-lint-agent.vercel.app",
    "video_url": "https://youtube.com/watch?v=abc",
    "description": "GitHub Action с проверкой кода через LLM.",
}


def _draft_url(contest) -> str:
    return reverse("my-submission", args=[contest.slug])


def _submit_url(contest) -> str:
    return reverse("submit-solution", args=[contest.slug])


# --- дедлайн ---------------------------------------------------------------


def test_cannot_submit_after_the_deadline(client: APIClient, participant) -> None:
    contest = EndedContestFactory()

    response = client.post(_submit_url(contest), VALID, format="json")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "contest_closed"
    assert not Submission.objects.exists()


def test_cannot_save_a_draft_after_the_deadline(client: APIClient, participant) -> None:
    contest = EndedContestFactory()

    assert client.put(_draft_url(contest), VALID, format="json").status_code == 409


def test_cannot_edit_an_existing_submission_after_the_deadline(client, participant) -> None:
    contest = EndedContestFactory()
    SubmittedFactory(contest=contest, user=participant)

    response = client.put(_draft_url(contest), {"description": "правка"}, format="json")

    assert response.status_code == 409


def test_cannot_submit_before_the_contest_starts(client: APIClient, participant) -> None:
    from datetime import timedelta

    from django.utils import timezone

    contest = ContestFactory(starts_at=timezone.now() + timedelta(days=1))

    assert client.post(_submit_url(contest), VALID, format="json").status_code == 409


# --- состояние контеста ----------------------------------------------------


def test_cannot_submit_to_a_draft_contest(client: APIClient, participant) -> None:
    contest = DraftContestFactory()

    assert client.post(_submit_url(contest), VALID, format="json").status_code == 404


def test_cannot_submit_to_an_archived_contest(client: APIClient, participant) -> None:
    from apps.contests.models import ContestStatus

    contest = ContestFactory(status=ContestStatus.ARCHIVED)

    assert client.post(_submit_url(contest), VALID, format="json").status_code == 404


# --- одна заявка на человека ----------------------------------------------


def test_second_submit_updates_the_same_submission(client: APIClient, participant) -> None:
    """«Засчитывается последняя отправка» — значит одна запись, а не история."""
    contest = ContestFactory()

    client.post(_submit_url(contest), VALID, format="json")
    client.post(_submit_url(contest), VALID | {"description": "второй заход"}, format="json")

    submission = Submission.objects.get()
    assert Submission.objects.count() == 1
    assert submission.description == "второй заход"


def test_resubmitting_does_not_move_the_submission_date(client, participant) -> None:
    contest = ContestFactory()
    client.post(_submit_url(contest), VALID, format="json")
    first = Submission.objects.get().submitted_at

    client.post(_submit_url(contest), VALID | {"description": "правка"}, format="json")

    assert Submission.objects.get().submitted_at == first


def test_two_people_can_submit_to_the_same_contest(client: APIClient, participant) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=UserFactory())

    client.post(_submit_url(contest), VALID, format="json")

    assert Submission.objects.filter(contest=contest).count() == 2


# --- валидация -------------------------------------------------------------


def test_submit_requires_a_github_url(client: APIClient, participant) -> None:
    contest = ContestFactory()

    response = client.post(_submit_url(contest), {"live_url": VALID["live_url"]}, format="json")

    assert response.status_code == 400
    assert "github_url" in response.json()["error"]["details"]


def test_submit_requires_a_live_url(client: APIClient, participant) -> None:
    contest = ContestFactory()

    response = client.post(_submit_url(contest), {"github_url": VALID["github_url"]}, format="json")

    assert response.status_code == 400
    assert "live_url" in response.json()["error"]["details"]


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "https://gitlab.com/user/repo",
        "https://github.com",
        "https://github.com/only-user",
        "https://evil.com/github.com/user/repo",
    ],
)
def test_non_github_repository_urls_are_rejected(client: APIClient, participant, url) -> None:
    contest = ContestFactory()

    response = client.post(_submit_url(contest), VALID | {"github_url": url}, format="json")

    assert response.status_code == 400
    assert "github_url" in response.json()["error"]["details"]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/sarahdev/ai-lint-agent",
        "http://github.com/sarahdev/ai-lint-agent",
        "https://www.github.com/sarahdev/ai-lint-agent",
        "https://GitHub.com/SarahDev/Ai-Lint-Agent",
    ],
)
def test_valid_github_urls_are_accepted(client: APIClient, participant, url) -> None:
    contest = ContestFactory()

    response = client.post(_submit_url(contest), VALID | {"github_url": url}, format="json")

    assert response.status_code == 200


def test_description_longer_than_500_characters_is_rejected(client, participant) -> None:
    contest = ContestFactory()

    response = client.post(_submit_url(contest), VALID | {"description": "я" * 501}, format="json")

    assert response.status_code == 400
    assert "description" in response.json()["error"]["details"]


# --- черновики -------------------------------------------------------------


def test_a_draft_may_be_saved_half_finished(client: APIClient, participant) -> None:
    """Кнопка «Сохранить черновик» не должна требовать заполненных ссылок."""
    contest = ContestFactory()

    response = client.put(_draft_url(contest), {"description": "пока думаю"}, format="json")

    assert response.status_code == 201
    assert Submission.objects.get().status == SubmissionStatus.DRAFT


def test_a_draft_still_rejects_a_malformed_github_url(client, participant) -> None:
    contest = ContestFactory()

    response = client.put(_draft_url(contest), {"github_url": "gitlab.com/x"}, format="json")

    assert response.status_code == 400


def test_a_submitted_entry_cannot_be_emptied(client: APIClient, participant) -> None:
    """Иначе можно было бы отправить решение и стереть ссылки, оставшись в списке."""
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=participant)

    response = client.put(_draft_url(contest), {"github_url": ""}, format="json")

    assert response.status_code == 400
    assert "github_url" in response.json()["error"]["details"]


def test_draft_becomes_submitted_only_through_submit(client: APIClient, participant) -> None:
    contest = ContestFactory()
    SubmissionFactory(contest=contest, user=participant)

    client.put(_draft_url(contest), {"status": "submitted"}, format="json")

    assert Submission.objects.get().status == SubmissionStatus.DRAFT


# --- доступ ----------------------------------------------------------------


def test_anonymous_cannot_submit(client: APIClient) -> None:
    contest = ContestFactory()

    assert client.post(_submit_url(contest), VALID, format="json").status_code == 401


def test_participant_only_sees_their_own_submission(client: APIClient, participant) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=UserFactory())

    response = client.get(_draft_url(contest))

    assert response.status_code == 200
    assert response.json()["submission"] is None
