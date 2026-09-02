"""Разбор входящего запроса за прокси."""

from __future__ import annotations

from rest_framework.request import Request


def client_ip(request: Request) -> str | None:
    """Адрес клиента, а не nginx.

    Заголовок ставит наш собственный прокси, поэтому первому значению в
    цепочке можно верить.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
