"""Serializers del módulo de compras."""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    PurchaseOrder,
    PurchaseOrderItem,
    Reception,
    ReceptionItem,
    ReceptionItemAllocation,
    Supplier,
)

# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = (
            "id",
            "nombre_comercial",
            "razon_social",
            "nit",
            "pais",
            "correo",
            "telefono",
            "ciudad",
            "direccion",
            "is_active",
            "observaciones",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class SupplierWriteSerializer(serializers.Serializer):
    nombre_comercial = serializers.CharField(max_length=200)
    razon_social = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    nit = serializers.CharField(
        max_length=20, required=False, allow_blank=True, allow_null=True
    )
    pais = serializers.CharField(max_length=100, required=True)
    correo = serializers.EmailField(required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=300, required=False, allow_blank=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)


# ---------------------------------------------------------------------------
# PurchaseOrderItem
# ---------------------------------------------------------------------------


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    quantity_pending = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderItem
        fields = (
            "id",
            "product",
            "product_name",
            "product_sku",
            "quantity_ordered",
            "quantity_received",
            "quantity_pending",
            "unit_cost",
            "notes",
        )
        read_only_fields = ("id", "quantity_received")

    def get_quantity_pending(self, obj) -> int:
        return obj.quantity_pending


class PurchaseOrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity_ordered = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=4)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


# ---------------------------------------------------------------------------
# PurchaseOrder
# ---------------------------------------------------------------------------


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_nombre = serializers.CharField(
        source="supplier.nombre_comercial", read_only=True
    )
    supplier_nit = serializers.CharField(source="supplier.nit", read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id",
            "number",
            "supplier",
            "supplier_nombre",
            "supplier_nit",
            "status",
            "expected_delivery",
            "notes",
            "items",
            "created_by",
            "confirmed_by",
            "confirmed_at",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "number",
            "status",
            "confirmed_by",
            "confirmed_at",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
            "updated_at",
        )


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField()
    expected_delivery = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = PurchaseOrderItemWriteSerializer(many=True, allow_empty=False)


class PurchaseOrderUpdateSerializer(serializers.Serializer):
    expected_delivery = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = PurchaseOrderItemWriteSerializer(many=True, required=False)


class POCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5)


# ---------------------------------------------------------------------------
# ReceptionItem
# ---------------------------------------------------------------------------


class ReceptionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="purchase_order_item.product.name", read_only=True
    )
    product_sku = serializers.CharField(
        source="purchase_order_item.product.sku", read_only=True
    )
    quantity_expected = serializers.SerializerMethodField()
    movement_id = serializers.UUIDField(
        source="movement.id", read_only=True, allow_null=True
    )
    allocations = serializers.SerializerMethodField()

    class Meta:
        model = ReceptionItem
        fields = (
            "id",
            "purchase_order_item",
            "product_name",
            "product_sku",
            "quantity_expected",
            "quantity_received",
            "lot_code",
            "lot_expiration_date",
            "serial_number",
            "discrepancy_note",
            "movement_id",
            "allocations",
        )
        read_only_fields = ("id", "movement_id")

    def get_quantity_expected(self, obj) -> int:
        return obj.quantity_expected

    def get_allocations(self, obj):
        return ReceptionItemAllocationSerializer(obj.allocations.all(), many=True).data


class ReceptionItemAllocationSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.name", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)
    movement_id = serializers.UUIDField(
        source="movement.id", read_only=True, allow_null=True
    )

    class Meta:
        model = ReceptionItemAllocation
        fields = (
            "id",
            "location",
            "location_code",
            "location_name",
            "quantity_received",
            "lot_code",
            "lot_expiration_date",
            "serial_number",
            "movement_id",
        )
        read_only_fields = ("id", "movement_id")


class ReceptionItemAllocationWriteSerializer(serializers.Serializer):
    location_id = serializers.UUIDField()
    quantity_received = serializers.IntegerField(min_value=1)
    lot_code = serializers.CharField(required=False, allow_blank=True, default="")
    lot_expiration_date = serializers.DateField(required=False, allow_null=True)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class ReceptionItemWriteSerializer(serializers.Serializer):
    purchase_order_item_id = serializers.UUIDField()
    quantity_received = serializers.IntegerField(min_value=0)
    lot_code = serializers.CharField(required=False, allow_blank=True, default="")
    lot_expiration_date = serializers.DateField(required=False, allow_null=True)
    serial_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    discrepancy_note = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    allocations = ReceptionItemAllocationWriteSerializer(
        many=True,
        required=False,
        default=list,
        help_text=(
            "Distribución avanzada opcional. Cada fila puede indicar ubicación, lote "
            "y cantidad."
        ),
    )


# ---------------------------------------------------------------------------
# Reception
# ---------------------------------------------------------------------------


class ReceptionSerializer(serializers.ModelSerializer):
    po_number = serializers.CharField(source="purchase_order.number", read_only=True)
    supplier_nombre = serializers.CharField(
        source="purchase_order.supplier.nombre_comercial", read_only=True
    )
    location_name = serializers.CharField(
        source="destination_location.name", read_only=True
    )
    items = ReceptionItemSerializer(many=True, read_only=True)
    has_allocations = serializers.SerializerMethodField()

    class Meta:
        model = Reception
        fields = (
            "id",
            "purchase_order",
            "po_number",
            "supplier_nombre",
            "status",
            "destination_location",
            "location_name",
            "received_by",
            "confirmed_at",
            "notes",
            "has_allocations",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "received_by",
            "confirmed_at",
            "created_at",
            "updated_at",
        )

    def get_has_allocations(self, obj) -> bool:
        return any(
            getattr(item, "allocations", None) and item.allocations.exists()
            for item in obj.items.all()
        )


class ReceptionCreateSerializer(serializers.Serializer):
    po_id = serializers.UUIDField()
    destination_location_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = ReceptionItemWriteSerializer(many=True, allow_empty=False)
