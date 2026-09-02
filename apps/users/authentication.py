from __future__ import annotations

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Берёт access-токен из httpOnly-куки, а не из заголовка Authorization.

    Заголовок тоже поддерживается — так удобнее дёргать API из curl и из
    тестов, — но фронтенд им не пользуется.

    Испорченная или просроченная кука — это гость, а не ошибка. Браузер шлёт
    её на каждый запрос, в том числе к публичным адресам, и после истечения
    access-токена (15 минут) весь сайт отвечал бы 401 — а серверный рендер
    Next.js, который перекладывает куки в API, падал бы на каждой странице.
    Защищённые адреса при этом остаются защищёнными: без пользователя
    IsAuthenticated ответит тем же 401.
    """

    def authenticate(self, request: Request):
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS_NAME)
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except AuthenticationFailed:
            return None
