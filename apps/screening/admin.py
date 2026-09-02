from django.contrib import admin

from .models import SubmissionScreening


@admin.register(SubmissionScreening)
class SubmissionScreeningAdmin(admin.ModelAdmin):
    list_display = ["submission", "status", "finding_count", "live_status", "checked_at"]
    list_filter = ["status"]
    search_fields = ["submission__user__username", "submission__github_url"]
    readonly_fields = [field.name for field in SubmissionScreening._meta.fields]

    @admin.display(description="находок")
    def finding_count(self, obj: SubmissionScreening) -> int:
        return len(obj.findings)

    def has_add_permission(self, request) -> bool:
        return False
