from __future__ import annotations

import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import handle_update

logger = logging.getLogger(__name__)

SECRET_HEADER = "HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN"


class TelegramWebhookView(APIView):
    """Приёмник апдейтов Telegram.

    Защита двойная: секрет в пути и секрет в заголовке
    ``X-Telegram-Bot-Api-Secret-Token``, который Telegram шлёт сам.
    """

    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def post(self, request: Request, secret: str) -> Response:
        if not self._secret_is_valid(request, secret):
            logger.warning("Вебхук отклонён: неверный секрет")
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            handle_update(request.data)
        except Exception:
            # Ненулевой код заставил бы Telegram повторять апдейт по кругу,
            # поэтому ошибку логируем, а отвечаем всё равно 200.
            logger.exception("Ошибка обработки апдейта Telegram")

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def _secret_is_valid(request: Request, secret: str) -> bool:
        from django.utils.crypto import constant_time_compare

        expected = settings.TELEGRAM_WEBHOOK_SECRET
        if not expected:
            logger.error("TELEGRAM_WEBHOOK_SECRET не задан — вебхук отключён")
            return False

        header = request.META.get(SECRET_HEADER, "")
        return constant_time_compare(secret, expected) and constant_time_compare(header, expected)
