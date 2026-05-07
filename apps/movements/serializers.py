"""Serializers de movimientos (RF-005–RF-009)."""

from __future__ import annotations

from rest_framework import serializers

from apps.movements.models import Movement


class MovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = Movement
        fields = (
            "id",
            "movement_type",
            "product",
            "product_sku",
            "origin_location",
            "destination_location",
            "quantity",
            "stock_previo_origen",
            "stock_resultante_origen",
            "stock_previo_destino",
            "stock_resultante_destino",
            "serial_number",
            "quantity_invoiced",
            "discrepancy_note",
            "justification",
            "scanned_code",
            "order_sku",
            "invoice_number",
            "invoice_pdf",
            "related_movement",
            "executed_by",
            "created_at",
        )
        read_only_fields = fields


class EntryCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    qty_invoiced = serializers.IntegerField(required=False, allow_null=True)
    discrepancy_note = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    cold_chain_acknowledged = serializers.BooleanField(default=False)
    electrical_safety_acknowledged = serializers.BooleanField(default=False)


class DispatchCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    movement_type = serializers.CharField()
    scanned_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    order_sku = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    customer_data = serializers.JSONField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)
    cold_chain_acknowledged = serializers.BooleanField(default=False)
    electrical_safety_acknowledged = serializers.BooleanField(default=False)
    privacy_notice_acknowledged = serializers.BooleanField(default=False)


class TransferCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    origin_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    cold_chain_acknowledged = serializers.BooleanField(default=False)
    electrical_safety_acknowledged = serializers.BooleanField(default=False)


class ReturnCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    related_movement_id = serializers.UUIDField(required=False, allow_null=True)


class AdjustmentCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    new_quantity = serializers.IntegerField(min_value=0)
    justification = serializers.CharField(allow_blank=True)


class CorrectionCreateSerializer(serializers.Serializer):
    origin_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class AdjustmentCorrectionSerializer(serializers.Serializer):
    """Cuerpo para `POST .../adjustments/correct/` con id de movimiento."""

    movement_id = serializers.UUIDField()
    origin_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class ComboDispatchSerializer(serializers.Serializer):
    """Despacho de un combo completo desde una ubicación (RF-003, Opción B)."""

    combo_id = serializers.UUIDField(help_text="UUID del combo a despachar.")
    location_id = serializers.UUIDField(
        help_text="UUID de la ubicación desde donde se descuentan los productos."
    )
