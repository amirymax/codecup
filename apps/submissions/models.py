from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

MAX_DESCRIPTION_LENGTH = 500
MAX_SCORE = 100

GITHUB_URL = re.compile(r"^https?://(www\.)?github\.com/[^/\s]+/[^/\s]+", re.IGNORECASE)


def validate_github_url(value: str) -> None:
    if not GITHUB_URL.match(value):
        raise ValidationError("Ссылка должна вести на репозиторий github.com.")


class SubmissionStatus(models.TextChoices):
    DRAFT = "draft", "черновик"
    SUBMITTED = "submitted", "отправлено"
    REVIEWED = "reviewed", "проверено"


class DisplayStatus(models.TextChoices):
    """Четыре бейджа из макетов. ``winner`` перекрывает обычный статус."""

    DRAFT = "draft", "черновик"
    SUBMITTED = "submitted", "отправлено"
    REVIEWED = "reviewed", "проверено"
    WINNER = "winner", "победитель"


class SubmissionQuerySet(models.QuerySet):
    def counted(self) -> SubmissionQuerySet:
        """Заявки, которые считаются участием: черновики не в счёт."""
        return self.exclude(status=SubmissionStatus.DRAFT)

    def review_queue(self) -> SubmissionQuerySet:
        """Очередь проверки в стабильном порядке.

        Порядок фиксирован, иначе кнопки «предыдущая / следующая» на экране
        проверки водили бы админа по кругу.
        """
        return self.counted().order_by("submitted_at", "id")

    def pending_review(self) -> SubmissionQuerySet:
        return self.filter(status=SubmissionStatus.SUBMITTED)


class Submission(models.Model):
    """Решение участника.

    На контест приходится одна заявка от человека: на макете отправки прямо
    сказано, что засчитывается последняя версия до дедлайна. Поэтому здесь
    не история отправок, а одна редактируемая запись.
    """

    contest = models.ForeignKey(
        "contests.Contest",
        verbose_name="контест",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="участник",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    github_url = models.URLField("репозиторий GitHub", blank=True)
    live_url = models.URLField("живая демонстрация", blank=True)
    video_url = models.URLField("демо-видео", blank=True)
    description = models.TextField("описание", blank=True, max_length=MAX_DESCRIPTION_LENGTH)

    status = models.CharField(
        "статус",
        max_length=16,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.DRAFT,
    )
    submitted_at = models.DateTimeField("отправлено", null=True, blank=True)

    # --- поля проверки: наружу участнику не отдаются ---------------------
    score = models.PositiveSmallIntegerField(
        "оценка",
        null=True,
        blank=True,
        validators=[MaxValueValidator(MAX_SCORE)],
    )
    reviewer_notes = models.TextField("заметки проверяющего", blank=True)
    is_winner = models.BooleanField("победитель", default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="проверил",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_submissions",
    )
    reviewed_at = models.DateTimeField("проверено", null=True, blank=True)

    created_at = models.DateTimeField("создана", auto_now_add=True)
    updated_at = models.DateTimeField("обновлена", auto_now=True)

    objects = SubmissionQuerySet.as_manager()

    class Meta:
        verbose_name = "заявка"
        verbose_name_plural = "заявки"
        ordering = ["-submitted_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["contest", "user"],
                name="unique_submission_per_contest_and_user",
            )
        ]
        indexes = [models.Index(fields=["contest", "status"])]

    def __str__(self) -> str:
        return f"{self.user} → {self.contest.title}"

    @property
    def display_status(self) -> str:
        """Статус для бейджа: победа важнее, чем «проверено»."""
        return DisplayStatus.WINNER if self.is_winner else self.status

    @property
    def is_editable(self) -> bool:
        """Править можно, пока контест принимает решения."""
        return self.contest.accepts_submissions

    @property
    def repo_name(self) -> str:
        """``github.com/user/repo`` без схемы — так репозиторий показан в списках."""
        return self.github_url.split("://", 1)[-1].removeprefix("www.")

    def mark_submitted(self) -> None:
        # Повторная отправка не сдвигает дату: считается первый переход из
        # черновика, а правки после него дедлайн уже не продлевают.
        if self.status == SubmissionStatus.DRAFT:
            self.status = SubmissionStatus.SUBMITTED
            self.submitted_at = timezone.now()
            self.save(update_fields=["status", "submitted_at", "updated_at"])

    def apply_review(self, *, reviewer, score=None, notes=None, is_winner=None) -> None:
        fields = ["status", "reviewed_by", "reviewed_at", "updated_at"]
        if score is not None:
            self.score = score
            fields.append("score")
        if notes is not None:
            self.reviewer_notes = notes
            fields.append("reviewer_notes")
        if is_winner is not None:
            self.is_winner = is_winner
            fields.append("is_winner")

        self.status = SubmissionStatus.REVIEWED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=fields)
