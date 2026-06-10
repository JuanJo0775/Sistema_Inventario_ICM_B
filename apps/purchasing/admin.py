"""Registro administrativo del módulo de compras."""

from django.contrib import admin

from .models import (
    PurchaseOrder,
    PurchaseOrderCounter,
    PurchaseOrderItem,
    Reception,
    ReceptionItem,
    ReceptionItemAllocation,
    Supplier,
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("nombre_comercial", "nit", "is_active", "ciudad", "created_at")
    list_filter = ("is_active",)
    search_fields = ("nombre_comercial", "nit", "razon_social")
    readonly_fields = ("id", "created_at", "updated_at")


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ("id", "quantity_received", "created_at", "updated_at")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "supplier", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "supplier__nombre_comercial", "supplier__nit")
    readonly_fields = (
        "id",
        "number",
        "confirmed_by",
        "confirmed_at",
        "cancelled_by",
        "cancelled_at",
        "created_at",
        "updated_at",
    )
    inlines = [PurchaseOrderItemInline]


class ReceptionItemInline(admin.TabularInline):
    model = ReceptionItem
    extra = 0
    readonly_fields = ("id", "movement", "created_at", "updated_at")


class ReceptionItemAllocationInline(admin.TabularInline):
    model = ReceptionItemAllocation
    extra = 0
    readonly_fields = ("id", "movement", "created_at", "updated_at")


@admin.register(ReceptionItemAllocation)
class ReceptionItemAllocationAdmin(admin.ModelAdmin):
    list_display = (
        "reception_item",
        "location",
        "quantity_received",
        "lot_code",
        "lot_expiration_date",
        "movement",
        "created_at",
    )
    search_fields = (
        "reception_item__purchase_order_item__product__sku",
        "reception_item__reception__purchase_order__number",
        "location__code",
        "lot_code",
    )
    readonly_fields = ("id", "movement", "created_at", "updated_at")


@admin.register(Reception)
class ReceptionAdmin(admin.ModelAdmin):
    list_display = ("id", "purchase_order", "status", "received_by", "confirmed_at")
    list_filter = ("status",)
    search_fields = ("purchase_order__number",)
    readonly_fields = ("id", "confirmed_at", "created_at", "updated_at")
    inlines = [ReceptionItemInline]


@admin.register(PurchaseOrderCounter)
class PurchaseOrderCounterAdmin(admin.ModelAdmin):
    list_display = ("pk", "last_number")
