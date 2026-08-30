from __future__ import annotations

from typing import Any

import factory

from apps.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    telegram_id = factory.Sequence(lambda n: 100_000 + n)
    username = factory.Sequence(lambda n: f"user_{n}")
    telegram_username = factory.LazyAttribute(lambda o: o.username)
    first_name = "Тест"


class AdminFactory(UserFactory):
    is_staff = True


def telegram_profile(**overrides: Any) -> dict[str, Any]:
    """Объект User из Bot API."""
    return {
        "id": 555_001,
        "is_bot": False,
        "first_name": "Сара",
        "last_name": "Разработчикова",
        "username": "sarah_dev",
        "language_code": "ru",
    } | overrides


def start_update(nonce: str = "", chat_id: int = 555_001, **overrides: Any) -> dict[str, Any]:
    """Апдейт с командой /start (с полезной нагрузкой из deep link)."""
    text = f"/start {nonce}".strip()
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1_700_000_000,
            "chat": {"id": chat_id, "type": "private"},
            "from": telegram_profile(id=chat_id),
            "text": text,
        },
    } | overrides


def callback_update(
    action: str,
    nonce: str,
    chat_id: int = 555_001,
    **profile_overrides: Any,
) -> dict[str, Any]:
    """Апдейт с нажатием инлайн-кнопки."""
    return {
        "update_id": 2,
        "callback_query": {
            "id": "cb-1",
            "from": telegram_profile(id=chat_id, **profile_overrides),
            "data": f"{action}:{nonce}",
            "message": {
                "message_id": 11,
                "date": 1_700_000_000,
                "chat": {"id": chat_id, "type": "private"},
            },
        },
    }
