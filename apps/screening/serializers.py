from __future__ import annotations

from rest_framework import serializers

from .models import SubmissionScreening


class ScreeningSerializer(serializers.ModelSerializer):
    """Итог автоматической проверки для экрана разбора заявки."""

    high_severity_count = serializers.IntegerField(read_only=True)
    has_findings = serializers.BooleanField(read_only=True)

    class Meta:
        model = SubmissionScreening
        fields = [
            "status",
            "findings",
            "repo_meta",
            "live_status",
            "files_scanned",
            "high_severity_count",
            "has_findings",
            "error",
            "checked_at",
        ]
        read_only_fields = fields
