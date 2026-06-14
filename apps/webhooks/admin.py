from django.contrib import admin

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = (
        "url",
        "is_active",
        "deleted_at",
        "max_retries",
        "created_by",
        "created_at",
    )
    list_filter = ("is_active", "deleted_at")
    search_fields = ("url",)
    readonly_fields = ("deleted_at", "created_at", "updated_at")


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ("event_type", "endpoint", "status", "attempts", "created_at")
    list_filter = ("status", "event_type")
    readonly_fields = ("created_at", "updated_at")
