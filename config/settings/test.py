"""Настройки для pytest: те же, что локально, но с быстрым хешером паролей."""

from .local import *  # noqa: F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
