from django.contrib import admin

from apps.movements.models import InvoiceCounter, Movement


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "movement_type",
        "product",
        "quantity",
        "executed_by",
        "created_at",
    )
    readonly_fields = [f.name for f in Movement._meta.fields]


@admin.register(InvoiceCounter)
class InvoiceCounterAdmin(admin.ModelAdmin):
    list_display = ("id", "last_number")
