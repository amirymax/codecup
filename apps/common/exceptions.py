"""Единый формат ошибок API.

Каждая ошибка выглядит так:

    {"error": {"code": "contest_closed", "message": "...", "details": {...}}}

Фронтенду достаточно посмотреть на ``code``, чтобы выбрать нужный экран,
а ``message`` уже на русском и пригоден для показа пользователю.
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(APIException):
    """Нарушение бизнес-правила: у него есть стабильный машинный код."""

    status_code = 409
    default_code = "domain_error"
    default_detail = "Действие сейчас недоступно."

    def __init__(self, detail: str | None = None, code: str | None = None, **details: Any) -> None:
        super().__init__(detail=detail, code=code)
        self.details = details


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    # DRF подменяет эти исключения у себя внутри, а нам достаётся исходное —
    # без такой же подмены код ошибки выродился бы в безликое "error".
    # Аргументы Http404 не переносим: Django кладёт туда английское
    # "No Contest matches the given query" с именем модели. Берём вместо
    # этого переведённое сообщение DRF.
    if isinstance(exc, Http404):
        exc = NotFound()
        response.data = {"detail": exc.detail}
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied()
        response.data = {"detail": exc.detail}

    code = getattr(exc, "detail", None)
    code = getattr(code, "code", None) or getattr(exc, "default_code", "error")

    payload: dict[str, Any] = {"code": code, "message": _message_from(response.data)}
    details = _details_from(response.data) | getattr(exc, "details", {})
    if details:
        payload["details"] = details

    response.data = {"error": payload}
    return response


def _message_from(data: Any) -> str:
    """Достаёт одну человекочитаемую строку из тела ответа DRF."""
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail is not None:
            return str(detail)
        for value in data.values():
            return _message_from(value)
    if isinstance(data, list) and data:
        return _message_from(data[0])
    return str(data)


def _details_from(data: Any) -> dict[str, Any]:
    """Ошибки валидации по полям — всё, кроме служебного ``detail``."""
    if isinstance(data, dict) and "detail" not in data:
        return dict(data)
    return {}
