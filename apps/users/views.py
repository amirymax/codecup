from __future__ import annotations

from contextlib import suppress

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.exceptions import DomainError

from .cookies import clear_auth_cookies, issue_tokens, set_auth_cookies
from .models import AuthTokenStatus, TelegramAuthToken
from .serializers import (
    AuthExchangeRequestSerializer,
    AuthStartResponseSerializer,
    AuthStatusResponseSerializer,
    UserSerializer,
)


class TelegramAuthStartView(APIView):
    """Шаг 1: выдать одноразовый код и ссылку на бота."""

    authentication_classes = []
    permission_classes = []
    throttle_scope = "auth_start"

    @extend_schema(
        summary="Начать вход через Telegram",
        request=None,
        responses={200: AuthStartResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        if not settings.TELEGRAM_BOT_USERNAME:
            raise DomainError(
                "Вход через Telegram пока не настроен.",
                code="telegram_not_configured",
            )

        token, client_secret = TelegramAuthToken.issue(
            ip=_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        payload = {
            "nonce": token.nonce,
            "client_secret": client_secret,
            "deep_link": f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token.nonce}",
            "expires_at": token.expires_at,
            "expires_in": settings.TELEGRAM_AUTH_TOKEN_TTL,
        }
        return Response(AuthStartResponseSerializer(payload).data)


class TelegramAuthStatusView(APIView):
    """Шаг 2: фронтенд опрашивает этот эндпоинт, пока ждёт подтверждения."""

    authentication_classes = []
    permission_classes = []
    throttle_scope = "auth_status"

    @extend_schema(
        summary="Статус попытки входа",
        responses={200: AuthStatusResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        nonce = request.query_params.get("nonce", "")
        token = TelegramAuthToken.objects.filter(nonce=nonce).first()
        # Неизвестный код неотличим от просроченного: так наружу не утекает
        # информация о том, какие коды существуют.
        current = token.current_status if token else AuthTokenStatus.EXPIRED
        return Response({"status": current})


class TelegramAuthExchangeView(APIView):
    """Шаг 3: обменять подтверждённый код на сессию в куках."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Обменять код на сессию",
        request=AuthExchangeRequestSerializer,
        responses={200: UserSerializer},
    )
    def post(self, request: Request) -> Response:
        payload = AuthExchangeRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        token = (
            # of=("self",) обязательно: user допускает NULL, поэтому
            # select_related даёт LEFT JOIN, а его Postgres блокировать не умеет.
            TelegramAuthToken.objects.select_for_update(of=("self",))
            .filter(nonce=data["nonce"])
            .select_related("user")
            .first()
        )

        # Один и тот же ответ на «нет такого кода», «чужой секрет» и «просрочен»:
        # подбирать nonce вслепую бессмысленно.
        if (
            token is None
            or token.status != AuthTokenStatus.CONFIRMED
            or token.is_expired
            or not token.matches_secret(data["client_secret"])
        ):
            raise DomainError(
                "Ссылка для входа недействительна или устарела.",
                code="auth_token_invalid",
            )

        token.consume()
        access, refresh = issue_tokens(token.user)

        response = Response(UserSerializer(token.user).data)
        return set_auth_cookies(response, access, refresh)


class AuthRefreshView(APIView):
    """Обновление access-токена по refresh-куке."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(summary="Обновить сессию", request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH_NAME)
        if not raw_refresh:
            return self._session_expired("refresh_token_missing", "Сессия не найдена.")

        try:
            refresh = RefreshToken(raw_refresh)
            # Access выпускаем до ротации: после неё jti уже другой.
            access = str(refresh.access_token)
            rotated = _rotate(refresh)
        except TokenError:
            return self._session_expired("refresh_token_invalid", "Сессия истекла.")

        return set_auth_cookies(Response(status=status.HTTP_204_NO_CONTENT), access, rotated)

    @staticmethod
    def _session_expired(code: str, message: str) -> Response:
        """Отвечает 401 и заодно убирает мёртвые куки из браузера."""
        response = Response(
            {"error": {"code": code, "message": message}},
            status=status.HTTP_401_UNAUTHORIZED,
        )
        return clear_auth_cookies(response)


class AuthLogoutView(APIView):
    """Выход: чистим куки и гасим refresh-токен."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(summary="Выйти", request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH_NAME)
        if raw_refresh:
            # Уже недействителен — выход всё равно должен получиться.
            with suppress(TokenError):
                RefreshToken(raw_refresh).blacklist()

        return clear_auth_cookies(Response(status=status.HTTP_204_NO_CONTENT))


class CurrentUserView(APIView):
    """Текущий пользователь по куке."""

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Текущий пользователь", responses={200: UserSerializer})
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)


def _rotate(refresh: RefreshToken) -> str:
    """Ротация refresh-токена, если она включена в настройках."""
    if not settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):
        return str(refresh)

    if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION"):
        # blacklist() появляется только при подключённом token_blacklist.
        with suppress(AttributeError):
            refresh.blacklist()

    refresh.set_jti()
    refresh.set_exp()
    refresh.set_iat()
    return str(refresh)


def _client_ip(request: Request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
