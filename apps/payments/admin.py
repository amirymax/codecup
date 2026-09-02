from django.contrib import admin

from .models import EntryPayment


@admin.register(EntryPayment)
class EntryPaymentAdmin(admin.ModelAdmin):
    list_display = ["user", "contest", "amount", "currency", "status", "submitted_at"]
    list_filter = ["status", "currency", "contest"]
    search_fields = ["user__username", "user__telegram_username", "contest__title"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "submitted_at",
        "reviewed_at",
        "telegram_file_id",
    ]
    autocomplete_fields = ["user", "contest"]
