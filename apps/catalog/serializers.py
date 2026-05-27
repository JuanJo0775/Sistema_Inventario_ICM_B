"""Serializers de catálogo (RF-003)."""

from __future__ import annotations

from uuid import UUID

from rest_framework import serializers

from apps.catalog.models import (Category, ComboItem, Product, ProductCombo,
                                 Subcategory)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "requires_serial_number",
            "is_returnable",
            "description",
            "created_at",
            "updated_at",
        )


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ("id", "category", "name", "slug", "created_at", "updated_at")


class ProductSerializer(serializers.ModelSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "category",
            "category_slug",
            "subcategory",
            "barcode",
            "brand",
            "expiration_date",
            "requires_expiration",
            "weight_grams",
            "requires_cold_chain",
            "is_active",
            "notes",
            "reorder_point",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "category_slug")


class ProductUpdateSerializer(serializers.Serializer):
    """Campos opcionales para actualización parcial (RF-003)."""

    name = serializers.CharField(required=False)
    sku = serializers.CharField(required=False)
    category_id = serializers.UUIDField(required=False)
    subcategory_id = serializers.UUIDField(required=False, allow_null=True)
    barcode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    brand = serializers.CharField(required=False, allow_blank=True)
    requires_cold_chain = serializers.BooleanField(required=False)
    requires_expiration = serializers.BooleanField(required=False)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    weight_grams = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    reorder_point = serializers.IntegerField(required=False, min_value=0)
    is_active = serializers.BooleanField(required=False)


class ProductCreateSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    category_id = serializers.UUIDField()
    subcategory_id = serializers.UUIDField(required=False, allow_null=True)
    barcode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    brand = serializers.CharField(default="Can")
    requires_cold_chain = serializers.BooleanField(default=False)
    requires_expiration = serializers.BooleanField(default=False)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    weight_grams = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    reorder_point = serializers.IntegerField(required=False, default=0, min_value=0)
    is_active = serializers.BooleanField(required=False, default=True)


class ComboItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComboItem
        fields = ("id", "product", "quantity")


class ComboSerializer(serializers.ModelSerializer):
    components = ComboItemSerializer(many=True, read_only=True, source="combo_items")

    class Meta:
        model = ProductCombo
        fields = (
            "id",
            "name",
            "sku",
            "is_active",
            "components",
            "created_at",
            "updated_at",
        )


class ResolveIdentifierQuerySerializer(serializers.Serializer):
    """Acepta `q` o `identifier` (BR-13, RF-003)."""

    q = serializers.CharField(required=False, allow_blank=True)
    identifier = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        raw = (attrs.get("q") or attrs.get("identifier") or "").strip()
        if not raw:
            raise serializers.ValidationError(
                "Indique el parámetro de consulta `q` o `identifier`."
            )
        attrs["_value"] = raw
        return attrs


class ComboCreateItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(help_text="UUID del producto")
    quantity = serializers.IntegerField(default=1, min_value=1, help_text="Cantidad del producto en el combo")


class ComboCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    sku = serializers.CharField()
    is_active = serializers.BooleanField(required=False, default=True)
    items = ComboCreateItemSerializer(many=True, allow_empty=False)


class CategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    requires_serial_number = serializers.BooleanField(required=False, default=False)
    is_returnable = serializers.BooleanField(required=False, default=False)


class SubcategoryCreateSerializer(serializers.Serializer):
    category_id = serializers.UUIDField()
    name = serializers.CharField()
