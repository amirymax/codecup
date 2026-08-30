"""Поведение модели токена и заведение пользователей из Telegram."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.users.models import AuthTokenStatus, TelegramAuthToken, User

from .factories import UserFactory, telegram_profile

pytestmark = pytest.mark.django_db


def test_issue_stores_only_a_hash_of_the_client_secret() -> None:
    token, secret = TelegramAuthToken.issue()

    assert secret not in token.client_secret_hash
    assert token.matches_secret(secret)
    assert not token.matches_secret(secret + "x")


def test_expiry_is_derived_not_stored() -> None:
    """Просроченный токен не должен «зависать» в pending."""
    token, _ = TelegramAuthToken.issue()
    token.expires_at = timezone.now() - timedelta(seconds=1)

    assert token.status == AuthTokenStatus.PENDING
    assert token.current_status == AuthTokenStatus.EXPIRED
    assert not token.is_confirmable


def test_confirmed_token_is_no_longer_confirmable() -> None:
    token, _ = TelegramAuthToken.issue()
    token.confirm(UserFactory())

    assert not token.is_confirmable


def test_user_created_from_telegram_has_no_usable_password() -> None:
    user, created = User.objects.get_or_create_from_telegram(telegram_profile())

    assert created
    assert not user.has_usable_password()
    assert user.telegram_id == 555_001


def test_username_falls_back_when_telegram_has_none() -> None:
    user, _ = User.objects.get_or_create_from_telegram(telegram_profile(username=None))

    assert user.username == "user_555001"


def test_username_collision_gets_a_suffix() -> None:
    UserFactory(username="sarah_dev")

    user, _ = User.objects.get_or_create_from_telegram(telegram_profile())

    assert user.username != "sarah_dev"
    assert user.username.startswith("sarah_dev_")


def test_profile_is_refreshed_on_every_login() -> None:
    User.objects.get_or_create_from_telegram(telegram_profile())

    user, created = User.objects.get_or_create_from_telegram(
        telegram_profile(first_name="Сара", last_name="Новая")
    )

    assert not created
    assert user.last_name == "Новая"
    assert User.objects.count() == 1


def test_is_admin_follows_is_staff() -> None:
    assert not UserFactory().is_admin
    assert UserFactory(is_staff=True).is_admin
