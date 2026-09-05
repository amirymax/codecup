from __future__ import annotations

from rest_framework import serializers

from apps.common.serializers import NavigationSerializer
from apps.screening.serializers import ScreeningSerializer
from apps.users.serializers import UserSerializer

from .models import (
    GITHUB_URL,
    MAX_DESCRIPTION_LENGTH,
    MAX_SCORE,
    MIN_DESCRIPTION_LENGTH,
    DisplayStatus,
    Submission,
    SubmissionStatus,
    validate_live_url,
    validate_video_url,
)


class _BaseSubmissionSerializer(serializers.ModelSerializer):
    # ChoiceField даёт в схеме перечисление — на фронтенде это четыре бейджа
    # из макета, а не произвольная строка.
    display_status = serializers.ChoiceField(choices=DisplayStatus.choices, read_only=True)
    contest_title = serializers.CharField(source="contest.title", read_only=True)
    contest_slug = serializers.SlugField(source="contest.slug", read_only=True)


class MySubmissionSerializer(_BaseSubmissionSerializer):
    """Своя заявка глазами участника.

    Ни ``score``, ни ``reviewer_notes`` тут нет и быть не должно: на макете
    проверки заметки прямо помечены как невидимые для участника.
    """

    is_editable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "contest_title",
            "contest_slug",
            "github_url",
            "live_url",
            "video_url",
            "description",
            "status",
            "display_status",
            "is_editable",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "display_status",
            "is_editable",
            "submitted_at",
            "created_at",
            "updated_at",
        ]

    def validate_github_url(self, value: str) -> str:
        if value and not GITHUB_URL.match(value):
            raise serializers.ValidationError("Ссылка должна вести на репозиторий github.com.")
        return value

    def validate_live_url(self, value: str) -> str:
        if value:
            _reraise(validate_live_url, value)
        return value

    def validate_video_url(self, value: str) -> str:
        if value:
            _reraise(validate_video_url, value)
        return value

    def validate_description(self, value: str) -> str:
        # Верхняя граница действует всегда, нижняя — только при отправке:
        # черновик пишут по частям, и обрывать его на полуслове незачем.
        if len(value) > MAX_DESCRIPTION_LENGTH:
            raise serializers.ValidationError(f"Не длиннее {MAX_DESCRIPTION_LENGTH} символов.")
        return value

    def validate(self, attrs):
        """Черновик можно сохранить наполовину, отправленную заявку — нет.

        Иначе участник мог бы отправить решение, а потом стереть ссылки и
        остаться в списке отправивших с пустой заявкой.
        """
        if self._requires_complete_data():
            merged = {**self._current_values(), **attrs}
            missing = {}
            if not merged.get("github_url"):
                missing["github_url"] = "Ссылка на GitHub обязательна."
            if not merged.get("live_url"):
                missing["live_url"] = "Ссылка на демо обязательна."

            description = (merged.get("description") or "").strip()
            if len(description) < MIN_DESCRIPTION_LENGTH:
                missing["description"] = (
                    f"Опишите проект хотя бы в {MIN_DESCRIPTION_LENGTH} символах "
                    f"(сейчас {len(description)})."
                )

            if missing:
                raise serializers.ValidationError(missing)
        return attrs

    def _requires_complete_data(self) -> bool:
        if self.context.get("require_complete"):
            return True
        return self.instance is not None and self.instance.status != SubmissionStatus.DRAFT

    def _current_values(self) -> dict:
        if self.instance is None:
            return {}
        return {
            "github_url": self.instance.github_url,
            "live_url": self.instance.live_url,
            "description": self.instance.description,
        }


class ProfileSubmissionSerializer(_BaseSubmissionSerializer):
    """Строка истории на странице профиля."""

    repo_name = serializers.CharField(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "contest_title",
            "contest_slug",
            "repo_name",
            "display_status",
            "submitted_at",
            "created_at",
        ]
        read_only_fields = fields


class ContestWorkSerializer(_BaseSubmissionSerializer):
    """Работа участника, открытая всем на странице контеста.

    Ни оценки, ни заметок проверяющего здесь нет и быть не должно: это
    внутренняя кухня проверки, а не часть работы.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)
    repo_name = serializers.CharField(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "username",
            "display_name",
            "repo_name",
            "github_url",
            "live_url",
            "video_url",
            "description",
            "display_status",
            "submitted_at",
        ]
        read_only_fields = fields


class AdminSubmissionListSerializer(_BaseSubmissionSerializer):
    """Строка в списке заявок админки."""

    username = serializers.CharField(source="user.username", read_only=True)
    repo_name = serializers.CharField(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "username",
            "contest_title",
            "contest_slug",
            "repo_name",
            "status",
            "display_status",
            "score",
            "is_winner",
            "submitted_at",
        ]
        read_only_fields = fields


class AdminSubmissionDetailSerializer(_BaseSubmissionSerializer):
    """Экран проверки: здесь оценка и внутренние заметки уже видны."""

    username = serializers.CharField(source="user.username", read_only=True)
    telegram_username = serializers.CharField(source="user.telegram_username", read_only=True)
    repo_name = serializers.CharField(read_only=True)
    video_bonus = serializers.IntegerField(read_only=True)
    total_score = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "username",
            "telegram_username",
            "contest_title",
            "contest_slug",
            "github_url",
            "live_url",
            "video_url",
            "description",
            "repo_name",
            "status",
            "display_status",
            "score",
            "video_bonus",
            "total_score",
            "reviewer_notes",
            "is_winner",
            "reviewed_at",
            "submitted_at",
            "created_at",
        ]
        read_only_fields = [
            field for field in fields if field not in {"score", "reviewer_notes", "is_winner"}
        ]

    def validate_score(self, value):
        if value is not None and not 0 <= value <= MAX_SCORE:
            raise serializers.ValidationError(f"Оценка должна быть от 0 до {MAX_SCORE}.")
        return value


class MySubmissionEnvelopeSerializer(serializers.Serializer):
    """submission равен null, если участник ещё ничего не отправлял."""

    submission = MySubmissionSerializer(allow_null=True)


class PublicProfileSerializer(serializers.Serializer):
    """Страница профиля участника."""

    # Именно UserSerializer, а не DictField: иначе в схеме у поля нет
    # структуры и на фронтенде profile.user приходит как unknown.
    user = UserSerializer()
    submissions_count = serializers.IntegerField()
    wins_count = serializers.IntegerField()
    submissions = ProfileSubmissionSerializer(many=True)


class AdminSubmissionEnvelopeSerializer(serializers.Serializer):
    """Заявка, навигация по очереди и итог автоматической проверки."""

    submission = AdminSubmissionDetailSerializer()
    navigation = NavigationSerializer()
    screening = ScreeningSerializer(allow_null=True)


def _reraise(validator, value: str) -> None:
    """Переводит ValidationError из модели в ошибку поля DRF."""
    from django.core.exceptions import ValidationError as DjangoValidationError

    try:
        validator(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages[0]) from exc
