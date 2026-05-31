"""Serializers de inventario (RF-004)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from apps.catalog.serializers import ProductSerializer
from apps.inventory.models import (
    Location,
    StockByLocation,
    StorageTemplate,
    StorageType,
)


class StorageTypeCreateSerializer(serializers.Serializer):
    code = serializers.SlugField()
    name = serializers.CharField()
    category = serializers.CharField(
        required=False, allow_blank=True, default="general"
    )
    description = serializers.CharField(required=False, allow_blank=True, default="")
    capabilities = serializers.JSONField(required=False, default=dict)
    default_is_retail = serializers.BooleanField(required=False, default=False)
    is_system = serializers.BooleanField(required=False, default=False)
    sort_order = serializers.IntegerField(required=False, min_value=0, default=0)


class StorageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageType
        fields = (
            "id",
            "code",
            "name",
            "category",
            "description",
            "capabilities",
            "default_is_retail",
            "is_system",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )


class StorageTemplateCreateSerializer(serializers.Serializer):
    code = serializers.SlugField()
    name = serializers.CharField()
    storage_type_id = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    defaults = serializers.JSONField(required=False, default=dict)
    is_system = serializers.BooleanField(required=False, default=False)
    sort_order = serializers.IntegerField(required=False, min_value=0, default=0)


class StorageTemplateSerializer(serializers.ModelSerializer):
    storage_type_id = serializers.UUIDField(required=False, allow_null=True)
    storage_type_code = serializers.CharField(
        source="storage_type.code", read_only=True
    )
    storage_type_name = serializers.CharField(
        source="storage_type.name", read_only=True
    )

    class Meta:
        model = StorageTemplate
        fields = (
            "id",
            "code",
            "name",
            "storage_type_id",
            "storage_type_code",
            "storage_type_name",
            "description",
            "defaults",
            "is_system",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )


class LocationCreateSerializer(serializers.Serializer):
    """Serializador de entrada para crear una ubicación (sin code, sin enum)."""

    name = serializers.CharField(
        help_text="Nombre de la ubicación (ej. 'Vitrina', 'Bodega Central')."
    )
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
    storage_type_id = serializers.UUIDField(required=False, allow_null=True)
    storage_template_id = serializers.UUIDField(required=False, allow_null=True)
    operational_status = serializers.ChoiceField(
        choices=Location.OperationalStatus.choices,
        required=False,
        default=Location.OperationalStatus.ACTIVE,
    )
    capacity_mode = serializers.ChoiceField(
        choices=Location.CapacityMode.choices,
        required=False,
        default=Location.CapacityMode.NONE,
    )
    capacity_level = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=5
    )
    capacity_score = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )
    occupancy_estimate_pct = serializers.FloatField(
        required=False, allow_null=True, min_value=0.0, max_value=100.0
    )


class LocationSerializer(serializers.ModelSerializer):
    storage_type_id = serializers.UUIDField(required=False, allow_null=True)
    storage_type_code = serializers.CharField(
        source="storage_type.code", read_only=True
    )
    storage_type_name = serializers.CharField(
        source="storage_type.name", read_only=True
    )
    storage_template_id = serializers.UUIDField(required=False, allow_null=True)
    storage_template_code = serializers.CharField(
        source="storage_template.code", read_only=True
    )
    storage_template_name = serializers.CharField(
        source="storage_template.name", read_only=True
    )

    class Meta:
        model = Location
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_retail",
            "max_capacity",
            "storage_type_id",
            "storage_type_code",
            "storage_type_name",
            "storage_template_id",
            "storage_template_code",
            "storage_template_name",
            "operational_status",
            "capacity_mode",
            "capacity_level",
            "capacity_score",
            "occupancy_estimate_pct",
            "is_active",
            "created_at",
            "updated_at",
        )


class LocationStateTransitionSerializer(serializers.Serializer):
    operational_status = serializers.ChoiceField(
        choices=Location.OperationalStatus.choices
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
    storage_type_id = serializers.CharField(required=False, allow_null=True)
    storage_type_code = serializers.CharField(required=False, allow_null=True)
    storage_template_id = serializers.CharField(required=False, allow_null=True)
    storage_template_code = serializers.CharField(required=False, allow_null=True)
    operational_status = serializers.CharField(required=False)
    capacity_mode = serializers.CharField(required=False)
    capacity_level = serializers.IntegerField(required=False, allow_null=True)
    capacity_score = serializers.IntegerField(required=False, allow_null=True)
    occupancy_estimate_pct = serializers.FloatField(required=False, allow_null=True)
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
