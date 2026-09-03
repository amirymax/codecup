"""Кого считать участником контеста."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payments.models import PaymentStatus
from apps.payments.tests.factories import PaidContestFactory, PaymentFactory
from apps.submissions.tests.factories import SubmissionFactory, SubmittedFactory
from apps.users.tests.factories import UserFactory

from .factories import ContestFactory

pytestmark = pytest.mark.django_db


def _count(client: APIClient, contest) -> int:
    return client.get(reverse("contest-detail", args=[contest.slug])).json()["participants_count"]


def test_an_accepted_receipt_counts_even_without_a_submission(
    client: APIClient, admin_user
) -> None:
    """Человек заплатил и участвует, даже если работу пришлёт в последний день."""
    contest = PaidContestFactory()
    payment = PaymentFactory(contest=contest, status=PaymentStatus.PENDING)
    payment.accept(admin_user)

    assert _count(client, contest) == 1


def test_a_receipt_still_being_checked_does_not_count(client: APIClient) -> None:
    contest = PaidContestFactory()
    PaymentFactory(contest=contest, status=PaymentStatus.PENDING)

    assert _count(client, contest) == 0


def test_a_rejected_receipt_does_not_count(client: APIClient, admin_user) -> None:
    contest = PaidContestFactory()
    payment = PaymentFactory(contest=contest, status=PaymentStatus.PENDING)
    payment.reject(admin_user, "Не видно суммы")

    assert _count(client, contest) == 0


def test_paying_and_submitting_is_still_one_person(client: APIClient, admin_user) -> None:
    contest = PaidContestFactory()
    user = UserFactory()
    payment = PaymentFactory(contest=contest, user=user, status=PaymentStatus.PENDING)
    payment.accept(admin_user)
    SubmittedFactory(contest=contest, user=user)

    assert _count(client, contest) == 1


def test_each_paying_participant_is_counted_once(client: APIClient, admin_user) -> None:
    contest = PaidContestFactory()
    for _ in range(3):
        payment = PaymentFactory(contest=contest, status=PaymentStatus.PENDING)
        payment.accept(admin_user)

    assert _count(client, contest) == 3


def test_a_free_contest_counts_submitted_work(client: APIClient) -> None:
    """Платить не за что, поэтому участие — это присланная работа."""
    contest = ContestFactory()
    SubmittedFactory(contest=contest)
    SubmittedFactory(contest=contest)
    SubmissionFactory(contest=contest)  # черновик — это ещё не участие

    assert _count(client, contest) == 2


def test_the_landing_shows_the_same_number(client: APIClient, admin_user) -> None:
    contest = PaidContestFactory(is_featured=True)
    payment = PaymentFactory(contest=contest, status=PaymentStatus.PENDING)
    payment.accept(admin_user)

    body = client.get(reverse("contest-featured")).json()

    assert body["contest"]["participants_count"] == 1


def test_the_list_shows_the_same_number(client: APIClient, admin_user) -> None:
    contest = PaidContestFactory()
    payment = PaymentFactory(contest=contest, status=PaymentStatus.PENDING)
    payment.accept(admin_user)

    body = client.get(reverse("contest-list")).json()

    row = next(r for r in body["results"] if r["slug"] == contest.slug)
    assert row["participants_count"] == 1
