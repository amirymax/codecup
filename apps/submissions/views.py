from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import DomainError
from apps.contests.models import Contest

from .models import Submission, SubmissionStatus
from .serializers import (
    AdminSubmissionDetailSerializer,
    AdminSubmissionListSerializer,
    MySubmissionSerializer,
    ProfileSubmissionSerializer,
)


def _open_contest(slug: str) -> Contest:
    """Контест, в который сейчас можно отправлять решения."""
    contest = get_object_or_404(Contest.objects.public(), slug=slug)
    if not contest.accepts_submissions:
        raise DomainError(
            "Приём заявок на этот контест закрыт.",
            code="contest_closed",
            slug=contest.slug,
        )
    return contest


class MySubmissionView(APIView):
    """Своя заявка на контест: одна на человека, правится до дедлайна."""

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Моя заявка", responses={200: MySubmissionSerializer})
    def get(self, request: Request, slug: str) -> Response:
        contest = get_object_or_404(Contest.objects.public(), slug=slug)
        submission = Submission.objects.filter(contest=contest, user=request.user).first()
        if submission is None:
            return Response({"submission": None})
        return Response({"submission": MySubmissionSerializer(submission).data})

    @extend_schema(
        summary="Сохранить черновик заявки",
        request=MySubmissionSerializer,
        responses={200: MySubmissionSerializer},
    )
    def put(self, request: Request, slug: str) -> Response:
        contest = _open_contest(slug)
        instance = Submission.objects.filter(contest=contest, user=request.user).first()

        serializer = MySubmissionSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(contest=contest, user=request.user)

        code = status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        return Response({"submission": MySubmissionSerializer(submission).data}, status=code)


class SubmitSolutionView(APIView):
    """Перевод заявки из черновика в отправленные."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Отправить решение",
        request=MySubmissionSerializer,
        responses={200: MySubmissionSerializer},
    )
    def post(self, request: Request, slug: str) -> Response:
        contest = _open_contest(slug)
        instance = Submission.objects.filter(contest=contest, user=request.user).first()

        # require_complete включает обязательность ссылок: при отправке
        # неполная заявка недопустима, в отличие от черновика.
        serializer = MySubmissionSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"require_complete": True},
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(contest=contest, user=request.user)
        submission.mark_submitted()

        return Response({"submission": MySubmissionSerializer(submission).data})


class MySubmissionListView(generics.ListAPIView):
    """История заявок для своего профиля."""

    serializer_class = ProfileSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user).select_related("contest")


class AdminSubmissionListView(generics.ListAPIView):
    """Список заявок в админке."""

    serializer_class = AdminSubmissionListSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Заявки",
        parameters=[
            OpenApiParameter("contest", str, description="Слаг контеста"),
            OpenApiParameter(
                "status",
                str,
                description="Фильтр статуса; winner — только победители",
                enum=[*SubmissionStatus.values, "winner"],
            ),
            OpenApiParameter("search", str, description="Поиск по участнику или репозиторию"),
        ],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Submission.objects.review_queue().select_related("contest", "user")
        params = self.request.query_params

        if contest_slug := params.get("contest"):
            queryset = queryset.filter(contest__slug=contest_slug)

        if requested := params.get("status"):
            if requested == "winner":
                queryset = queryset.filter(is_winner=True)
            elif requested in SubmissionStatus.values:
                queryset = queryset.filter(status=requested)

        if search := params.get("search"):
            queryset = queryset.filter(
                Q(user__username__icontains=search)
                | Q(user__telegram_username__icontains=search)
                | Q(github_url__icontains=search)
            )

        return queryset


class AdminSubmissionDetailView(APIView):
    """Экран проверки заявки."""

    permission_classes = [IsAdminUser]

    @extend_schema(summary="Заявка", responses={200: AdminSubmissionDetailSerializer})
    def get(self, request: Request, pk: int) -> Response:
        submission = get_object_or_404(Submission.objects.select_related("contest", "user"), pk=pk)
        return Response(self._payload(submission))

    @extend_schema(
        summary="Сохранить проверку",
        request=AdminSubmissionDetailSerializer,
        responses={200: AdminSubmissionDetailSerializer},
    )
    def patch(self, request: Request, pk: int) -> Response:
        submission = get_object_or_404(Submission.objects.select_related("contest", "user"), pk=pk)

        serializer = AdminSubmissionDetailSerializer(submission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        submission.apply_review(
            reviewer=request.user,
            score=data.get("score"),
            notes=data.get("reviewer_notes"),
            is_winner=data.get("is_winner"),
        )
        return Response(self._payload(submission))

    def _payload(self, submission: Submission) -> dict:
        """Заявка вместе с навигацией «предыдущая / следующая».

        Экран проверки показывает «3 / 36» и стрелки, поэтому позиция и
        соседи считаются на сервере — там же, где задан порядок очереди.
        """
        queue = list(
            Submission.objects.review_queue()
            .filter(contest=submission.contest)
            .values_list("id", flat=True)
        )
        try:
            index = queue.index(submission.id)
        except ValueError:
            index = None

        navigation = {
            "position": None if index is None else index + 1,
            "total": len(queue),
            "previous_id": queue[index - 1] if index else None,
            "next_id": queue[index + 1] if index is not None and index + 1 < len(queue) else None,
        }
        return {
            "submission": AdminSubmissionDetailSerializer(submission).data,
            "navigation": navigation,
        }


class PublicProfileView(APIView):
    """Публичный профиль участника.

    Живёт в этом приложении, а не в users: почти всё содержимое — история
    заявок, и так users не приходится зависеть от submissions.
    """

    permission_classes = []

    @extend_schema(summary="Профиль участника")
    def get(self, request: Request, username: str) -> Response:
        from apps.users.models import User
        from apps.users.serializers import UserSerializer

        user = get_object_or_404(User.objects.filter(is_active=True), username=username)
        submissions = Submission.objects.filter(user=user).counted().select_related("contest")

        return Response(
            {
                "user": UserSerializer(user).data,
                "submissions_count": submissions.count(),
                "wins_count": submissions.filter(is_winner=True).count(),
                "submissions": ProfileSubmissionSerializer(submissions, many=True).data,
            }
        )
