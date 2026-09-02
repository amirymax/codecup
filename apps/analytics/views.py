from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AnalyticsSummarySerializer, TrackEventSerializer
from .services import record, summary

# Сколько суток показывать по умолчанию и максимум.
DEFAULT_DAYS = 30
MAX_DAYS = 365


class TrackEventView(APIView):
    """Приём событий из браузера.

    Открыт для всех: посещения гостей — это большая часть трафика, и ради
    них статистика и нужна. От перебора защищает троттлинг.
    """

    permission_classes = []
    throttle_scope = "analytics"

    @extend_schema(
        summary="Записать событие",
        request=TrackEventSerializer,
        responses={204: None},
    )
    def post(self, request: Request) -> Response:
        serializer = TrackEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record(request, **serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminAnalyticsView(APIView):
    """Сводка посещаемости для админки."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Посещаемость",
        parameters=[
            OpenApiParameter(
                "days",
                int,
                description=f"За сколько суток, 1–{MAX_DAYS}. По умолчанию {DEFAULT_DAYS}.",
            )
        ],
        responses={200: AnalyticsSummarySerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(AnalyticsSummarySerializer(summary(_days(request))).data)


def _days(request: Request) -> int:
    """Окно в сутках. Мусор в параметре — не повод отвечать ошибкой."""
    try:
        days = int(request.query_params.get("days", DEFAULT_DAYS))
    except (TypeError, ValueError):
        return DEFAULT_DAYS
    return max(1, min(days, MAX_DAYS))
