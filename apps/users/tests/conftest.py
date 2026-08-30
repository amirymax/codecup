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

    monkeypatch.setattr("apps.telegrambot.client.TelegramClient.call", fake_call)
    return calls
