from __future__ import annotations

from typing import Any

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import transaction
from django.utils.crypto import get_random_string


class UserManager(DjangoUserManager):
    """Пользователи заводятся из Telegram, а не через форму регистрации."""

    @transaction.atomic
    def get_or_create_from_telegram(self, profile: dict[str, Any]) -> tuple[Any, bool]:
        """Находит пользователя по telegram_id или создаёт нового.

        ``profile`` — объект User из Telegram Bot API. Профиль обновляется при
        каждом входе: человек мог сменить имя или @username.
        """
        telegram_id = int(profile["id"])
        fields = {
            "telegram_username": profile.get("username") or "",
            "first_name": (profile.get("first_name") or "")[:150],
            "last_name": (profile.get("last_name") or "")[:150],
            "language_code": (profile.get("language_code") or "ru")[:5],
        }

        user = self.filter(telegram_id=telegram_id).first()
        if user is not None:
            for field, value in fields.items():
                setattr(user, field, value)
            user.save(update_fields=[*fields, "updated_at"])
            return user, False

        user = self.model(
            telegram_id=telegram_id,
            username=self._unique_username(profile),
            **fields,
        )
        # Пароля у аккаунта нет и быть не может: вход только через Telegram.
        user.set_unusable_password()
        user.save()
        return user, True

    def _unique_username(self, profile: dict[str, Any]) -> str:
        """Подбирает свободный username: @telegram, иначе user_<id>."""
        base = (profile.get("username") or f"user_{profile['id']}")[:140]
        candidate = base
        while self.filter(username__iexact=candidate).exists():
            candidate = f"{base}_{get_random_string(4).lower()}"
        return candidate
