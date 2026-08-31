from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


def receipt_path(instance: EntryPayment, filename: str) -> str:
    return f"receipts/{instance.contest_id}/{instance.user_id}/{filename}"


class PaymentStatus(models.TextChoices):
    AWAITING_RECEIPT = "awaiting_receipt", "ждём чек"
    PENDING = "pending", "на проверке"
    ACCEPTED = "accepted", "принят"
    REJECTED = "rejected", "отклонён"


class EntryPaymentQuerySet(models.QuerySet):
    def pending_review(self) -> EntryPaymentQuerySet:
        return self.filter(status=PaymentStatus.PENDING)

    def accepted(self) -> EntryPaymentQuerySet:
        return self.filter(status=PaymentStatus.ACCEPTED)


class EntryPayment(models.Model):
    """Взнос за участие в платном контесте.

    Одна запись на человека и контест: платят один раз. Отклонённый чек не
    создаёт вторую запись — участник присылает новый в ту же.
    """

    contest = models.ForeignKey(
        "contests.Contest",
        verbose_name="контест",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="участник",
        on_delete=models.CASCADE,
        related_name="payments",
    )

    # Сумма фиксируется на момент заявки: если админ потом поменяет взнос,
    # уже отправленные чеки не должны «подорожать» задним числом.
    amount = models.DecimalField("сумма", max_digits=12, decimal_places=2)
    currency = models.CharField("валюта", max_length=3)

    status = models.CharField(
        "статус",
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.AWAITING_RECEIPT,
    )

    receipt = models.FileField("чек", upload_to=receipt_path, blank=True)
    # Чек, пришедший в бот: id файла в Telegram сохраняем на случай, если
    # скачать его сразу не удалось.
    telegram_file_id = models.CharField("файл в Telegram", max_length=200, blank=True)
    receipt_kind = models.CharField("тип файла", max_length=10, blank=True)  # photo | document
    # Пока флаг взведён, следующий файл от этого человека в боте считается чеком.
    expects_receipt_in_bot = models.BooleanField("ждём чек в боте", default=False)

    submitted_at = models.DateTimeField("чек получен", null=True, blank=True)
    reviewed_at = models.DateTimeField("проверен", null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="проверил",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payments",
    )
    rejection_reason = models.TextField("причина отказа", blank=True)

    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    objects = EntryPaymentQuerySet.as_manager()

    class Meta:
        verbose_name = "взнос за участие"
        verbose_name_plural = "взносы за участие"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["contest", "user"], name="unique_payment_per_entry")
        ]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"{self.user} → {self.contest} ({self.get_status_display()})"

    @property
    def is_accepted(self) -> bool:
        return self.status == PaymentStatus.ACCEPTED

    @property
    def receipt_is_photo(self) -> bool:
        """Фото Telegram пересылает как photo, файл — как document."""
        return bool(self.telegram_file_id) and self.receipt_kind == "photo"

    @property
    def has_receipt(self) -> bool:
        return bool(self.receipt) or bool(self.telegram_file_id)

    def attach_receipt(self, *, file=None, telegram_file_id: str = "", kind: str = "") -> None:
        """Принимает чек с сайта или из бота и ставит его в очередь проверки."""
        if file is not None:
            self.receipt = file
        if telegram_file_id:
            self.telegram_file_id = telegram_file_id
            self.receipt_kind = kind

        self.status = PaymentStatus.PENDING
        self.submitted_at = timezone.now()
        self.expects_receipt_in_bot = False
        self.rejection_reason = ""
        self.save()

    def wait_for_bot_receipt(self) -> None:
        self.status = PaymentStatus.AWAITING_RECEIPT
        self.expects_receipt_in_bot = True
        self.save(update_fields=["status", "expects_receipt_in_bot", "updated_at"])

    def accept(self, reviewer) -> None:
        self.status = PaymentStatus.ACCEPTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = ""
        self.save(
            update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"]
        )

    def reject(self, reviewer, reason: str = "") -> None:
        self.status = PaymentStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        # Отклонённый чек можно заменить новым, поэтому запись остаётся живой.
        self.save(
            update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"]
        )
