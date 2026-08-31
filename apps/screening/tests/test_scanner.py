"""Поиск секретов в архиве репозитория.

Сеть здесь не нужна: архивы собираются в памяти.
"""

from __future__ import annotations

import io
import tarfile

import pytest

from apps.screening.scanner import scan_tarball, should_scan


def make_tarball(files: dict[str, str]) -> bytes:
    """Архив в том же виде, в каком его отдаёт GitHub: всё внутри repo-<sha>/."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            payload = content.encode()
            info = tarfile.TarInfo(name=f"repo-abc1234/{name}")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def titles(files: dict[str, str]) -> list[str]:
    return [finding.title for finding in scan_tarball(make_tarball(files)).findings]


# --- что должно находиться -------------------------------------------------


# Образцы собираются из кусков, а не пишутся целиком.
#
# Это не украшательство: строку вида sk_live_… в этом файле заблокировала
# push-защита самого GitHub. Шаблоны обязаны быть похожи на настоящие ключи,
# поэтому и выглядят как настоящие — а значит, в исходник их класть нельзя.
def fake(*parts: str) -> str:
    return "".join(parts)


AWS_SAMPLE = fake("AKIA", "ZZ7WQ4NKPLMXQ2AB")


SAMPLES = [
    ("Ключ доступа AWS", AWS_SAMPLE),
    ("Токен GitHub", fake("gh", "p_", "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8")),
    ("Токен Telegram-бота", fake("1234567890", ":", "AAHkq2ZmNvXpQrStUvWxYz0123456789abc")),
    ("Ключ Anthropic", fake("sk", "-ant-", "api03-AbCdEfGhIjKlMnOpQrStUv")),
    ("Ключ Google API", fake("AIza", "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q")),
    ("Токен Slack", fake("xox", "b-", "1234567890-abcdefghijkl")),
    ("Боевой ключ Stripe", fake("sk", "_live_", "A1b2C3d4E5f6G7h8I9j0K1l2")),
    ("Приватный ключ", fake("-----BEGIN RSA ", "PRIVATE KEY-----")),
    ("Строка подключения к базе с паролем", fake("postgres://app:", "h7Kd93jXm", "@db.host/app")),
]


@pytest.mark.parametrize(("name", "secret"), SAMPLES, ids=[name for name, _ in SAMPLES])
def test_real_looking_secrets_are_found(name: str, secret: str) -> None:
    assert name in titles({"src/config.py": f'value = "{secret}"'})


def test_a_committed_env_file_is_reported() -> None:
    assert "Файл .env в репозитории" in titles({".env": "TOKEN=abc"})


def test_the_finding_records_where_it_is() -> None:
    files = {"a.py": "ok\nok\nAWS = '" + AWS_SAMPLE + "'"}

    finding = scan_tarball(make_tarball(files)).findings[0]

    assert finding.path == "a.py"
    assert finding.line == 3


def test_the_secret_itself_is_not_stored_in_full() -> None:
    """Хранить чужой ключ у себя — значит просто перенести утечку к себе."""
    secret = AWS_SAMPLE
    files = {"a.py": f"AWS = '{secret}'"}

    finding = scan_tarball(make_tarball(files)).findings[0]

    assert secret not in finding.detail
    assert finding.detail.startswith(secret[:8])


# --- что находиться не должно ----------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        'KEY = "sk-your-key-here"',
        'KEY = os.environ["OPENAI_API_KEY"]',
        "KEY = process.env.SECRET_TOKEN",
        'AWS_KEY = "' + "AKIA" + 'IOSFODNN7EXAMPLE"',
        'password = "changeme"',
        'DB = "postgres://user:' + "password" + '@localhost/db"',
        'token = "<your-token>"',
        'key = "${GITHUB_TOKEN}"',
    ],
)
def test_placeholders_are_not_reported(line: str) -> None:
    assert titles({"README.md": line}) == []


def test_example_files_are_skipped_entirely() -> None:
    """Файл-образец существует ради формата значений, а не ради значений."""
    assert titles({".env.example": 'DB = "postgres://app:h7Kd93jXm@db.host/app"'}) == []


def test_dependencies_are_not_scanned() -> None:
    secret = f'AWS = "{AWS_SAMPLE}"'

    assert titles({"node_modules/pkg/index.js": secret}) == []
    assert titles({"vendor/lib.py": secret}) == []
    assert titles({".git/config": secret}) == []


def test_lock_files_and_binaries_are_skipped() -> None:
    assert not should_scan("package-lock.json")
    assert not should_scan("logo.png")
    assert not should_scan("app/bundle.min.js")
    assert should_scan("src/main.py")


def test_minified_lines_are_ignored() -> None:
    """Одна строка на сотни килобайт — это сборка, а не исходник."""
    long_line = "x" * 1200 + f' AWS = "{AWS_SAMPLE}"'

    assert titles({"app.js": long_line}) == []


def test_binary_files_do_not_break_the_scan() -> None:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        payload = b"\x00\x01\x02\xff\xfe"
        info = tarfile.TarInfo(name="repo-abc/logo.bin")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
        text = f'AWS = "{AWS_SAMPLE}"'.encode()
        info = tarfile.TarInfo(name="repo-abc/app.py")
        info.size = len(text)
        archive.addfile(info, io.BytesIO(text))

    result = scan_tarball(buffer.getvalue())

    assert [f.title for f in result.findings] == ["Ключ доступа AWS"]


def test_the_same_pattern_is_not_reported_endlessly() -> None:
    """Иначе один цикл с ключом даёт сотни одинаковых находок."""
    line = f'AWS = "{AWS_SAMPLE}"'
    files = {f"file_{i}.py": line for i in range(40)}

    assert len(scan_tarball(make_tarball(files)).findings) <= 5


def test_an_empty_repository_yields_nothing() -> None:
    assert titles({"README.md": "# Проект"}) == []
