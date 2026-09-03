from __future__ import annotations

from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from .models import EntryPayment, PaymentSettings, PaymentStatus


class MyPaymentSerializer(serializers.ModelSerializer):
    """Своё участие глазами участника."""

    class Meta:
        model = EntryPayment
        fields = [
            "id",
            "amount",
            "currency",
            "status",
            "has_receipt",
            "expects_receipt_in_bot",
            "rejection_reason",
            "submitted_at",
            "created_at",
        ]
        read_only_fields = fields

    has_receipt = serializers.BooleanField(read_only=True)


class ParticipationSerializer(serializers.Serializer):
    """Что нужно знать странице контеста об участии."""

    is_paid = serializers.BooleanField()
    entry_fee = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    requisites = serializers.CharField()
    can_submit = serializers.BooleanField()
    payment = MyPaymentSerializer(allow_null=True)


class ReceiptUploadSerializer(serializers.Serializer):
    """Чек, загруженный с сайта."""

    receipt = serializers.FileField()

    def validate_receipt(self, value):
        if value.size > settings.RECEIPT_MAX_BYTES:
            limit = settings.RECEIPT_MAX_BYTES // (1024 * 1024)
            raise serializers.ValidationError(f"Файл больше {limit} МБ.")
        if value.content_type not in settings.RECEIPT_CONTENT_TYPES:
            raise serializers.ValidationError("Подойдёт изображение или PDF.")
        return value


class AdminPaymentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    telegram_username = serializers.CharField(source="user.telegram_username", read_only=True)
    contest_title = serializers.CharField(source="contest.title", read_only=True)
    contest_slug = serializers.SlugField(source="contest.slug", read_only=True)
    receipt_url = serializers.SerializerMethodField()
    receipt_source = serializers.SerializerMethodField()

    class Meta:
        model = EntryPayment
        fields = [
            "id",
            "username",
            "telegram_username",
            "contest_title",
            "contest_slug",
            "amount",
            "currency",
            "status",
            "receipt_url",
            "receipt_source",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_receipt_source(self, payment: EntryPayment) -> str:
        """file — можно открыть, telegram — только в чате, none — чека нет."""
        if payment.receipt:
            return "file"
        return "telegram" if payment.telegram_file_id else "none"

    def get_receipt_url(self, payment: EntryPayment) -> str | None:
        """Ссылка на защищённый эндпоинт, а не на файл в media.

        Открывается переходом по ссылке, поэтому кука сессии уходит вместе с
        запросом и права проверяются как обычно.
        """
        if not payment.receipt:
            return None
        url = reverse("admin-payment-receipt", args=[payment.id])
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class PaymentDecisionSerializer(serializers.Serializer):
    """Решение админа по чеку."""

    decision = serializers.ChoiceField(choices=["accept", "reject"])
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, attrs):
        if attrs["decision"] == "reject" and not attrs.get("reason"):
            raise serializers.ValidationError({"reason": "Укажите причину отказа."})
        return attrs


__all__ = [
    "AdminPaymentSerializer",
    "MyPaymentSerializer",
    "ParticipationSerializer",
    "PaymentDecisionSerializer",
    "PaymentStatus",
    "ReceiptUploadSerializer",
]


class PaymentSettingsSerializer(serializers.ModelSerializer):
    """Реквизиты в админке."""

    requisites = serializers.CharField(allow_blank=True, max_length=2000)

    class Meta:
        model = PaymentSettings
        fields = ["requisites", "updated_at"]
        read_only_fields = ["updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Админ должен видеть ровно тот текст, который видит участник,
        # включая запасной — иначе он правит пустоту и не понимает, почему.
        data["requisites"] = instance.effective_requisites
        return data
