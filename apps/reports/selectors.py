"""Reportes y KPIs de solo lectura (RF-010)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from apps.movements.models import Movement, MovementType


def movement_counts_by_period(*, start: datetime, end: datetime) -> dict[str, int]:
    """RF-010 — Conteo de movimientos por tipo en un rango temporal."""
    qs = (
        Movement.objects.filter(created_at__gte=start, created_at__lte=end)
        .values("movement_type")
        .annotate(c=Count("id"))
    )
    return {row["movement_type"]: row["c"] for row in qs}


def sales_dispatch_totals(*, start: datetime, end: datetime) -> dict[str, Any]:
    """RF-010 — Totales de salidas de venta en el período."""
    filt = Movement.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        movement_type__in=[MovementType.SALIDA_VENTA_MAYOR, MovementType.SALIDA_VENTA_MENOR],
    )
    return {
        "mayor": filt.filter(movement_type=MovementType.SALIDA_VENTA_MAYOR).aggregate(q=Sum("quantity"))["q"] or 0,
        "menor": filt.filter(movement_type=MovementType.SALIDA_VENTA_MENOR).aggregate(q=Sum("quantity"))["q"] or 0,
    }


def movement_history(*, product_id: int | None = None, user_id: int | None = None, start=None, end=None):
    """RF-010 — Historial filtrable ( queryset lazy )."""
    qs = Movement.objects.all().select_related("product", "executed_by")
    if product_id:
        qs = qs.filter(product_id=product_id)
    if user_id:
        qs = qs.filter(executed_by_id=user_id)
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lte=end)
    return qs.order_by("-created_at")


def rotation_by_category(*, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """RF-010 — Rotación aproximada por categoría (unidades movidas / período)."""
    from apps.catalog.models import Category

    rows = []
    for cat in Category.objects.all():
        qty = (
            Movement.objects.filter(
                created_at__gte=start,
                created_at__lte=end,
                product__category=cat,
            ).aggregate(q=Sum("quantity"))["q"]
            or 0
        )
        rows.append({"category": cat.name, "units": int(qty)})
    return rows


def discrepancies_summary(*, start: datetime, end: datetime) -> int:
    """RF-010 — Movimientos con nota de discrepancia en recepción."""
    return Movement.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        movement_type=MovementType.ENTRADA,
    ).exclude(discrepancy_note__isnull=True).exclude(discrepancy_note__exact="").count()
