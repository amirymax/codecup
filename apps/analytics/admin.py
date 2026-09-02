from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["name", "path", "user", "created_at"]
    list_filter = ["name", "created_at"]
    search_fields = ["path"]
    readonly_fields = ["name", "path", "visitor", "user", "created_at"]
