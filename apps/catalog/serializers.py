"""Serializers de catálogo (RF-003)."""

from __future__ import annotations

from uuid import UUID

from rest_framework import serializers

from apps.catalog.models import (Category, ComboItem, Product, ProductCombo,
                                 Subcategory)
from shared.utils.barcode import build_product_barcode_payload


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
    barcode_type = serializers.SerializerMethodField()

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
            "barcode_type",
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
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "category_slug",
            "barcode_type",
        )

    def get_barcode_type(self, obj: Product) -> str | None:
        return "Code128" if obj.barcode else None


class ProductDetailSerializer(ProductSerializer):
    barcode_svg = serializers.SerializerMethodField()
    barcode_svg_data_uri = serializers.SerializerMethodField()
    barcode_payload = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + (
            "barcode_svg",
            "barcode_svg_data_uri",
            "barcode_payload",
        )

    def get_barcode_payload(self, obj: Product) -> dict[str, str] | None:
        if not obj.barcode:
            return None
        payload = self._get_cached_barcode_payload(obj)
        return {
            "type": payload["type"],
            "value": payload["value"],
        }

    def get_barcode_svg(self, obj: Product) -> str | None:
        if not obj.barcode:
            return None
        return self._get_cached_barcode_payload(obj)["svg"]

    def get_barcode_svg_data_uri(self, obj: Product) -> str | None:
        if not obj.barcode:
            return None
        return self._get_cached_barcode_payload(obj)["svg_data_uri"]

    def _get_cached_barcode_payload(self, obj: Product) -> dict[str, str]:
        cache_attr = "_barcode_payload_cache"
        payload = getattr(obj, cache_attr, None)
        if payload is None:
            payload = build_product_barcode_payload(obj.id, barcode=obj.barcode)
            setattr(obj, cache_attr, payload)
        return payload


class ProductBarcodeSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    sku = serializers.CharField()
    name = serializers.CharField()
    barcode = serializers.CharField()
    barcode_type = serializers.CharField()
    barcode_svg = serializers.CharField()
    barcode_svg_data_uri = serializers.CharField()
    render_format = serializers.CharField()

    @classmethod
    def from_product(cls, product: Product) -> dict[str, str]:
        payload = build_product_barcode_payload(product.id, barcode=product.barcode)
        return {
            "product_id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "barcode": payload["value"],
            "barcode_type": payload["type"],
            "barcode_svg": payload["svg"],
            "barcode_svg_data_uri": payload["svg_data_uri"],
            "render_format": "svg",
        }


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
