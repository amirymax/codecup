"""Проверка заявки целиком. GitHub и живая демонстрация подменяются."""

from __future__ import annotations

from datetime import timedelta

import httpx
import pytest
from django.utils import timezone

from apps.contests.tests.factories import ContestFactory
from apps.screening.github import GitHubError, RepoNotFound, RepoRef, parse_repo_url
from apps.screening.models import ScreeningStatus, SubmissionScreening
from apps.screening.service import screen_submission
from apps.submissions.tests.factories import SubmittedFactory

from .test_scanner import AWS_SAMPLE, make_tarball

pytestmark = pytest.mark.django_db


class FakeGitHub:
    def __init__(self, *, repo=None, readme=True, commits=None, files=None, raises=None):
        self._repo = repo or {
            "full_name": "dev/project",
            "private": False,
            "size": 120,
            "stargazers_count": 3,
            "created_at": "2026-08-01T00:00:00Z",
            "pushed_at": "2026-08-20T00:00:00Z",
            "default_branch": "main",
        }
        self._readme = readme
        self._commits = commits if commits is not None else [{"sha": "abc"}]
        self._files = files or {"README.md": "# Проект"}
        self._raises = raises

    def repo(self, ref):
        if self._raises:
            raise self._raises
        return self._repo

    def has_readme(self, ref):
        return self._readme

    def commits_since(self, ref, since, limit=100):
        return self._commits

    def tarball(self, ref, max_bytes):
        return make_tarball(self._files)


@pytest.fixture(autouse=True)
def no_live_check(monkeypatch):
    """По умолчанию живую ссылку не дёргаем."""
    monkeypatch.setattr(
        httpx, "get", lambda *a, **k: httpx.Response(200, request=httpx.Request("GET", "https://x"))
    )


def titles(screening) -> list[str]:
    return [item["title"] for item in screening.findings]


# --- разбор ссылки ---------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/dev/project", RepoRef("dev", "project")),
        ("https://www.github.com/dev/project/", RepoRef("dev", "project")),
        ("https://github.com/dev/project.git", RepoRef("dev", "project")),
        ("https://github.com/dev/project/tree/main", RepoRef("dev", "project")),
        ("https://gitlab.com/dev/project", None),
        ("не ссылка", None),
    ],
)
def test_repo_url_parsing(url: str, expected) -> None:
    assert parse_repo_url(url) == expected


# --- проверки --------------------------------------------------------------


def test_a_clean_repository_produces_no_findings() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub())

    assert screening.status == ScreeningStatus.DONE
    assert screening.findings == []


def test_a_secret_in_the_repository_is_reported() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")
    client = FakeGitHub(files={"app.py": f'AWS = "{AWS_SAMPLE}"'})

    screening = screen_submission(submission, client=client)

    assert "Ключ доступа AWS" in titles(screening)
    assert screening.high_severity_count == 1


def test_a_missing_repository_is_reported() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/gone")

    screening = screen_submission(submission, client=FakeGitHub(raises=RepoNotFound("нет")))

    assert "Репозиторий недоступен" in titles(screening)


def test_a_private_repository_is_reported_and_not_downloaded() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")
    client = FakeGitHub(repo={**FakeGitHub()._repo, "private": True})

    screening = screen_submission(submission, client=client)

    assert "Репозиторий закрыт" in titles(screening)
    assert screening.files_scanned == 0


def test_a_missing_readme_is_reported() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub(readme=False))

    assert "Нет README" in titles(screening)


def test_an_empty_repository_is_reported() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")
    client = FakeGitHub(repo={**FakeGitHub()._repo, "size": 0})

    screening = screen_submission(submission, client=client)

    assert "Репозиторий пуст" in titles(screening)


def test_work_done_before_the_contest_is_flagged() -> None:
    """Готовый проект, принесённый со стороны, — это заметно по коммитам."""
    contest = ContestFactory(starts_at=timezone.now() - timedelta(days=2))
    submission = SubmittedFactory(contest=contest, github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub(commits=[]))

    assert "Нет коммитов за время контеста" in titles(screening)


def test_a_non_github_link_is_reported_without_calling_the_api() -> None:
    submission = SubmittedFactory(github_url="https://gitlab.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub(raises=AssertionError("вызван")))

    assert "Ссылка не ведёт на репозиторий GitHub" in titles(screening)


def test_repository_metadata_is_kept_for_the_reviewer() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub())

    assert screening.repo_meta["stars"] == 3
    assert screening.repo_meta["default_branch"] == "main"


# --- живая демонстрация ----------------------------------------------------


def test_the_live_url_status_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx, "get", lambda *a, **k: httpx.Response(503, request=httpx.Request("GET", "https://x"))
    )
    submission = SubmittedFactory(github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub())

    assert screening.live_status == 503


def test_an_unreachable_demo_leaves_the_status_empty(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise httpx.ConnectError("нет связи")

    monkeypatch.setattr(httpx, "get", boom)
    submission = SubmittedFactory(github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub())

    assert screening.live_status is None


# --- сбои ------------------------------------------------------------------


def test_a_github_outage_is_a_failed_check_not_a_finding() -> None:
    """Сбой у нас не должен выглядеть как претензия к работе участника."""
    submission = SubmittedFactory(github_url="https://github.com/dev/project")

    screening = screen_submission(submission, client=FakeGitHub(raises=GitHubError("HTTP 502")))

    assert screening.status == ScreeningStatus.FAILED
    assert screening.findings == []
    assert "502" in screening.error


def test_rechecking_replaces_the_previous_result() -> None:
    submission = SubmittedFactory(github_url="https://github.com/dev/project")
    screen_submission(submission, client=FakeGitHub(files={"a.py": f'k = "{AWS_SAMPLE}"'}))

    screening = screen_submission(submission, client=FakeGitHub())

    assert screening.findings == []
    # Перечитываем: Django кеширует обратную связь на объекте заявки.
    submission.refresh_from_db()
    assert SubmissionScreening.objects.get(submission=submission).findings == []
    assert SubmissionScreening.objects.filter(submission=submission).count() == 1
