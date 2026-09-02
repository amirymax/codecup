from __future__ import annotations

import re

from rest_framework import serializers

from .models import MAX_EVENT_NAME_LENGTH, MAX_PATH_LENGTH, PAGEVIEW

# Имена событий задаём мы сами в коде фронтенда, поэтому набор символов узкий.
EVENT_NAME = re.compile(r"^[a-z0-9_]+$")


class TrackEventSerializer(serializers.Serializer):
    """То, что присылает браузер."""

    name = serializers.CharField(max_length=MAX_EVENT_NAME_LENGTH, default=PAGEVIEW)
    path = serializers.CharField(max_length=MAX_PATH_LENGTH, allow_blank=True, default="")

    def validate_name(self, value: str) -> str:
        if not EVENT_NAME.match(value):
            raise serializers.ValidationError("Недопустимое имя события.")
        return value

    def validate_path(self, value: str) -> str:
        # Query-строку отбрасываем: в ней оказываются персональные данные,
        # а для статистики по страницам она всё равно не нужна.
        return value.split("?")[0][:MAX_PATH_LENGTH]


class DailyPointSerializer(serializers.Serializer):
    day = serializers.DateField()
    views = serializers.IntegerField()
    visitors = serializers.IntegerField()


class PageStatSerializer(serializers.Serializer):
    path = serializers.CharField()
    views = serializers.IntegerField()
    visitors = serializers.IntegerField()


class EventStatSerializer(serializers.Serializer):
    name = serializers.CharField()
    count = serializers.IntegerField()
    visitors = serializers.IntegerField()


class AnalyticsSummarySerializer(serializers.Serializer):
    """Сводка для админки."""

    days = serializers.IntegerField()
    views = serializers.IntegerField()
    visitors = serializers.IntegerField()
    logged_in = serializers.IntegerField()
    daily = DailyPointSerializer(many=True)
    pages = PageStatSerializer(many=True)
    events = EventStatSerializer(many=True)
