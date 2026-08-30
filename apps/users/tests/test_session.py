"""Обновление и завершение сессии."""

from __future__ import annotations

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.cookies import issue_tokens

from .factories import UserFactory

pytestmark = pytest.mark.django_db


def _login(client: APIClient):
    user = UserFactory()
    access, refresh = issue_tokens(user)
    client.cookies[settings.AUTH_COOKIE_ACCESS_NAME] = access
    client.cookies[settings.AUTH_COOKIE_REFRESH_NAME] = refresh
    return user


def test_refresh_issues_a_new_access_cookie(client: APIClient) -> None:
    _login(client)

    response = client.post(reverse("auth-refresh"))

    assert response.status_code == 204
    assert response.cookies[settings.AUTH_COOKIE_ACCESS_NAME].value


def test_refresh_rotates_the_refresh_cookie(client: APIClient) -> None:
    _login(client)
    before = client.cookies[settings.AUTH_COOKIE_REFRESH_NAME].value

    response = client.post(reverse("auth-refresh"))

    assert response.cookies[settings.AUTH_COOKIE_REFRESH_NAME].value != before


def test_refresh_without_a_cookie_returns_401(client: APIClient) -> None:
    response = client.post(reverse("auth-refresh"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "refresh_token_missing"


def test_refresh_with_a_broken_cookie_clears_it(client: APIClient) -> None:
    client.cookies[settings.AUTH_COOKIE_REFRESH_NAME] = "not-a-token"

    response = client.post(reverse("auth-refresh"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "refresh_token_invalid"
    assert response.cookies[settings.AUTH_COOKIE_REFRESH_NAME].value == ""


def test_logout_clears_both_cookies(client: APIClient) -> None:
    _login(client)

    response = client.post(reverse("auth-logout"))

    assert response.status_code == 204
    assert response.cookies[settings.AUTH_COOKIE_ACCESS_NAME].value == ""
    assert response.cookies[settings.AUTH_COOKIE_REFRESH_NAME].value == ""


def test_refresh_token_cannot_be_reused_after_logout(client: APIClient) -> None:
    _login(client)
    stolen = client.cookies[settings.AUTH_COOKIE_REFRESH_NAME].value

    client.post(reverse("auth-logout"))

    client.cookies[settings.AUTH_COOKIE_REFRESH_NAME] = stolen
    assert client.post(reverse("auth-refresh")).status_code == 401


def test_logout_works_even_without_a_session(client: APIClient) -> None:
    assert client.post(reverse("auth-logout")).status_code == 204


def test_access_cookie_authenticates_requests(client: APIClient) -> None:
    user = _login(client)

    response = client.get(reverse("auth-me"))

    assert response.status_code == 200
    assert response.json()["username"] == user.username


def test_garbage_access_cookie_is_rejected(client: APIClient) -> None:
    client.cookies[settings.AUTH_COOKIE_ACCESS_NAME] = "not-a-token"

    assert client.get(reverse("auth-me")).status_code == 401
