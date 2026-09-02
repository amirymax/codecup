"""Шаблоны секретов, которые ищем в присланных репозиториях.

Задача — заметить настоящую утечку, а не поймать каждое совпадение. Поэтому
рядом с шаблонами живут признаки заведомо учебных значений: в примерах и
тестовых данных «ключи» встречаются постоянно, и без отсева список находок
станет бесполезным.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretPattern:
    key: str
    title: str
    severity: str  # high | medium
    regex: re.Pattern[str]


PATTERNS: tuple[SecretPattern, ...] = (
    SecretPattern(
        "aws_access_key",
        "Ключ доступа AWS",
        "high",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    SecretPattern(
        "github_token",
        "Токен GitHub",
        "high",
        re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,})\b"),
    ),
    SecretPattern(
        "telegram_bot_token",
        "Токен Telegram-бота",
        "high",
        re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{35}\b"),
    ),
    SecretPattern(
        "anthropic_key",
        "Ключ Anthropic",
        "high",
        re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    ),
    SecretPattern(
        "openai_key",
        "Ключ OpenAI",
        "high",
        re.compile(r"\bsk-(proj-)?[A-Za-z0-9]{20,}\b"),
    ),
    SecretPattern(
        "google_api_key",
        "Ключ Google API",
        "high",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ),
    SecretPattern(
        "slack_token",
        "Токен Slack",
        "high",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    ),
    SecretPattern(
        "stripe_key",
        "Боевой ключ Stripe",
        "high",
        re.compile(r"\bsk_live_[0-9a-zA-Z]{16,}\b"),
    ),
    SecretPattern(
        "private_key",
        "Приватный ключ",
        "high",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    ),
    SecretPattern(
        "database_url",
        "Строка подключения к базе с паролем",
        "high",
        re.compile(r"\b(?:postgres|postgresql|mysql|mongodb)(?:\+\w+)?://[^:\s/]+:[^@\s]{6,}@"),
    ),
    SecretPattern(
        "generic_secret",
        "Похоже на пароль или ключ в коде",
        "medium",
        re.compile(
            r"""(?ix)
            \b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\b
            \s*[:=]\s*
            ['"]([^'"\s]{12,})['"]
            """
        ),
    ),
)

# Строки с такими словами почти всегда пример, а не утечка.
PLACEHOLDER_MARKERS = (
    "example",
    "placeholder",
    "your-",
    "your_",
    "yourkey",
    "changeme",
    "change-me",
    "dummy",
    "sample",
    "test-key",
    "xxxxx",
    "<",
    "${",
    "{{",
    "os.environ",
    "process.env",
    "getenv",
    "replace",
    "todo",
    "fake",
    # Учебные значения в строках подключения.
    "user:password",
    ":password@",
    ":secret@",
    "localhost",
    "127.0.0.1",
)


def looks_like_placeholder(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)
