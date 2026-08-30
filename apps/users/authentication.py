from __future__ import annotations

from django.conf import settings
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Берёт access-токен из httpOnly-куки, а не из заголовка Authorization.

    Заголовок тоже поддерживается — так удобнее дёргать API из curl и из
    тестов, — но фронтенд им не пользуется.
    """

    def authenticate(self, request: Request):
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS_NAME)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
