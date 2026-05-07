"""Serializers de inventario (RF-004)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from apps.catalog.serializers import ProductSerializer
from apps.inventory.models import Location, StockByLocation


class LocationCreateSerializer(serializers.Serializer):
    """Serializador de entrada para crear una ubicación (sin code, sin enum)."""

    name = serializers.CharField(help_text="Nombre de la ubicación (ej. 'Vitrina', 'Bodega Central').")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    is_retail = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Si se omite, el sistema lo detecta automáticamente según el nombre.",
    )
    max_capacity = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Capacidad máxima de productos. Recomendado para vitrinas.",
    )



class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_retail",
            "max_capacity",
            "is_active",
            "created_at",
            "updated_at",
        )


class StockByLocationSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = StockByLocation
        fields = (
            "id",
            "product",
            "product_sku",
            "location",
            "current_stock",
            "last_movement_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PerLocationStockRowSerializer(serializers.Serializer):
    location_id = serializers.CharField(required=False)
    location_code = serializers.CharField()
    location_name = serializers.CharField(required=False)
    quantity = serializers.IntegerField()


class StockByProductResponseSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField(required=False)
    sku = serializers.CharField(required=False)
    by_location = PerLocationStockRowSerializer(many=True, required=False)
    per_location = PerLocationStockRowSerializer(many=True)
    total = serializers.IntegerField()


class StockReconstructRequestSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    location_id = serializers.UUIDField()


class StockReconstructResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    reconstructed = serializers.IntegerField()
    actual = serializers.IntegerField()


@extend_schema_serializer(component_name="InventoryPaginatedProductList")
class PaginatedProductListSerializer(serializers.Serializer):
    """Forma estándar DRF `PageNumberPagination` para listas de productos."""

    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True, required=False)
    previous = serializers.CharField(allow_null=True, required=False)
    results = ProductSerializer(many=True)


@extend_schema_serializer(component_name="InventoryPaginatedStockByLocationList")
class PaginatedStockByLocationListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True, required=False)
    previous = serializers.CharField(allow_null=True, required=False)
    results = StockByLocationSerializer(many=True)
