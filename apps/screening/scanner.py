"""Поиск секретов в архиве репозитория."""

from __future__ import annotations

import io
import tarfile
from dataclasses import dataclass, field

from .patterns import PATTERNS, looks_like_placeholder

# Каталоги и файлы, которые смотреть бессмысленно: там чужой код и сборки.
SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "vendor",
        "dist",
        "build",
        ".next",
        "__pycache__",
        ".venv",
        "venv",
        "target",
        "Pods",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
    }
)

SKIP_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".svg",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".mp4",
        ".mov",
        ".mp3",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".lock",
        ".min.js",
        ".min.css",
        ".map",
        ".so",
        ".dylib",
        ".dll",
        ".exe",
        ".class",
        ".jar",
        ".pyc",
    }
)

SKIP_FILENAMES = frozenset(
    {"package-lock.json", "yarn.lock", "poetry.lock", "pnpm-lock.yaml", "Cargo.lock"}
)

MAX_FILE_BYTES = 512 * 1024
MAX_FILES = 4000
MAX_FINDINGS_PER_PATTERN = 5


@dataclass
class Finding:
    check: str
    severity: str
    title: str
    detail: str
    path: str = ""
    line: int = 0

    def as_dict(self) -> dict:
        return {
            "check": self.check,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "path": self.path,
            "line": self.line,
        }


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0


def should_scan(path: str) -> bool:
    parts = path.split("/")
    if any(part in SKIP_DIRS for part in parts):
        return False

    name = parts[-1]
    if name in SKIP_FILENAMES:
        return False
    return not any(name.endswith(suffix) for suffix in SKIP_SUFFIXES)


def scan_tarball(data: bytes) -> ScanResult:
    """Ищет секреты в tar.gz-архиве, который отдаёт GitHub."""
    result = ScanResult()
    counts: dict[str, int] = {}

    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive:
            if not member.isfile() or result.files_scanned >= MAX_FILES:
                continue

            # GitHub кладёт всё в каталог вида repo-<sha>; он в путях не нужен.
            path = member.name.split("/", 1)[-1] if "/" in member.name else member.name
            if not path or not should_scan(path):
                continue
            if member.size > MAX_FILE_BYTES:
                continue

            handle = archive.extractfile(member)
            if handle is None:
                continue

            try:
                text = handle.read().decode("utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # двоичный файл — пропускаем

            result.files_scanned += 1
            # Файлы-образцы существуют, чтобы показать формат значений, —
            # искать в них утечки бессмысленно.
            if not _is_example_file(path):
                _scan_text(path, text, result, counts)

            if _committed_env_file(path):
                result.findings.append(
                    Finding(
                        check="secrets",
                        severity="high",
                        title="Файл .env в репозитории",
                        detail="Файл с переменными окружения попал в историю коммитов.",
                        path=path,
                    )
                )

    return result


def _scan_text(path: str, text: str, result: ScanResult, counts: dict[str, int]) -> None:
    for number, line in enumerate(text.splitlines(), start=1):
        if len(line) > 1000:
            continue  # минифицированная строка — не читаем
        if looks_like_placeholder(line):
            continue

        for pattern in PATTERNS:
            if counts.get(pattern.key, 0) >= MAX_FINDINGS_PER_PATTERN:
                continue
            match = pattern.regex.search(line)
            if match is None:
                continue

            counts[pattern.key] = counts.get(pattern.key, 0) + 1
            result.findings.append(
                Finding(
                    check="secrets",
                    severity=pattern.severity,
                    title=pattern.title,
                    detail=_redact(match.group(0)),
                    path=path,
                    line=number,
                )
            )


EXAMPLE_SUFFIXES = (".example", ".sample", ".template", ".dist", ".default")


def _is_example_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    return any(name.endswith(suffix) for suffix in EXAMPLE_SUFFIXES)


def _committed_env_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    if not name.startswith(".env"):
        return False
    # .env.example и подобные — это документация, а не утечка.
    return not _is_example_file(path)


def _redact(secret: str) -> str:
    """Показываем начало и длину: полный ключ хранить у себя незачем."""
    visible = secret[:8]
    return f"{visible}… ({len(secret)} символов)"
