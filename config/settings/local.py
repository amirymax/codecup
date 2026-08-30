"""Локальная разработка: Postgres в Docker, Django — на хосте."""

from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", ".ngrok-free.app", ".trycloudflare.com"]

# В разработке куки ходят по http, поэтому Secure выключен.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)
