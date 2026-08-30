"""Проверка заявок админом и граница конфиденциальности."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contests.tests.factories import ContestFactory
from apps.submissions.models import Submission, SubmissionStatus
from apps.users.tests.factories import UserFactory

from .factories import SubmissionFactory, SubmittedFactory

pytestmark = pytest.mark.django_db


# --- что видит участник ----------------------------------------------------


def test_participant_never_sees_the_score_or_reviewer_notes(client, participant) -> None:
    """На макете проверки заметки помечены как невидимые для участника."""
    contest = ContestFactory()
    SubmittedFactory(
        contest=contest,
        user=participant,
        score=82,
        reviewer_notes="Слабая обработка ошибок",
        status=SubmissionStatus.REVIEWED,
    )

    body = client.get(reverse("my-submission", args=[contest.slug])).json()["submission"]

    assert "score" not in body
    assert "reviewer_notes" not in body
    assert "Слабая обработка ошибок" not in str(body)


def test_reviewer_notes_never_leak_through_the_profile(client, participant) -> None:
    SubmittedFactory(user=participant, reviewer_notes="внутренняя заметка")

    body = client.get(reverse("my-submission-list")).json()

    assert "внутренняя заметка" not in str(body)
    assert "score" not in str(body)


def test_reviewer_notes_never_leak_through_a_public_profile(client) -> None:
    user = UserFactory(username="sarah_dev")
    SubmittedFactory(user=user, reviewer_notes="внутренняя заметка", score=91)

    body = client.get(reverse("public-profile", args=["sarah_dev"])).json()

    assert "внутренняя заметка" not in str(body)
    # Проверяем именно отсутствие полей, а не подстроку «91»: короткое число
    # случайно встречается в идентификаторах и микросекундах дат.
    for row in body["submissions"]:
        assert "score" not in row
        assert "reviewer_notes" not in row


def test_participant_cannot_set_their_own_score(client: APIClient, participant) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest, user=participant)

    client.put(
        reverse("my-submission", args=[contest.slug]),
        {"score": 100, "is_winner": True},
        format="json",
    )

    submission = Submission.objects.get()
    assert submission.score is None
    assert not submission.is_winner


# --- доступ ----------------------------------------------------------------


def test_participant_cannot_open_the_review_queue(client: APIClient, participant) -> None:
    assert client.get(reverse("admin-submission-list")).status_code == 403


def test_anonymous_cannot_open_the_review_queue(client: APIClient) -> None:
    assert client.get(reverse("admin-submission-list")).status_code == 401


def test_participant_cannot_review_a_submission(client: APIClient, participant) -> None:
    submission = SubmittedFactory()

    response = client.patch(
        reverse("admin-submission-detail", args=[submission.pk]),
        {"score": 90},
        format="json",
    )

    assert response.status_code == 403


# --- очередь проверки ------------------------------------------------------


def test_queue_excludes_drafts(client: APIClient, admin) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    SubmissionFactory(contest=contest)  # черновик

    assert client.get(reverse("admin-submission-list")).json()["count"] == 1


def test_queue_can_be_filtered_by_contest(client: APIClient, admin) -> None:
    wanted = ContestFactory(title="Нужный")
    SubmittedFactory(contest=wanted)
    SubmittedFactory(contest=ContestFactory(title="Другой"))

    response = client.get(reverse("admin-submission-list"), {"contest": wanted.slug})

    assert response.json()["count"] == 1


def test_queue_can_be_filtered_to_pending_review(client: APIClient, admin) -> None:
    SubmittedFactory()
    SubmittedFactory(status=SubmissionStatus.REVIEWED)

    response = client.get(reverse("admin-submission-list"), {"status": "submitted"})

    assert response.json()["count"] == 1


def test_queue_can_be_filtered_to_winners(client: APIClient, admin) -> None:
    SubmittedFactory(is_winner=True)
    SubmittedFactory()

    assert client.get(reverse("admin-submission-list"), {"status": "winner"}).json()["count"] == 1


def test_queue_can_be_searched_by_participant(client: APIClient, admin) -> None:
    SubmittedFactory(user=UserFactory(username="sarah_dev"))
    SubmittedFactory(user=UserFactory(username="max_builds"))

    response = client.get(reverse("admin-submission-list"), {"search": "sarah"})

    assert response.json()["count"] == 1


# --- навигация по очереди --------------------------------------------------


def test_review_screen_reports_position_and_neighbours(client: APIClient, admin) -> None:
    """Экран проверки показывает «3 / 36» и стрелки — считает это сервер."""
    contest = ContestFactory()
    first, second, third = (SubmittedFactory(contest=contest) for _ in range(3))

    body = client.get(reverse("admin-submission-detail", args=[second.pk])).json()

    assert body["navigation"] == {
        "position": 2,
        "total": 3,
        "previous_id": first.pk,
        "next_id": third.pk,
    }


def test_first_submission_has_no_previous(client: APIClient, admin) -> None:
    contest = ContestFactory()
    first = SubmittedFactory(contest=contest)
    SubmittedFactory(contest=contest)

    body = client.get(reverse("admin-submission-detail", args=[first.pk])).json()
    navigation = body["navigation"]

    assert navigation["previous_id"] is None
    assert navigation["position"] == 1


def test_last_submission_has_no_next(client: APIClient, admin) -> None:
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    last = SubmittedFactory(contest=contest)

    body = client.get(reverse("admin-submission-detail", args=[last.pk])).json()
    navigation = body["navigation"]

    assert navigation["next_id"] is None
    assert navigation["position"] == 2


def test_navigation_stays_within_one_contest(client: APIClient, admin) -> None:
    only = SubmittedFactory(contest=ContestFactory(title="Первый"))
    SubmittedFactory(contest=ContestFactory(title="Второй"))

    body = client.get(reverse("admin-submission-detail", args=[only.pk])).json()
    navigation = body["navigation"]

    assert navigation == {"position": 1, "total": 1, "previous_id": None, "next_id": None}


# --- сохранение проверки ---------------------------------------------------


def test_admin_saves_score_notes_and_winner(client: APIClient, admin) -> None:
    submission = SubmittedFactory()

    response = client.patch(
        reverse("admin-submission-detail", args=[submission.pk]),
        {"score": 82, "reviewer_notes": "Отличная работа с агентом.", "is_winner": True},
        format="json",
    )

    assert response.status_code == 200
    submission.refresh_from_db()
    assert submission.score == 82
    assert submission.reviewer_notes == "Отличная работа с агентом."
    assert submission.is_winner
    assert submission.status == SubmissionStatus.REVIEWED
    assert submission.reviewed_by == admin
    assert submission.reviewed_at is not None


def test_winner_badge_overrides_the_reviewed_badge(client: APIClient, admin) -> None:
    submission = SubmittedFactory()

    body = client.patch(
        reverse("admin-submission-detail", args=[submission.pk]),
        {"score": 95, "is_winner": True},
        format="json",
    ).json()["submission"]

    assert body["status"] == "reviewed"
    assert body["display_status"] == "winner"


def test_winner_can_be_unset(client: APIClient, admin) -> None:
    submission = SubmittedFactory(is_winner=True)

    client.patch(
        reverse("admin-submission-detail", args=[submission.pk]),
        {"is_winner": False},
        format="json",
    )

    submission.refresh_from_db()
    assert not submission.is_winner


@pytest.mark.parametrize("score", [-1, 101, 1000])
def test_score_outside_zero_to_hundred_is_rejected(client: APIClient, admin, score) -> None:
    submission = SubmittedFactory()

    response = client.patch(
        reverse("admin-submission-detail", args=[submission.pk]),
        {"score": score},
        format="json",
    )

    assert response.status_code == 400


def test_admin_sees_the_notes_they_saved(client: APIClient, admin) -> None:
    submission = SubmittedFactory(reviewer_notes="внутренняя заметка", score=70)

    body = client.get(reverse("admin-submission-detail", args=[submission.pk])).json()

    assert body["submission"]["reviewer_notes"] == "внутренняя заметка"
    assert body["submission"]["score"] == 70


def test_reviewing_a_missing_submission_returns_not_found(client: APIClient, admin) -> None:
    response = client.get(reverse("admin-submission-detail", args=[9999]))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
