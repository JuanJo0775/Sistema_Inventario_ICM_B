from django.contrib import admin

from apps.inventory.models import Location, StockByLocation


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_retail", "is_active")


@admin.register(StockByLocation)
class StockByLocationAdmin(admin.ModelAdmin):
    """
    RF-004, BR-11 — Stock derivado solo lectura en Admin.

    La mutación del inventario ocurre únicamente vía movimientos (`Movement`), no editando caché.
    """

    list_display = ("product", "location", "current_stock", "last_movement_at", "created_at")
    readonly_fields = ("id", "product", "location", "current_stock", "last_movement_at", "created_at", "updated_at")

    def has_add_permission(self, request):  # noqa: ANN001 — firma Django Admin API
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: ANN001
        return False
