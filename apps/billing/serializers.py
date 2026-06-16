"""Serializers para el módulo de facturación comercial."""

from __future__ import annotations

from rest_framework import serializers

from apps.movements.models import Invoice, Movement


class InvoiceItemInputSerializer(serializers.Serializer):
    """Un ítem del carrito al crear una factura multi-producto."""

    product_id = serializers.UUIDField(help_text="UUID del producto a despachar.")
    quantity = serializers.IntegerField(min_value=1, help_text="Cantidad a despachar.")
    discount_pct = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        help_text="Porcentaje de descuento (0-100). Opcional.",
    )


class CustomerDataInputSerializer(serializers.Serializer):
    """Datos del cliente para la factura."""

    name = serializers.CharField(max_length=255, help_text="Nombre o razón social.")
    id_number = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default="",
        help_text="NIT o número de documento.",
    )
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    address = serializers.CharField(required=False, allow_blank=True, default="")


class InvoiceCreateSerializer(serializers.Serializer):
    """
    Cuerpo para POST /billing/invoices/ — factura multi-producto.

    RF-006, BR-13 — Crea múltiples movements de salida y los agrupa en un Invoice.
    """

    invoice_type = serializers.ChoiceField(
        choices=["retail", "wholesale"],
        help_text="'retail' → SALIDA_VENTA_MENOR | 'wholesale' → SALIDA_VENTA_MAYOR.",
    )
    location_id = serializers.UUIDField(
        help_text="UUID de la ubicación origen del stock."
    )
    customer = CustomerDataInputSerializer()
    items = InvoiceItemInputSerializer(many=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    privacy_notice_acknowledged = serializers.BooleanField(
        default=False,
        help_text="Requerido para wholesale (Ley 1581, RNF-006).",
    )

    def validate_items(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError(
                "La factura debe contener al menos un ítem."
            )
        return value


class InvoiceVoidSerializer(serializers.Serializer):
    """Cuerpo para POST /billing/invoices/{id}/void/."""

    reason = serializers.CharField(
        min_length=5,
        max_length=500,
        help_text="Motivo de anulación (obligatorio, mínimo 5 caracteres).",
    )


class MovementSummarySerializer(serializers.ModelSerializer):
    """Resumen de Movement para el detalle de factura."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Movement
        fields = (
            "id",
            "movement_type",
            "product",
            "product_sku",
            "product_name",
            "quantity",
            "unit_price",
            "discount_pct",
            "discount_amount",
            "subtotal",
            "tax_rate_pct",
            "tax_amount",
            "total_amount",
            "origin_location",
            "created_at",
        )
        read_only_fields = fields


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Detalle completo de factura para GET /billing/invoices/{id}/."""

    issued_by_username = serializers.CharField(
        source="issued_by.username", read_only=True
    )
    voided_by_username = serializers.CharField(
        source="voided_by.username",
        read_only=True,
        allow_null=True,
    )
    movements_detail = MovementSummarySerializer(
        source="movements",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Invoice
        fields = (
            "id",
            "number",
            "invoice_type",
            "customer_name",
            "customer_id_number",
            "customer_email",
            "customer_phone",
            "customer_address",
            "subtotal",
            "discount_total",
            "tax_total",
            "total_amount",
            "currency",
            "pdf",
            "issued_by",
            "issued_by_username",
            "issued_at",
            "is_voided",
            "void_reason",
            "voided_at",
            "voided_by",
            "voided_by_username",
            "movements_detail",
        )
        read_only_fields = fields


class InvoiceListSerializer(serializers.ModelSerializer):
    """Resumen de factura para GET /billing/invoices/."""

    issued_by_username = serializers.CharField(
        source="issued_by.username", read_only=True
    )
    item_count = serializers.SerializerMethodField()

    def get_item_count(self, obj) -> int:
        # Prefetched en la queryset de la view
        if (
            hasattr(obj, "_prefetched_objects_cache")
            and "movements" in obj._prefetched_objects_cache
        ):
            return len(obj._prefetched_objects_cache["movements"])
        return obj.movements.count()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "number",
            "invoice_type",
            "customer_name",
            "customer_id_number",
            "total_amount",
            "currency",
            "issued_by_username",
            "issued_at",
            "is_voided",
            "item_count",
        )
        read_only_fields = fields


class InvoiceStatsSerializer(serializers.Serializer):
    """Respuesta de GET /billing/invoices/stats/."""

    total_sales_today = serializers.DecimalField(max_digits=18, decimal_places=4)
    total_sales_month = serializers.DecimalField(max_digits=18, decimal_places=4)
    invoice_count_today = serializers.IntegerField()
    invoice_count_month = serializers.IntegerField()


class CompanyInfoSerializer(serializers.Serializer):
    """GET/PUT /billing/config/company/."""

    id = serializers.IntegerField(read_only=True)
    company_name = serializers.CharField(max_length=200)
    nit = serializers.CharField(max_length=50, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    dian_resolution = serializers.CharField(required=False, allow_blank=True)
    dian_range_from = serializers.IntegerField(required=False, allow_null=True)
    dian_range_to = serializers.IntegerField(required=False, allow_null=True)
    invoice_series = serializers.CharField(max_length=10, required=False)
    invoice_footer = serializers.CharField(required=False, allow_blank=True)
    updated_at = serializers.DateTimeField(read_only=True)
