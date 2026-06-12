"""Serializers de movimientos (RF-005–RF-009)."""

from __future__ import annotations

from rest_framework import serializers

from apps.movements.models import Movement


class MovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    lot_code = serializers.SerializerMethodField()
    lot_expiration_date = serializers.SerializerMethodField()

    def get_lot_code(self, obj):
        return getattr(getattr(obj, "lot", None), "code", None)

    def get_lot_expiration_date(self, obj):
        lot = getattr(obj, "lot", None)
        return getattr(lot, "expiration_date", None)

    class Meta:
        model = Movement
        fields = (
            "id",
            "movement_type",
            "product",
            "product_sku",
            "lot",
            "lot_code",
            "lot_expiration_date",
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
            # --- Precio snapshot (BR-16) ---
            # Todos nullable: null si el producto no tenía precio al momento del despacho.
            # Nunca bloquean el flujo — el despacho se completa aunque sean null.
            "unit_price",
            "unit_cost",
            "discount_pct",
            "discount_amount",
            "subtotal",
            "tax_rate_pct",
            "tax_amount",
            "total_amount",
            "currency",
            "price_type",
            "customer_snapshot",
        )
        read_only_fields = fields


class EntryCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    lot_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    lot_expiration_date = serializers.DateField(required=False, allow_null=True)
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
    lot_id = serializers.UUIDField(required=False, allow_null=True)
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
    discount_pct = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
        max_value=100,
        help_text=(
            "Descuento en porcentaje (0-100). Opcional — omitir si no aplica descuento. "
            "Solo tiene efecto si el producto tiene precio configurado."
        ),
    )


class TransferCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    origin_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    lot_id = serializers.UUIDField(required=False, allow_null=True)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    cold_chain_acknowledged = serializers.BooleanField(default=False)
    electrical_safety_acknowledged = serializers.BooleanField(default=False)


class ReturnCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    lot_id = serializers.UUIDField(required=False, allow_null=True)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    related_movement_id = serializers.UUIDField(required=False, allow_null=True)


class AdjustmentCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()
    new_quantity = serializers.IntegerField(min_value=0)
    justification = serializers.CharField(allow_blank=True)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class CorrectionCreateSerializer(serializers.Serializer):
    origin_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class AdjustmentCorrectionSerializer(serializers.Serializer):
    """Cuerpo para `POST .../adjustments/correct/` con id de movimiento."""

    movement_id = serializers.UUIDField()
    origin_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class ComboDispatchSerializer(serializers.Serializer):
    """Despacho de un combo completo desde una ubicación (RF-003, Opción B)."""

    combo_id = serializers.UUIDField(help_text="UUID del combo a despachar.")
    location_id = serializers.UUIDField(
        help_text="UUID de la ubicación desde donde se descuentan los productos."
    )
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class InvoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.CharField()
    customer_name = serializers.CharField()
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField()
    customer_address = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=4)
    discount_total = serializers.DecimalField(max_digits=12, decimal_places=4)
    tax_total = serializers.DecimalField(max_digits=12, decimal_places=4)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=4)
    currency = serializers.CharField()
    pdf = serializers.FileField(allow_null=True)
    issued_by = serializers.CharField(
        source="issued_by.username",
        help_text="Username del operador que generó la factura.",
    )
    issued_at = serializers.DateTimeField()
    movement_ids = serializers.SerializerMethodField(
        help_text="Lista de UUIDs de los movimientos agrupados en esta factura.",
    )

    def get_movement_ids(self, obj) -> list[str]:
        return [str(m.id) for m in obj.movements.all()]
