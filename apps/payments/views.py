from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import DomainError
from apps.contests.models import Contest

from .models import EntryPayment, PaymentSettings, PaymentStatus
from .serializers import (
    AdminPaymentSerializer,
    ParticipationSerializer,
    PaymentDecisionSerializer,
    PaymentSettingsSerializer,
    ReceiptUploadSerializer,
)
from .services import get_or_create_payment, participation_state


def _open_contest(slug: str) -> Contest:
    contest = get_object_or_404(Contest.objects.public(), slug=slug)
    if not contest.accepts_submissions:
        raise DomainError("Приём заявок на этот контест закрыт.", code="contest_closed")
    return contest


def _paid_contest(slug: str) -> Contest:
    contest = _open_contest(slug)
    if not contest.is_paid:
        raise DomainError("Участие в этом контесте бесплатное.", code="contest_is_free")
    return contest


class ParticipationView(APIView):
    """Состояние участия: сумма, реквизиты и свой чек."""

    permission_classes = []

    @extend_schema(summary="Участие в контесте", responses={200: ParticipationSerializer})
    def get(self, request: Request, slug: str) -> Response:
        contest = get_object_or_404(Contest.objects.public(), slug=slug)
        state = participation_state(contest, request.user)
        return Response(ParticipationSerializer(state).data)


class UploadReceiptView(APIView):
    """Чек, загруженный прямо на сайте."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Загрузить чек",
        request=ReceiptUploadSerializer,
        responses={200: ParticipationSerializer},
    )
    def post(self, request: Request, slug: str) -> Response:
        contest = _paid_contest(slug)
        payment = get_or_create_payment(contest, request.user)

        if payment.is_accepted:
            raise DomainError("Взнос уже принят.", code="payment_already_accepted")

        if payment.is_under_review:
            raise DomainError(
                "Ваш чек уже на проверке. Дождитесь решения администратора.",
                code="payment_under_review",
            )

        upload = ReceiptUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        payment.attach_receipt(file=upload.validated_data["receipt"])

        _notify_admin(payment)
        return Response(ParticipationSerializer(participation_state(contest, request.user)).data)


class ReceiptViaBotView(APIView):
    """Участник обещает прислать чек в бот."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Отправить чек через бота",
        request=None,
        responses={200: ParticipationSerializer},
    )
    def post(self, request: Request, slug: str) -> Response:
        contest = _paid_contest(slug)
        payment = get_or_create_payment(contest, request.user)

        if payment.is_accepted:
            raise DomainError("Взнос уже принят.", code="payment_already_accepted")

        if payment.is_under_review:
            raise DomainError(
                "Ваш чек уже на проверке. Дождитесь решения администратора.",
                code="payment_under_review",
            )

        payment.wait_for_bot_receipt()

        state = participation_state(contest, request.user)
        data = ParticipationSerializer(state).data
        data["bot_url"] = _bot_url()
        return Response(data)


class AdminPaymentListView(generics.ListAPIView):
    """Очередь проверки взносов."""

    serializer_class = AdminPaymentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = EntryPayment.objects.select_related("contest", "user")
        requested = self.request.query_params.get("status")
        if requested in PaymentStatus.values:
            queryset = queryset.filter(status=requested)
        if contest := self.request.query_params.get("contest"):
            queryset = queryset.filter(contest__slug=contest)
        return queryset


class AdminPaymentDecisionView(APIView):
    """Принять или отклонить взнос."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Решение по взносу",
        request=PaymentDecisionSerializer,
        responses={200: AdminPaymentSerializer},
    )
    def post(self, request: Request, pk: int) -> Response:
        payment = get_object_or_404(EntryPayment.objects.select_related("contest", "user"), pk=pk)

        decision = PaymentDecisionSerializer(data=request.data)
        decision.is_valid(raise_exception=True)

        if decision.validated_data["decision"] == "accept":
            payment.accept(request.user)
        else:
            payment.reject(request.user, decision.validated_data.get("reason", ""))

        _notify_participant(payment)
        # Чек лежит в чате администратора с живыми кнопками: без этого его
        # можно принять второй раз уже из Telegram.
        _close_bot_message(payment)
        return Response(
            AdminPaymentSerializer(payment, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


def _bot_url() -> str:
    from django.conf import settings

    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}"


def _notify_admin(payment: EntryPayment) -> None:
    from apps.telegrambot.payments import forward_receipt_to_admin

    forward_receipt_to_admin(payment)


def _close_bot_message(payment: EntryPayment) -> None:
    from apps.telegrambot.payments import close_admin_decision_message

    close_admin_decision_message(payment)


def _notify_participant(payment: EntryPayment) -> None:
    from apps.telegrambot.payments import notify_participant

    notify_participant(payment)


class AdminPaymentRequisitesView(APIView):
    """Реквизиты для оплаты: посмотреть и изменить прямо из админки."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Реквизиты для оплаты",
        responses={200: PaymentSettingsSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(PaymentSettingsSerializer(PaymentSettings.load()).data)

    @extend_schema(
        summary="Изменить реквизиты для оплаты",
        request=PaymentSettingsSerializer,
        responses={200: PaymentSettingsSerializer},
    )
    def put(self, request: Request) -> Response:
        serializer = PaymentSettingsSerializer(PaymentSettings.load(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)
