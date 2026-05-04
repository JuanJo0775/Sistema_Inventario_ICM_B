from django.contrib import admin

from apps.alerts.models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("product", "alert_type", "is_resolved", "created_at")
