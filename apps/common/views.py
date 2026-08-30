from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Проверка живости: приложение отвечает и база доступна."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(summary="Проверка состояния сервиса", responses={200: None, 503: None})
    def get(self, request: Request) -> Response:
        database_ok = self._database_ok()
        payload = {
            "status": "ok" if database_ok else "degraded",
            "database": "ok" if database_ok else "unavailable",
        }
        code = status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=code)

    @staticmethod
    def _database_ok() -> bool:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return False
        return True


class ApiNotFoundView(APIView):
    """Ловушка для несуществующих путей под /api/.

    Без неё Django отдаёт HTML-страницу 404, а фронтенд всегда разбирает
    ответ как JSON — и падает на разборе вместо того, чтобы показать ошибку.
    """

    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def get(self, request: Request, *args, **kwargs) -> Response:
        raise NotFound("Запрашиваемый ресурс не найден.")

    post = put = patch = delete = get
