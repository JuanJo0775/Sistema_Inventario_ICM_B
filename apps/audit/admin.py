from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "created_at")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
