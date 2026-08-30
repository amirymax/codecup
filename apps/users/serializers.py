from __future__ import annotations

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Профиль текущего пользователя."""

    display_name = serializers.CharField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "display_name",
            "telegram_username",
            "first_name",
            "last_name",
            "photo_url",
            "is_admin",
            "notify_opt_in",
            "created_at",
        ]
        read_only_fields = fields


class AuthStartResponseSerializer(serializers.Serializer):
    nonce = serializers.CharField()
    client_secret = serializers.CharField()
    deep_link = serializers.URLField()
    expires_at = serializers.DateTimeField()
    expires_in = serializers.IntegerField()


class AuthStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class AuthExchangeRequestSerializer(serializers.Serializer):
    nonce = serializers.CharField(max_length=64)
    client_secret = serializers.CharField(max_length=64)
