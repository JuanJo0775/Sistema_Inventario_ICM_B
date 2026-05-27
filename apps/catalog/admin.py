from django.contrib import admin

from apps.catalog.models import (Category, ComboItem, Lot, Product,
                                 ProductCombo, Subcategory)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "requires_serial_number", "is_returnable")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "brand",
        "requires_expiration",
        "is_active",
    )
    search_fields = ("sku", "name", "barcode")


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("product", "code", "expiration_date", "created_at")
    search_fields = ("code", "product__sku", "product__name")


class ComboItemInline(admin.TabularInline):
    model = ComboItem
    extra = 0


@admin.register(ProductCombo)
class ProductComboAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "is_active")
    inlines = [ComboItemInline]
