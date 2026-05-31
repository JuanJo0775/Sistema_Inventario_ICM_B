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
            "max_retries",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")
        extra_kwargs = {
            "secret": {"write_only": True},
        }


class WebhookEndpointCreateSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=500)
    secret = serializers.CharField(max_length=128, min_length=8)
    events = serializers.ListField(
        child=serializers.CharField(max_length=64),
        min_length=1,
        help_text='Lista de event_types a suscribir. Ej: ["STOCK_CRITICO"].',
    )
    is_active = serializers.BooleanField(default=True)
    max_retries = serializers.IntegerField(min_value=1, max_value=10, default=3)


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
