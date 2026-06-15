from __future__ import annotations

from rest_framework import serializers

from apps.alerts.models import Alert


class AlertStatsSerializer(serializers.Serializer):
    total_active = serializers.IntegerField()
    by_severity = serializers.DictField(child=serializers.IntegerField())
    by_category = serializers.DictField(child=serializers.IntegerField())
    generated_at = serializers.CharField()


class AlertSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    lot_code = serializers.CharField(source="lot.code", read_only=True)
    lot_expiration_date = serializers.DateField(
        source="lot.expiration_date", read_only=True
    )

    class Meta:
        model = Alert
        fields = (
            "id",
            "product",
            "product_sku",
            "lot",
            "lot_code",
            "lot_expiration_date",
            "location",
            "alert_type",
            "severity",
            "category",
            "message",
            "is_resolved",
            "resolved_at",
            "resolved_by",
            "created_at",
        )
        read_only_fields = fields
