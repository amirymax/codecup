from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from .models import Contest, ContestStatus, validate_requirements


class ContestListSerializer(serializers.ModelSerializer):
    """Карточка контеста в списке и на главной."""

    state = serializers.CharField(read_only=True)
    display_number = serializers.CharField(read_only=True)
    seconds_left = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "number",
            "display_number",
            "slug",
            "title",
            "description",
            "prize_pool",
            "currency",
            "deadline",
            "seconds_left",
            "state",
        ]
        read_only_fields = fields

    def get_seconds_left(self, contest: Contest) -> int:
        """Сколько секунд осталось до дедлайна.

        Отдаём числом, а не строкой: обратный отсчёт на фронтенде тикает сам,
        и ему не нужно доверять часам на устройстве пользователя.
        """
        return max(0, int((contest.deadline - timezone.now()).total_seconds()))


class ContestDetailSerializer(ContestListSerializer):
    class Meta(ContestListSerializer.Meta):
        fields = [
            *ContestListSerializer.Meta.fields,
            "requirements",
            "starts_at",
            "accepts_submissions",
            "created_at",
        ]
        read_only_fields = fields


class AdminContestSerializer(serializers.ModelSerializer):
    """Создание и редактирование контеста админом."""

    state = serializers.CharField(read_only=True)
    display_number = serializers.CharField(read_only=True)

    class Meta:
        model = Contest
        fields = [
            "id",
            "number",
            "display_number",
            "slug",
            "title",
            "description",
            "requirements",
            "prize_pool",
            "currency",
            "starts_at",
            "deadline",
            "status",
            "state",
            "is_featured",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "number", "display_number", "state", "created_at", "updated_at"]

    def validate_requirements(self, value):
        validate_requirements(value)
        return [item.strip() for item in value]

    def validate_deadline(self, value):
        # Правило нужно только при публикации: черновик можно готовить заранее
        # и выставить дату позже.
        if self.initial_data.get("status") == ContestStatus.PUBLISHED and value <= timezone.now():
            raise serializers.ValidationError(
                "Дедлайн опубликованного контеста должен быть в будущем."
            )
        return value

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        deadline = attrs.get("deadline", getattr(self.instance, "deadline", None))
        if starts_at and deadline and starts_at >= deadline:
            raise serializers.ValidationError({"starts_at": "Начало должно быть раньше дедлайна."})
        return attrs


class FeaturedContestSerializer(serializers.Serializer):
    """Ответ главной страницы; contest равен null, когда ничего не идёт."""

    contest = ContestDetailSerializer(allow_null=True)
