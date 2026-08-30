from __future__ import annotations

from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User


class AdminStatsSerializer(serializers.Serializer):
    """Четыре плитки на админ-панели."""

    total_users = serializers.IntegerField()
    active_contests = serializers.IntegerField()
    submissions = serializers.IntegerField()
    pending_review = serializers.IntegerField()


class AdminUserSerializer(serializers.ModelSerializer):
    submissions_count = serializers.IntegerField(read_only=True)
    wins_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "telegram_id",
            "telegram_username",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "submissions_count",
            "wins_count",
            "created_at",
        ]
        read_only_fields = fields


class AdminStatsView(APIView):
    """Счётчики для админ-панели."""

    permission_classes = [IsAdminUser]

    @extend_schema(summary="Счётчики админ-панели", responses={200: AdminStatsSerializer})
    def get(self, request: Request) -> Response:
        from apps.contests.models import Contest
        from apps.submissions.models import Submission

        payload = {
            "total_users": User.objects.filter(is_active=True).count(),
            "active_contests": Contest.objects.live().count(),
            "submissions": Submission.objects.counted().count(),
            "pending_review": Submission.objects.pending_review().count(),
        }
        return Response(AdminStatsSerializer(payload).data)


class AdminUserListView(generics.ListAPIView):
    """Список пользователей."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Пользователи",
        parameters=[
            OpenApiParameter("search", str, description="Поиск по логину, имени или Telegram ID"),
            OpenApiParameter("is_staff", bool, description="Только администраторы"),
        ],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        from apps.submissions.models import SubmissionStatus

        counted = ~Q(submissions__status=SubmissionStatus.DRAFT)
        queryset = User.objects.annotate(
            submissions_count=Count("submissions", filter=counted, distinct=True),
            wins_count=Count("submissions", filter=Q(submissions__is_winner=True), distinct=True),
        )

        params = self.request.query_params
        if search := params.get("search"):
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(telegram_username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(telegram_id__icontains=search)
            )
        if params.get("is_staff") in {"true", "1"}:
            queryset = queryset.filter(is_staff=True)

        return queryset.order_by("-created_at")
