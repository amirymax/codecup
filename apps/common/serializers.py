"""Сериализаторы-обёртки для ответов, которые не являются одним объектом.

Нужны не ради самих ответов, а ради схемы OpenAPI: из неё генерируются
типы для фронтенда, и «голый» dict превратился бы в бесполезный any.
"""

from __future__ import annotations

from rest_framework import serializers


class NavigationSerializer(serializers.Serializer):
    """Счётчик «3 / 36» и стрелки на экране проверки."""

    position = serializers.IntegerField(allow_null=True)
    total = serializers.IntegerField()
    previous_id = serializers.IntegerField(allow_null=True)
    next_id = serializers.IntegerField(allow_null=True)
