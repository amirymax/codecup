from django.contrib import admin

from .models import Contest, ContestState, NotifySubscription


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = [
        "display_number",
        "title",
        "state_label",
        "prize_pool",
        "deadline",
        "is_featured",
    ]
    list_filter = ["status", "is_featured"]
    search_fields = ["title", "description", "slug"]
    readonly_fields = ["number", "created_at", "updated_at", "state_label"]
    prepopulated_fields: dict = {}

    fieldsets = (
        (None, {"fields": ("number", "title", "slug", "description", "requirements")}),
        ("Условия", {"fields": ("prize_pool", "currency", "starts_at", "deadline")}),
        ("Публикация", {"fields": ("status", "state_label", "is_featured", "created_by")}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="состояние")
    def state_label(self, obj: Contest) -> str:
        return ContestState(obj.state).label


@admin.register(NotifySubscription)
class NotifySubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at"]
    search_fields = ["user__username"]
