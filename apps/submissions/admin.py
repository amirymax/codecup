from django.contrib import admin

from .models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["user", "contest", "status", "score", "is_winner", "submitted_at"]
    list_filter = ["status", "is_winner", "contest"]
    search_fields = ["user__username", "github_url", "contest__title"]
    readonly_fields = ["created_at", "updated_at", "submitted_at", "reviewed_at"]
    autocomplete_fields = ["user", "contest"]

    fieldsets = (
        (None, {"fields": ("contest", "user", "status")}),
        ("Решение", {"fields": ("github_url", "live_url", "video_url", "description")}),
        ("Проверка", {"fields": ("score", "reviewer_notes", "is_winner", "reviewed_by")}),
        ("Даты", {"fields": ("submitted_at", "reviewed_at", "created_at", "updated_at")}),
    )
