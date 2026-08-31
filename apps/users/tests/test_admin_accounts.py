"""Создание администраторов: createsuperuser и make_admin."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.users.models import User

from .factories import UserFactory

pytestmark = pytest.mark.django_db


def test_createsuperuser_asks_for_the_telegram_id() -> None:
    """telegram_id обязателен и уникален, поэтому команда обязана его спросить.

    Без этого createsuperuser падал на вставке с NOT NULL constraint.
    """
    assert "telegram_id" in User.REQUIRED_FIELDS


def test_createsuperuser_succeeds_with_a_telegram_id(settings) -> None:
    settings.DJANGO_SUPERUSER_PASSWORD = "irrelevant"

    call_command(
        "createsuperuser",
        interactive=False,
        username="root_admin",
        telegram_id=555_900_001,
    )

    user = User.objects.get(username="root_admin")
    assert user.telegram_id == 555_900_001
    assert user.is_staff and user.is_superuser


def test_make_admin_promotes_by_telegram_username() -> None:
    user = UserFactory(telegram_username="AmiriCode", is_staff=False)

    call_command("make_admin", telegram_username="AmiriCode")

    user.refresh_from_db()
    assert user.is_staff and user.is_superuser


def test_make_admin_ignores_the_at_sign_and_case() -> None:
    user = UserFactory(telegram_username="AmiriCode", is_staff=False)

    call_command("make_admin", telegram_username="@amiricode")

    user.refresh_from_db()
    assert user.is_staff


def test_make_admin_promotes_by_telegram_id() -> None:
    user = UserFactory(telegram_id=777_123, is_staff=False)

    call_command("make_admin", telegram_id=777_123)

    user.refresh_from_db()
    assert user.is_staff


def test_make_admin_can_revoke() -> None:
    user = UserFactory(telegram_username="ExAdmin", is_staff=True, is_superuser=True)

    call_command("make_admin", telegram_username="ExAdmin", revoke=True)

    user.refresh_from_db()
    assert not user.is_staff
    assert not user.is_superuser


def test_make_admin_explains_what_to_do_when_the_user_has_never_logged_in() -> None:
    with pytest.raises(CommandError, match="войдите"):
        call_command("make_admin", telegram_username="NeverSeen")
