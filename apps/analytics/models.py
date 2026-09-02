"""Посещаемость сайта.

Посетителей не идентифицируем. Вместо IP-адреса храним необратимый хеш от
IP и User-Agent: восстановить из него адрес нельзя, а посчитать уникальных
посетителей — можно. Поэтому баннер о cookie не нужен: мы их не ставим.
"""

from __future__ import annotations

import hashlib

from django.conf import settings
from django.db import models

# Длина пути ограничена: адреса длиннее — это почти всегда мусор от ботов.
MAX_PATH_LENGTH = 200
MAX_EVENT_NAME_LENGTH = 40

PAGEVIEW = "pageview"


def visitor_hash(ip: str | None, user_agent: str) -> str:
    """Стабильный анонимный отпечаток посетителя.

    Ключ — SECRET_KEY, поэтому хеш нельзя подобрать перебором адресов со
    стороны. Соль не меняется по дням намеренно: иначе один и тот же человек
    считался бы новым посетителем каждые сутки, и «уникальные за месяц»
    ничего бы не значили.
    """
    material = f"{ip or ''}|{user_agent}".encode()
    key = settings.SECRET_KEY.encode()[:32]  # blake2s не принимает ключ длиннее
    return hashlib.blake2s(material, key=key, digest_size=16).hexdigest()


class EventQuerySet(models.QuerySet):
    def pageviews(self):
        return self.filter(name=PAGEVIEW)

    def visitors(self) -> int:
        return self.values("visitor").distinct().count()


class Event(models.Model):
    """Одно событие: просмотр страницы или клик по кнопке."""

    name = models.CharField("событие", max_length=MAX_EVENT_NAME_LENGTH)
    path = models.CharField("страница", max_length=MAX_PATH_LENGTH, blank=True)
    visitor = models.CharField("посетитель", max_length=32)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField("когда", auto_now_add=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = "событие"
        verbose_name_plural = "события"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
            models.Index(fields=["path", "created_at"]),
            models.Index(fields=["visitor"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} {self.path}"
