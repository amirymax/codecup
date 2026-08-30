"""Описание способа аутентификации для OpenAPI."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CookieJWTScheme(OpenApiAuthenticationExtension):
    """Без этого drf-spectacular не знает про нашу куку и ругается на каждую вьюху."""

    target_class = "apps.users.authentication.CookieJWTAuthentication"
    name = "cookieAuth"

    def get_security_definition(self, auto_schema):
        from django.conf import settings

        return {
            "type": "apiKey",
            "in": "cookie",
            "name": settings.AUTH_COOKIE_ACCESS_NAME,
            "description": "JWT в httpOnly-куке. Ставится на /api/auth/telegram/exchange/.",
        }
