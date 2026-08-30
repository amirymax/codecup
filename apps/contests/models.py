from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .slugs import unique_slug

MAX_REQUIREMENTS = 20
MAX_REQUIREMENT_LENGTH = 300


def validate_requirements(value: object) -> None:
    """Требования — это упорядоченный список непустых строк."""
    if not isinstance(value, list):
        raise ValidationError("Требования должны быть списком.")
    if len(value) > MAX_REQUIREMENTS:
        raise ValidationError(f"Не больше {MAX_REQUIREMENTS} требований.")
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("Каждое требование — это строка.")
        if not item.strip():
            raise ValidationError("Требование не может быть пустым.")
        if len(item) > MAX_REQUIREMENT_LENGTH:
            raise ValidationError(f"Требование длиннее {MAX_REQUIREMENT_LENGTH} символов.")


class ContestStatus(models.TextChoices):
    """То, чем управляет админ."""

    DRAFT = "draft", "черновик"
    PUBLISHED = "published", "опубликован"
    ARCHIVED = "archived", "в архиве"


class ContestState(models.TextChoices):
    """То, что видит пользователь: зависит ещё и от текущего времени."""

    DRAFT = "draft", "черновик"
    LIVE = "live", "идёт"
    ENDED = "ended", "завершён"
    ARCHIVED = "archived", "в архиве"


class ContestQuerySet(models.QuerySet):
    def public(self) -> ContestQuerySet:
        """Всё, что вообще можно показывать снаружи."""
        return self.filter(status=ContestStatus.PUBLISHED)

    def live(self) -> ContestQuerySet:
        return self.public().filter(deadline__gt=timezone.now())

    def ended(self) -> ContestQuerySet:
        return self.public().filter(deadline__lte=timezone.now())

    def by_state(self, state: str | None) -> ContestQuerySet:
        if state == ContestState.LIVE:
            return self.live()
        if state == ContestState.ENDED:
            return self.ended()
        return self.public()


class Contest(models.Model):
    """Контест.

    ``status`` — это решение админа, а ``state`` вычисляется на чтение из
    статуса и дедлайна. Поэтому контест не может «зависнуть» опубликованным
    после дедлайна, и для перевода в завершённые не нужен фоновый процесс.
    """

    number = models.PositiveIntegerField("номер", unique=True, editable=False)
    slug = models.SlugField("адрес", max_length=220, unique=True, blank=True)
    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    requirements = models.JSONField(
        "требования",
        default=list,
        blank=True,
        validators=[validate_requirements],
    )
    prize_pool = models.DecimalField("призовой фонд", max_digits=12, decimal_places=2, default=0)
    currency = models.CharField("валюта", max_length=3, default="USD")
    starts_at = models.DateTimeField("начало", null=True, blank=True)
    deadline = models.DateTimeField("дедлайн")
    status = models.CharField(
        "статус",
        max_length=16,
        choices=ContestStatus.choices,
        default=ContestStatus.DRAFT,
    )
    is_featured = models.BooleanField("показывать на главной", default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="автор",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_contests",
    )
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    objects = ContestQuerySet.as_manager()

    class Meta:
        verbose_name = "контест"
        verbose_name_plural = "контесты"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "deadline"])]

    def __str__(self) -> str:
        return f"#{self.number:02d} {self.title}"

    def save(self, *args, **kwargs) -> None:
        if self.number is None:
            self.number = self._next_number()
        if not self.slug:
            self.slug = unique_slug(
                type(self),
                self.title,
                fallback=f"contest-{self.number}",
                exclude_pk=self.pk,
            )
        super().save(*args, **kwargs)

    @classmethod
    def _next_number(cls) -> int:
        last = cls.objects.aggregate(models.Max("number"))["number__max"]
        return (last or 0) + 1

    # --- вычисляемое состояние ------------------------------------------

    @property
    def state(self) -> str:
        if self.status == ContestStatus.DRAFT:
            return ContestState.DRAFT
        if self.status == ContestStatus.ARCHIVED:
            return ContestState.ARCHIVED
        return ContestState.ENDED if self.is_over else ContestState.LIVE

    @property
    def is_over(self) -> bool:
        return timezone.now() >= self.deadline

    @property
    def has_started(self) -> bool:
        return self.starts_at is None or timezone.now() >= self.starts_at

    @property
    def accepts_submissions(self) -> bool:
        """Можно ли сейчас присылать и править решения."""
        return self.state == ContestState.LIVE and self.has_started

    @property
    def display_number(self) -> str:
        return f"#{self.number:02d}"

    def publish(self) -> None:
        self.status = ContestStatus.PUBLISHED
        self.save(update_fields=["status", "updated_at"])


class NotifySubscription(models.Model):
    """«Уведомить меня» с главной, когда активного контеста нет."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        related_name="notify_subscription",
    )
    created_at = models.DateTimeField("создана", auto_now_add=True)

    class Meta:
        verbose_name = "подписка на уведомления"
        verbose_name_plural = "подписки на уведомления"

    def __str__(self) -> str:
        return str(self.user)
