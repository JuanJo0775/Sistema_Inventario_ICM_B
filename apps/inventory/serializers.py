"""Serializers de inventario (RF-004)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from apps.catalog.serializers import ProductSerializer
from apps.inventory.models import Location, StockByLocation


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_retail",
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
    location_id = serializers.CharField()
    location_code = serializers.CharField()
    quantity = serializers.IntegerField()


class StockByProductResponseSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    per_location = PerLocationStockRowSerializer(many=True)
    total = serializers.IntegerField()


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
