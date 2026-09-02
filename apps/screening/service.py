"""Четыре проверки присланной заявки.

Ни одна не блокирует отправку: находки собираются для проверяющего.
"""

from __future__ import annotations

import logging

import httpx
from django.conf import settings

from .github import GitHubClient, GitHubError, RepoNotFound, parse_repo_url
from .models import ScreeningStatus, SubmissionScreening
from .scanner import Finding, scan_tarball

logger = logging.getLogger(__name__)


def screen_submission(submission, client: GitHubClient | None = None) -> SubmissionScreening:
    screening, _ = SubmissionScreening.objects.get_or_create(submission=submission)
    screening.status = ScreeningStatus.PENDING
    screening.save(update_fields=["status"])

    client = client or GitHubClient()
    ref = parse_repo_url(submission.github_url)

    if ref is None:
        screening.finish(
            findings=[
                Finding(
                    "repo",
                    "high",
                    "Ссылка не ведёт на репозиторий GitHub",
                    submission.github_url or "—",
                ).as_dict()
            ],
            repo_meta={},
            live_status=_check_live_url(submission.live_url),
            files_scanned=0,
        )
        return screening

    findings: list[Finding] = []
    repo_meta: dict = {}
    files_scanned = 0

    try:
        repo_meta, meta_findings = _check_repo(client, ref, submission)
        findings.extend(meta_findings)

        if repo_meta.get("private") is not True:
            files_scanned, secret_findings = _check_secrets(client, ref)
            findings.extend(secret_findings)
    except RepoNotFound:
        findings.append(
            Finding(
                "repo", "high", "Репозиторий недоступен", f"{ref.full_name} не найден или скрыт"
            )
        )
    except (GitHubError, httpx.HTTPError) as exc:
        # Сеть подвела — это не находка о работе участника, а сбой проверки.
        screening.fail(str(exc))
        return screening

    screening.finish(
        findings=[item.as_dict() for item in findings],
        repo_meta=repo_meta,
        live_status=_check_live_url(submission.live_url),
        files_scanned=files_scanned,
    )
    return screening


def _check_repo(client: GitHubClient, ref, submission) -> tuple[dict, list[Finding]]:
    """Репозиторий существует, открыт, с README и работой внутри срока."""
    data = client.repo(ref)
    findings: list[Finding] = []

    meta = {
        "full_name": data.get("full_name", ref.full_name),
        "private": data.get("private", False),
        "size_kb": data.get("size", 0),
        "stars": data.get("stargazers_count", 0),
        "created_at": data.get("created_at"),
        "pushed_at": data.get("pushed_at"),
        "default_branch": data.get("default_branch", "main"),
        "license": (data.get("license") or {}).get("spdx_id"),
    }

    if meta["private"]:
        findings.append(
            Finding("repo", "high", "Репозиторий закрыт", "Требуется публичный репозиторий.")
        )
    if meta["size_kb"] == 0:
        findings.append(Finding("repo", "high", "Репозиторий пуст", "В нём нет файлов."))
    if not client.has_readme(ref):
        findings.append(
            Finding("repo", "medium", "Нет README", "В требованиях контеста README обязателен.")
        )

    findings.extend(_check_contest_window(client, ref, submission, meta))
    return meta, findings


def _check_contest_window(client: GitHubClient, ref, submission, meta: dict) -> list[Finding]:
    """Работа должна вестись во время контеста, а не быть принесённой готовой."""
    contest = submission.contest
    window_start = contest.starts_at or contest.created_at
    if window_start is None:
        return []

    try:
        commits = client.commits_since(ref, window_start, limit=5)
    except (GitHubError, httpx.HTTPError):
        return []  # проверка необязательная, ради неё падать не стоит

    if commits:
        return []

    return [
        Finding(
            "timeline",
            "medium",
            "Нет коммитов за время контеста",
            f"Последняя запись в репозитории — {meta.get('pushed_at') or 'неизвестно'}.",
        )
    ]


def _check_secrets(client: GitHubClient, ref) -> tuple[int, list[Finding]]:
    data = client.tarball(ref, max_bytes=settings.SCREENING_MAX_TARBALL_BYTES)
    result = scan_tarball(data)
    return result.files_scanned, result.findings


def _check_live_url(url: str) -> int | None:
    """Код ответа живой демонстрации; None, если достучаться не вышло."""
    if not url:
        return None
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
    except httpx.HTTPError:
        return None
    return response.status_code
