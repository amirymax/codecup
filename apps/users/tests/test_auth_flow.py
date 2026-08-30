"""Сквозной сценарий входа: старт → вебхук → подтверждение → обмен на куки."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import AuthTokenStatus, TelegramAuthToken, User

from .factories import callback_update, start_update

pytestmark = pytest.mark.django_db


def _webhook_url() -> str:
    return reverse("telegram-webhook", args=[settings.TELEGRAM_WEBHOOK_SECRET])


def _post_update(client: APIClient, update: dict):
    return client.post(
        _webhook_url(),
        update,
        format="json",
        HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=settings.TELEGRAM_WEBHOOK_SECRET,
    )


def test_full_login_flow_sets_cookies_and_creates_the_user(client: APIClient) -> None:
    start = client.post(reverse("auth-telegram-start"))
    assert start.status_code == 200
    nonce = start.json()["nonce"]
    client_secret = start.json()["client_secret"]
    assert start.json()["deep_link"] == f"https://t.me/CodeCupBot?start={nonce}"

    # Пока в Telegram ничего не нажали — статус pending.
    status_url = reverse("auth-telegram-status")
    assert client.get(status_url, {"nonce": nonce}).json()["status"] == "pending"

    # Пользователь открывает бота по deep link и жмёт «Подтвердить».
    assert _post_update(client, start_update(nonce)).status_code == 200
    assert _post_update(client, callback_update("confirm", nonce)).status_code == 200

    assert client.get(status_url, {"nonce": nonce}).json()["status"] == "confirmed"

    exchange = client.post(
        reverse("auth-telegram-exchange"),
        {"nonce": nonce, "client_secret": client_secret},
        format="json",
    )
    assert exchange.status_code == 200
    assert exchange.json()["telegram_username"] == "sarah_dev"

    # Токены пришли только в httpOnly-куках, в теле ответа их нет.
    assert "access" not in exchange.json()
    access_cookie = exchange.cookies[settings.AUTH_COOKIE_ACCESS_NAME]
    refresh_cookie = exchange.cookies[settings.AUTH_COOKIE_REFRESH_NAME]
    assert access_cookie["httponly"] is True
    assert refresh_cookie["httponly"] is True
    assert refresh_cookie["path"] == settings.AUTH_COOKIE_REFRESH_PATH

    user = User.objects.get(telegram_id=555_001)
    assert user.username == "sarah_dev"
    assert not user.has_usable_password()

    # Кука работает как удостоверение.
    me = client.get(reverse("auth-me"))
    assert me.status_code == 200
    assert me.json()["username"] == "sarah_dev"


def test_nonce_alone_is_not_enough_to_get_a_session(client: APIClient) -> None:
    """Код виден в Telegram, поэтому без секрета браузера он бесполезен."""
    start = client.post(reverse("auth-telegram-start")).json()
    _post_update(client, callback_update("confirm", start["nonce"]))

    response = client.post(
        reverse("auth-telegram-exchange"),
        {"nonce": start["nonce"], "client_secret": "секрет-злоумышленника"},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "auth_token_invalid"
    assert settings.AUTH_COOKIE_ACCESS_NAME not in response.cookies


def test_token_can_only_be_exchanged_once(client: APIClient) -> None:
    start = client.post(reverse("auth-telegram-start")).json()
    _post_update(client, callback_update("confirm", start["nonce"]))
    payload = {"nonce": start["nonce"], "client_secret": start["client_secret"]}

    assert client.post(reverse("auth-telegram-exchange"), payload, format="json").status_code == 200

    second = client.post(reverse("auth-telegram-exchange"), payload, format="json")
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "auth_token_invalid"


def test_unconfirmed_token_cannot_be_exchanged(client: APIClient) -> None:
    start = client.post(reverse("auth-telegram-start")).json()

    response = client.post(
        reverse("auth-telegram-exchange"),
        {"nonce": start["nonce"], "client_secret": start["client_secret"]},
        format="json",
    )

    assert response.status_code == 409


def test_expired_token_reports_expired_and_cannot_be_confirmed(client: APIClient) -> None:
    start = client.post(reverse("auth-telegram-start")).json()
    token = TelegramAuthToken.objects.get(nonce=start["nonce"])
    token.expires_at = timezone.now() - timedelta(seconds=1)
    token.save(update_fields=["expires_at"])

    status_response = client.get(reverse("auth-telegram-status"), {"nonce": start["nonce"]})
    assert status_response.json()["status"] == "expired"

    _post_update(client, callback_update("confirm", start["nonce"]))
    token.refresh_from_db()
    assert token.status == AuthTokenStatus.PENDING
    assert token.user is None


def test_unknown_nonce_looks_the_same_as_an_expired_one(client: APIClient) -> None:
    response = client.get(reverse("auth-telegram-status"), {"nonce": "нет-такого-кода"})

    assert response.status_code == 200
    assert response.json()["status"] == "expired"


def test_cancelling_in_telegram_stops_the_login(client: APIClient) -> None:
    start = client.post(reverse("auth-telegram-start")).json()

    _post_update(client, callback_update("cancel", start["nonce"]))

    assert (
        client.get(reverse("auth-telegram-status"), {"nonce": start["nonce"]}).json()["status"]
        == "cancelled"
    )
    assert not User.objects.exists()


def test_start_is_refused_when_the_bot_is_not_configured(client: APIClient, settings) -> None:
    settings.TELEGRAM_BOT_USERNAME = ""

    response = client.post(reverse("auth-telegram-start"))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "telegram_not_configured"


def test_me_requires_authentication(client: APIClient) -> None:
    assert client.get(reverse("auth-me")).status_code == 401


def test_returning_user_is_matched_by_telegram_id_not_username(client: APIClient) -> None:
    """Человек сменил @username — это всё ещё тот же аккаунт."""
    first = client.post(reverse("auth-telegram-start")).json()
    _post_update(client, callback_update("confirm", first["nonce"]))

    second = client.post(reverse("auth-telegram-start")).json()
    _post_update(client, callback_update("confirm", second["nonce"], username="sarah_ships"))

    assert User.objects.count() == 1
    user = User.objects.get()
    assert user.telegram_username == "sarah_ships"
    assert user.username == "sarah_dev"  # исходный логин на сайте не меняется
