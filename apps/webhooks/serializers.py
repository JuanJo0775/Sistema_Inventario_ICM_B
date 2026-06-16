"""Serializers de webhooks."""

from __future__ import annotations

from rest_framework import serializers

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = (
            "id",
            "url",
            "secret",
            "events",
            "is_active",
            "deleted_at",
            "max_retries",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "deleted_at",
            "created_by",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "secret": {"write_only": True},
        }


KNOWN_EVENT_TYPES = {
    # Events emitted by apps/alerts/services.py
    "LOW_STOCK",
    "EXPIRATION_30",
    "EXPIRATION_60",
    "LOT_EXPIRED",
    "COLD_CHAIN_MISSING",
    "LOCATION_BLOCKED_WITH_STOCK",
    "STOCK_MISMATCH",
    "STOCK_ZERO",
    # Events emitted by apps/movements/services.py
    "dispatch.completed",
    # Events emitted by apps/inventory/management/commands
    "STOCK_INTEGRITY_DIVERGENCE",
    # Aliases / legacy used in tests and documentation
    "STOCK_CRITICO",
    "PROXIMO_VENCIMIENTO",
    "movement.created",
    "alert.triggered",
    "TEST",
}


class WebhookEndpointCreateSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=500)
    secret = serializers.CharField(max_length=128, min_length=8)
    events = serializers.ListField(
        child=serializers.CharField(max_length=64),
        min_length=1,
        help_text='Lista de event_types a suscribir. Ej: ["dispatch.completed"].',
    )
    is_active = serializers.BooleanField(default=True)
    max_retries = serializers.IntegerField(min_value=1, max_value=10, default=3)

    def validate_events(self, value):
        unknown = [e for e in value if e not in KNOWN_EVENT_TYPES]
        if unknown:
            raise serializers.ValidationError(
                f"Tipos de evento desconocidos: {unknown}. Válidos: {sorted(KNOWN_EVENT_TYPES)}."
            )
        return value


class WebhookDeliverySerializer(serializers.ModelSerializer):
    endpoint_url = serializers.CharField(source="endpoint.url", read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = (
            "id",
            "endpoint",
            "endpoint_url",
            "event_type",
            "status",
            "attempts",
            "last_attempt_at",
            "next_retry_at",
            "response_code",
            "created_at",
        )
        read_only_fields = fields


class WebhookTestSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=64, default="TEST")
    payload = serializers.DictField(default=dict)
