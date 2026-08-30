from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "apps.users"
    label = "users"
    verbose_name = "Пользователи"

    def ready(self) -> None:
        # Регистрирует описание куки-аутентификации в схеме OpenAPI.
        from . import schema  # noqa: F401
