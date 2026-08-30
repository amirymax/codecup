"""Состояние контеста вычисляется, а не хранится."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.contests.models import Contest, ContestState, ContestStatus, validate_requirements

from .factories import ContestFactory, DraftContestFactory, EndedContestFactory

pytestmark = pytest.mark.django_db


def test_published_contest_before_deadline_is_live() -> None:
    assert ContestFactory().state == ContestState.LIVE


def test_published_contest_after_deadline_becomes_ended_without_any_job() -> None:
    contest = ContestFactory()
    contest.deadline = timezone.now() - timedelta(seconds=1)

    assert contest.state == ContestState.ENDED


def test_draft_stays_draft_regardless_of_deadline() -> None:
    assert DraftContestFactory().state == ContestState.DRAFT


def test_archived_contest_reports_archived() -> None:
    contest = ContestFactory(status=ContestStatus.ARCHIVED)

    assert contest.state == ContestState.ARCHIVED


def test_submissions_are_closed_after_the_deadline() -> None:
    assert ContestFactory().accepts_submissions
    assert not EndedContestFactory().accepts_submissions
    assert not DraftContestFactory().accepts_submissions


def test_submissions_are_closed_before_the_start() -> None:
    contest = ContestFactory(starts_at=timezone.now() + timedelta(days=1))

    assert not contest.accepts_submissions


# --- нумерация и адреса ----------------------------------------------------


def test_numbers_are_assigned_in_sequence() -> None:
    assert [ContestFactory().number for _ in range(3)] == [1, 2, 3]


def test_display_number_is_zero_padded() -> None:
    assert ContestFactory().display_number == "#01"


def test_russian_title_becomes_a_latin_slug() -> None:
    contest = ContestFactory(title="Создайте инструмент на базе ИИ")

    assert contest.slug == "sozdayte-instrument-na-baze-ii"


def test_duplicate_titles_get_distinct_slugs() -> None:
    first = ContestFactory(title="Один и тот же")
    second = ContestFactory(title="Один и тот же")

    assert first.slug != second.slug
    assert second.slug.endswith("-2")


def test_untranslatable_title_falls_back_to_the_number() -> None:
    contest = ContestFactory(title="!!!")

    assert contest.slug == f"contest-{contest.number}"


def test_slug_is_not_rewritten_on_rename() -> None:
    """Адрес контеста не должен ломаться из-за правки названия."""
    contest = ContestFactory(title="Первое название")
    original = contest.slug

    contest.title = "Совсем другое название"
    contest.save()

    assert contest.slug == original


# --- требования ------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["не список", [123], [""], ["   "], [["вложенный"]], ["x" * 301], [f"т{i}" for i in range(21)]],
)
def test_invalid_requirements_are_rejected(value) -> None:
    with pytest.raises(ValidationError):
        validate_requirements(value)


def test_valid_requirements_pass() -> None:
    validate_requirements(["Репозиторий GitHub", "Демо-ссылка"])


def test_empty_requirements_are_allowed() -> None:
    validate_requirements([])


# --- выборки ---------------------------------------------------------------


def test_public_queryset_hides_drafts_and_archive() -> None:
    live = ContestFactory()
    DraftContestFactory()
    ContestFactory(status=ContestStatus.ARCHIVED)

    assert list(Contest.objects.public()) == [live]


def test_live_and_ended_querysets_split_by_deadline() -> None:
    live = ContestFactory()
    ended = EndedContestFactory()

    assert list(Contest.objects.live()) == [live]
    assert list(Contest.objects.ended()) == [ended]


def test_publish_moves_a_draft_to_published() -> None:
    contest = DraftContestFactory()

    contest.publish()
    contest.refresh_from_db()

    assert contest.status == ContestStatus.PUBLISHED
