from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def telegram_settings(settings):
    """Бот «настроен», но сеть в тестах не трогаем."""
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_BOT_USERNAME = "CodeCupBot"
    settings.TELEGRAM_WEBHOOK_SECRET = "webhook-secret"
    return settings


@pytest.fixture(autouse=True)
def no_telegram_calls(monkeypatch):
    """Перехватывает все обращения к Bot API и записывает их.

    Тесты проверяют, что бот отправил нужное, не выходя в сеть.
    """
    calls: list[tuple[str, dict]] = []

    def fake_call(self, method, **payload):
        calls.append((method, payload))
        return {"message_id": 99}

    def fake_send_file(self, method, *, field, filename, content, **payload):
        calls.append(
            (method, payload | {"field": field, "filename": filename, "content": content})
        )
        return {"message_id": 99}

    monkeypatch.setattr("apps.telegrambot.client.TelegramClient.call", fake_call)
    monkeypatch.setattr("apps.telegrambot.client.TelegramClient.send_file", fake_send_file)
    return calls


def _authenticate(client, user):
    from django.conf import settings

    from apps.users.cookies import issue_tokens

    access, refresh = issue_tokens(user)
    client.cookies[settings.AUTH_COOKIE_ACCESS_NAME] = access
    client.cookies[settings.AUTH_COOKIE_REFRESH_NAME] = refresh
    return user


@pytest.fixture
def participant(client):
    from .factories import UserFactory

    return _authenticate(client, UserFactory())


@pytest.fixture
def admin(client):
    from .factories import AdminFactory

    return _authenticate(client, AdminFactory())
