from __future__ import annotations

import hashlib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import constant_time_compare, get_random_string

from .managers import UserManager

NONCE_LENGTH = 32
CLIENT_SECRET_LENGTH = 48


class User(AbstractUser):
    """Участник или администратор. Личность — это telegram_id.

    Роль администратора — это ``is_staff``; отдельного поля роли нет, чтобы
    права в API и в админке Django не разъезжались.
    """

    telegram_id = models.BigIntegerField("Telegram ID", unique=True, db_index=True)
    telegram_username = models.CharField("username в Telegram", max_length=64, blank=True)
    photo_url = models.URLField("аватар", blank=True)
    language_code = models.CharField("язык в Telegram", max_length=5, default="ru")
    notify_opt_in = models.BooleanField("уведомлять о новых контестах", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.username

    @property
    def display_name(self) -> str:
        return self.telegram_username or self.username

    @property
    def is_admin(self) -> bool:
        return self.is_staff


class AuthTokenStatus(models.TextChoices):
    PENDING = "pending", "ожидает подтверждения"
    CONFIRMED = "confirmed", "подтверждён"
    CONSUMED = "consumed", "обменян на сессию"
    CANCELLED = "cancelled", "отменён"
    EXPIRED = "expired", "просрочен"


class TelegramAuthToken(models.Model):
    """Одна попытка входа через Telegram.

    ``nonce`` уходит в Telegram внутри deep link, поэтому сам по себе он не
    даёт сессию: обменять его можно только вместе с ``client_secret``,
    который остался в браузере. Токен одноразовый и живёт пять минут.
    """

    nonce = models.CharField("одноразовый код", max_length=64, unique=True, db_index=True)
    client_secret_hash = models.CharField("хеш секрета браузера", max_length=64)
    status = models.CharField(
        "статус",
        max_length=16,
        choices=AuthTokenStatus.choices,
        default=AuthTokenStatus.PENDING,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="auth_tokens",
    )
    created_at = models.DateTimeField("создан", auto_now_add=True)
    expires_at = models.DateTimeField("истекает")
    confirmed_at = models.DateTimeField("подтверждён", null=True, blank=True)
    consumed_at = models.DateTimeField("обменян", null=True, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=400, blank=True)

    class Meta:
        verbose_name = "токен входа"
        verbose_name_plural = "токены входа"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "expires_at"])]

    def __str__(self) -> str:
        return f"{self.nonce[:8]}… ({self.get_status_display()})"

    # --- создание -------------------------------------------------------

    @classmethod
    def issue(cls, *, ip: str | None = None, user_agent: str = "") -> tuple[TelegramAuthToken, str]:
        """Создаёт токен. Возвращает его и client_secret — в базе только хеш."""
        client_secret = get_random_string(CLIENT_SECRET_LENGTH)
        token = cls.objects.create(
            nonce=get_random_string(NONCE_LENGTH),
            client_secret_hash=cls.hash_secret(client_secret),
            expires_at=timezone.now() + cls.lifetime(),
            ip=ip,
            user_agent=user_agent[:400],
        )
        return token, client_secret

    @staticmethod
    def lifetime() -> timedelta:
        return timedelta(seconds=settings.TELEGRAM_AUTH_TOKEN_TTL)

    @staticmethod
    def hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()

    # --- состояние ------------------------------------------------------

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def current_status(self) -> str:
        """Статус с учётом времени.

        Просрочка не пишется в базу отдельным заданием — она вычисляется,
        поэтому токен не может «зависнуть» в pending после истечения срока.
        """
        if self.status == AuthTokenStatus.PENDING and self.is_expired:
            return AuthTokenStatus.EXPIRED
        return self.status

    @property
    def is_confirmable(self) -> bool:
        return self.status == AuthTokenStatus.PENDING and not self.is_expired

    def matches_secret(self, client_secret: str) -> bool:
        return constant_time_compare(self.client_secret_hash, self.hash_secret(client_secret))

    # --- переходы -------------------------------------------------------

    def confirm(self, user: User) -> None:
        self.user = user
        self.status = AuthTokenStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=["user", "status", "confirmed_at"])

    def cancel(self) -> None:
        self.status = AuthTokenStatus.CANCELLED
        self.save(update_fields=["status"])

    def consume(self) -> None:
        self.status = AuthTokenStatus.CONSUMED
        self.consumed_at = timezone.now()
        self.save(update_fields=["status", "consumed_at"])
