"""Обращения к GitHub API.

Токен необязателен, но без него лимит — 60 запросов в час на IP, чего мало
даже для одного контеста. С токеном лимит 5000.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from django.conf import settings

API = "https://api.github.com"
REPO_URL = re.compile(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", re.IGNORECASE)


class GitHubError(RuntimeError):
    pass


class RepoNotFound(GitHubError):
    pass


@dataclass(frozen=True)
class RepoRef:
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


def parse_repo_url(url: str) -> RepoRef | None:
    match = REPO_URL.match(url or "")
    if match is None:
        return None
    owner, name = match.group(1), match.group(2)
    return RepoRef(owner, name.removesuffix(".git"))


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.timeout = settings.GITHUB_REQUEST_TIMEOUT

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "codecup-screening"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, path: str, **params) -> httpx.Response:
        response = httpx.get(
            f"{API}{path}",
            headers=self._headers(),
            params=params or None,
            timeout=self.timeout,
            follow_redirects=True,
        )
        if response.status_code == 404:
            raise RepoNotFound(path)
        if response.status_code >= 400:
            raise GitHubError(f"{path}: HTTP {response.status_code}")
        return response

    def repo(self, ref: RepoRef) -> dict:
        return self._get(f"/repos/{ref.owner}/{ref.name}").json()

    def has_readme(self, ref: RepoRef) -> bool:
        try:
            self._get(f"/repos/{ref.owner}/{ref.name}/readme")
        except RepoNotFound:
            return False
        return True

    def commits_since(self, ref: RepoRef, since: datetime, limit: int = 100) -> list[dict]:
        response = self._get(
            f"/repos/{ref.owner}/{ref.name}/commits",
            since=since.isoformat(),
            per_page=limit,
        )
        return response.json()

    def tarball(self, ref: RepoRef, max_bytes: int) -> bytes:
        """Архив репозитория. Обрываем чтение, если он слишком велик."""
        url = f"{API}/repos/{ref.owner}/{ref.name}/tarball"
        chunks: list[bytes] = []
        size = 0

        with httpx.stream(
            "GET", url, headers=self._headers(), timeout=self.timeout, follow_redirects=True
        ) as response:
            if response.status_code == 404:
                raise RepoNotFound(url)
            if response.status_code >= 400:
                raise GitHubError(f"tarball: HTTP {response.status_code}")

            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > max_bytes:
                    raise GitHubError("Репозиторий больше допустимого размера.")
                chunks.append(chunk)

        return b"".join(chunks)
