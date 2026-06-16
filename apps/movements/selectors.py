"""Consultas de solo lectura del ledger (RF-005–RF-009, RF-010)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from django.db.models import QuerySet

from apps.movements.models import Movement, MovementType


def _movement_base_qs() -> QuerySet[Movement]:
    return Movement.objects.select_related(
        "product",
        "lot",
        "product__category",
        "executed_by",
        "origin_location",
        "destination_location",
    )


def get_movement_by_id(movement_id: UUID) -> Movement:
    """
    RF-005–RF-009 — Detalle de movimiento con relaciones.

    Raises:
        Movement.DoesNotExist: Si no existe el id.
    """
    return _movement_base_qs().get(pk=movement_id)


def get_movements_by_product(
    product_id: UUID, filters: dict[str, Any] | None = None
) -> QuerySet[Movement]:
    """
    RF-005–RF-009 — Movimientos de un producto con filtros opcionales.

    Args:
        product_id: UUID del producto.
        filters: `movement_type` opcional.
    """
    filters = filters or {}
    qs = _movement_base_qs().filter(product_id=product_id)
    if mt := filters.get("movement_type"):
        qs = qs.filter(movement_type=mt)
    return qs.order_by("-created_at")


def get_movements_by_user(
    user_id: int, filters: dict[str, Any] | None = None
) -> QuerySet[Movement]:
    """
    RF-012 — Movimientos ejecutados por un usuario.

    Args:
        user_id: PK del usuario ejecutor.
        filters: `movement_type` opcional.
    """
    filters = filters or {}
    qs = _movement_base_qs().filter(executed_by_id=user_id)
    if mt := filters.get("movement_type"):
        qs = qs.filter(movement_type=mt)
    return qs.order_by("-created_at")


def get_movements_by_period(
    start: datetime,
    end: datetime,
    filters: dict[str, Any] | None = None,
) -> QuerySet[Movement]:
    """
    RF-010 — Movimientos en rango de fechas.

    Args:
        start: Inicio inclusive.
        end: Fin inclusive.
        filters: `movement_type`, `product_id`, `user_id` opcionales.
    """
    filters = filters or {}
    qs = _movement_base_qs().filter(created_at__gte=start, created_at__lte=end)
    if mt := filters.get("movement_type"):
        qs = qs.filter(movement_type=mt)
    if pid := filters.get("product_id"):
        qs = qs.filter(product_id=pid)
    if uid := filters.get("user_id"):
        qs = qs.filter(executed_by_id=uid)
    return qs.order_by("-created_at")


def get_dispatches_with_invoices() -> QuerySet[Movement]:
    """
    RF-010, BR-13 — Salidas con número de factura asignado (para reportes).

    Returns:
        QuerySet de movimientos tipo salida con `invoice_number` no nulo.
    """
    salidas = (
        MovementType.SALIDA_VENTA_MAYOR,
        MovementType.SALIDA_VENTA_MENOR,
        MovementType.SALIDA_DANO,
        MovementType.SALIDA_VENCIMIENTO,
    )
    return (
        _movement_base_qs()
        .filter(movement_type__in=salidas)
        .exclude(invoice_number__isnull=True)
        .exclude(invoice_number__exact="")
        .order_by("-created_at")
    )
