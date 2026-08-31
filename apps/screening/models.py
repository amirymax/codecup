from __future__ import annotations

from django.db import models
from django.utils import timezone


class ScreeningStatus(models.TextChoices):
    PENDING = "pending", "в очереди"
    DONE = "done", "проверено"
    FAILED = "failed", "не удалось"


class SubmissionScreening(models.Model):
    """Результат автоматической проверки присланного репозитория.

    Находки ничего не блокируют: у любого сканера секретов есть ложные
    срабатывания, и отклонять по ним живую работу нельзя. Это подсказка
    проверяющему, а не приговор.
    """

    submission = models.OneToOneField(
        "submissions.Submission",
        verbose_name="заявка",
        on_delete=models.CASCADE,
        related_name="screening",
    )
    status = models.CharField(
        "статус",
        max_length=10,
        choices=ScreeningStatus.choices,
        default=ScreeningStatus.PENDING,
    )
    findings = models.JSONField("находки", default=list, blank=True)
    repo_meta = models.JSONField("о репозитории", default=dict, blank=True)
    live_status = models.PositiveSmallIntegerField("ответ демо", null=True, blank=True)
    files_scanned = models.PositiveIntegerField("файлов проверено", default=0)
    error = models.TextField("ошибка", blank=True)
    checked_at = models.DateTimeField("проверено", null=True, blank=True)
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        verbose_name = "проверка заявки"
        verbose_name_plural = "проверки заявок"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"проверка {self.submission_id} ({self.get_status_display()})"

    @property
    def high_severity_count(self) -> int:
        return sum(1 for item in self.findings if item.get("severity") == "high")

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    def finish(self, *, findings, repo_meta, live_status, files_scanned) -> None:
        self.findings = findings
        self.repo_meta = repo_meta
        self.live_status = live_status
        self.files_scanned = files_scanned
        self.status = ScreeningStatus.DONE
        self.error = ""
        self.checked_at = timezone.now()
        self.save()

    def fail(self, reason: str) -> None:
        self.status = ScreeningStatus.FAILED
        self.error = reason[:2000]
        self.checked_at = timezone.now()
        self.save(update_fields=["status", "error", "checked_at"])
