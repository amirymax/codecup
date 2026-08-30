from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import TelegramAuthToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "telegram_id", "telegram_username", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_active", "notify_opt_in"]
    search_fields = ["username", "telegram_username", "telegram_id", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["telegram_id", "created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("username", "telegram_id", "telegram_username")}),
        ("Профиль", {"fields": ("first_name", "last_name", "photo_url", "language_code")}),
        ("Настройки", {"fields": ("notify_opt_in",)}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Даты", {"fields": ("created_at", "updated_at", "last_login")}),
    )
    add_fieldsets = ((None, {"fields": ("username", "telegram_id", "password1", "password2")}),)


@admin.register(TelegramAuthToken)
class TelegramAuthTokenAdmin(admin.ModelAdmin):
    list_display = ["nonce_preview", "status", "user", "created_at", "expires_at"]
    list_filter = ["status"]
    search_fields = ["nonce", "user__username"]
    readonly_fields = [field.name for field in TelegramAuthToken._meta.fields]

    @admin.display(description="код")
    def nonce_preview(self, obj: TelegramAuthToken) -> str:
        return f"{obj.nonce[:12]}…"

    def has_add_permission(self, request) -> bool:
        return False
