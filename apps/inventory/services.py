"""Servicios de inventario: interfaz pública para stock derivado (RF-004, BR-11)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from django.db import transaction

if TYPE_CHECKING:
    from apps.inventory.models import StockByLocation


def get_current_stock(product_id: UUID, location_id: UUID) -> int:
    """
    RF-004 — Cantidad actual en caché `StockByLocation` para producto/ubicación.

    Nota: el valor proviene del stock derivado; la verdad operativa es el ledger.
    """
    from apps.inventory.models import StockByLocation

    row = StockByLocation.objects.filter(product_id=product_id, location_id=location_id).first()
    return int(row.current_stock) if row else 0


@transaction.atomic
def ensure_stock_row_for_tests(product_id: UUID, location_id: UUID, quantity: int) -> StockByLocation:
    """Utilidad interna para pruebas y cargas controladas (no usar en producción desde vistas)."""
    from apps.inventory.models import StockByLocation

    row, _ = StockByLocation.objects.select_for_update().get_or_create(
        product_id=product_id,
        location_id=location_id,
        defaults={"current_stock": quantity},
    )
    if row.current_stock != quantity:
        row.current_stock = quantity
        row.save(update_fields=["current_stock", "updated_at"])
    return row
