"""Выдача JWT через httpOnly-куки.

Токены не отдаются в теле ответа и недоступны из JavaScript, поэтому
внедрённый на страницу скрипт не сможет их украсть. Refresh-кука живёт на
узком пути ``/api/auth/``, чтобы не уходить с каждым обычным запросом.
"""

from __future__ import annotations

from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def issue_tokens(user: User) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_auth_cookies(response: Response, access: str, refresh: str | None = None) -> Response:
    response.set_cookie(
        settings.AUTH_COOKIE_ACCESS_NAME,
        access,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/",
    )
    if refresh is not None:
        response.set_cookie(
            settings.AUTH_COOKIE_REFRESH_NAME,
            refresh,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            domain=settings.AUTH_COOKIE_DOMAIN,
            path=settings.AUTH_COOKIE_REFRESH_PATH,
        )
    return response


def clear_auth_cookies(response: Response) -> Response:
    response.delete_cookie(
        settings.AUTH_COOKIE_ACCESS_NAME,
        path="/",
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_COOKIE_REFRESH_NAME,
        path=settings.AUTH_COOKIE_REFRESH_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return response
