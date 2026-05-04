from django.contrib import admin

from apps.inventory.models import Location, StockByLocation


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_retail", "is_active")


@admin.register(StockByLocation)
class StockByLocationAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "current_stock", "last_movement_at")
