"""Запись событий и сводка по ним."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.request import Request

from apps.common.request import client_ip

from .models import PAGEVIEW, Event, visitor_hash

# Сколько строк показывать в таблице страниц: дальше идёт длинный хвост.
TOP_PAGES = 20
MAX_USER_AGENT = 400


def record(request: Request, name: str, path: str) -> Event:
    user = request.user if request.user.is_authenticated else None
    return Event.objects.create(
        name=name,
        path=path,
        visitor=visitor_hash(
            client_ip(request),
            request.META.get("HTTP_USER_AGENT", "")[:MAX_USER_AGENT],
        ),
        user=user,
    )


def summary(days: int) -> dict:
    """Сводка за последние `days` суток."""
    since = timezone.now() - timedelta(days=days)
    events = Event.objects.filter(created_at__gte=since)
    views = events.pageviews()

    return {
        "days": days,
        "views": views.count(),
        "visitors": views.visitors(),
        # Сколько из них вошли: показывает, доходит ли трафик до регистрации.
        "logged_in": views.filter(user__isnull=False).values("user").distinct().count(),
        "daily": _daily(views),
        "pages": _pages(views),
        "events": _events(events),
    }


def _daily(views) -> list[dict]:
    rows = (
        views.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(views=Count("id"), visitors=Count("visitor", distinct=True))
        .order_by("day")
    )
    return list(rows)


def _pages(views) -> list[dict]:
    rows = (
        views.values("path")
        .annotate(views=Count("id"), visitors=Count("visitor", distinct=True))
        .order_by("-views")[:TOP_PAGES]
    )
    return list(rows)


def _events(events) -> list[dict]:
    """Всё, кроме просмотров: клики по кнопкам и прочие действия."""
    rows = (
        events.exclude(name=PAGEVIEW)
        .values("name")
        .annotate(count=Count("id"), visitors=Count("visitor", distinct=True))
        .order_by("-count")
    )
    return list(rows)
