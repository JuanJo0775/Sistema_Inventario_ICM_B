"""Serializers de catálogo (RF-003)."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Category, ComboItem, Product, ProductCombo, Subcategory


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
            "weight_grams",
            "requires_cold_chain",
            "is_active",
            "notes",
            "reorder_point",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "category_slug")


class ProductCreateSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    category_id = serializers.UUIDField()
    subcategory_id = serializers.UUIDField(required=False, allow_null=True)
    barcode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    brand = serializers.CharField(default="Can")
    requires_cold_chain = serializers.BooleanField(default=False)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    weight_grams = serializers.IntegerField(required=False, allow_null=True, min_value=0)
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
        fields = ("id", "name", "sku", "is_active", "components", "created_at", "updated_at")


class ResolveIdentifierQuerySerializer(serializers.Serializer):
    q = serializers.CharField()
