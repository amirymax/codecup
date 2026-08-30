from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Contest, ContestState, NotifySubscription
from .serializers import (
    AdminContestSerializer,
    ContestDetailSerializer,
    ContestListSerializer,
    FeaturedContestSerializer,
)


class ContestListView(generics.ListAPIView):
    """Публичный список опубликованных контестов."""

    serializer_class = ContestListSerializer
    permission_classes = []

    @extend_schema(
        summary="Список контестов",
        parameters=[
            OpenApiParameter(
                "state",
                str,
                description="Фильтр: live или ended. По умолчанию — все опубликованные.",
                enum=[ContestState.LIVE, ContestState.ENDED],
            )
        ],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Contest.objects.by_state(self.request.query_params.get("state")).order_by(
            "-is_featured", "-deadline"
        )


class FeaturedContestView(APIView):
    """Контест для главной страницы.

    Всегда отдаёт объект с ключом ``contest``, который равен ``null``, если
    активного контеста нет: это состояние «Сейчас нет активного контеста».
    Обёртка, а не голый ``null``, по двум причинам — DRF рендерит None пустым
    телом без Content-Type, и в этот же ответ потом добавятся общие счётчики
    главной, не ломая формат.
    """

    permission_classes = []

    @extend_schema(summary="Контест на главной", responses={200: FeaturedContestSerializer})
    def get(self, request: Request) -> Response:
        contest = (
            Contest.objects.live().filter(is_featured=True).first()
            or Contest.objects.live().order_by("deadline").first()
        )
        payload = {"contest": ContestDetailSerializer(contest).data if contest else None}
        return Response(payload)


class ContestDetailView(generics.RetrieveAPIView):
    """Страница контеста."""

    serializer_class = ContestDetailSerializer
    permission_classes = []
    lookup_field = "slug"

    @extend_schema(summary="Контест")
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Черновики и архив наружу не показываем даже по прямой ссылке.
        return Contest.objects.public()


class NotifySubscribeView(APIView):
    """Кнопка «Уведомить меня», когда активного контеста нет."""

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Подписаться на анонсы", request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        NotifySubscription.objects.get_or_create(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Отписаться от анонсов", responses={204: None})
    def delete(self, request: Request) -> Response:
        NotifySubscription.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminContestListCreateView(generics.ListCreateAPIView):
    """Список и создание контестов в админке."""

    serializer_class = AdminContestSerializer
    permission_classes = [IsAdminUser]
    queryset = Contest.objects.all()

    def perform_create(self, serializer) -> None:
        serializer.save(created_by=self.request.user)


class AdminContestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, правка и удаление контеста."""

    serializer_class = AdminContestSerializer
    permission_classes = [IsAdminUser]
    queryset = Contest.objects.all()


class AdminContestPublishView(APIView):
    """Публикация черновика."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Опубликовать контест",
        request=None,
        responses={200: AdminContestSerializer},
    )
    def post(self, request: Request, pk: int) -> Response:
        contest = get_object_or_404(Contest, pk=pk)
        contest.publish()
        return Response(AdminContestSerializer(contest).data)
