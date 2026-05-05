"""Reportes y KPIs de solo lectura (RF-010)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from django.db.models import Count, Sum
from django.utils import timezone

from apps.alerts.models import Alert
from apps.catalog.models import Category, Product
from apps.catalog.selectors import get_products_expiring_soon
from apps.inventory.selectors import get_low_stock_products
from apps.movements.models import Movement, MovementType
from apps.movements.selectors import get_dispatches_with_invoices


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


def movement_history(
    *,
    product_id: UUID | str | None = None,
    user_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
):
    """RF-010 — Historial filtrable (QuerySet lazy)."""
    qs = Movement.objects.all().select_related("product", "executed_by")
    if product_id:
        qs = qs.filter(product_id=UUID(str(product_id)))
    if user_id is not None:
        qs = qs.filter(executed_by_id=user_id)
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lte=end)
    return qs.order_by("-created_at")


def rotation_by_category(*, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """RF-010 — Rotación aproximada por categoría (unidades movidas / período)."""
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


def get_inventory_summary() -> dict[str, Any]:
    """
    RF-010 — Resumen de inventario por categoría y productos sin stock.

    Valor aproximado: no hay precio en catálogo; se devuelve nota y conteos.
    """
    from apps.inventory.models import StockByLocation

    by_category: list[dict[str, Any]] = []
    for cat in Category.objects.all():
        total = (
            StockByLocation.objects.filter(product__category=cat).aggregate(s=Sum("current_stock"))["s"] or 0
        )
        by_category.append({"category_id": str(cat.id), "category": cat.name, "total_units": int(total)})
    zero_stock = (
        Product.objects.filter(is_active=True)
        .annotate(t=Sum("stock_by_location__current_stock"))
        .filter(t=0)
        .count()
    )
    return {
        "by_category": by_category,
        "products_with_zero_stock": zero_stock,
        "approximate_value": None,
        "approximate_value_note": "El catálogo no almacena precio unitario (ICM).",
    }


def get_movement_report(
    start: datetime,
    end: datetime,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    RF-010 — Agregados de movimientos en el período por tipo, producto y usuario.

    Args:
        start: Inicio del rango.
        end: Fin del rango.
        filters: `type` opcional (`movement_type`).
    """
    filters = filters or {}
    qs = Movement.objects.filter(created_at__gte=start, created_at__lte=end)
    if mtype := filters.get("type"):
        qs = qs.filter(movement_type=mtype)
    counts = {row["movement_type"]: row["c"] for row in qs.values("movement_type").annotate(c=Count("id"))}
    by_product = list(
        qs.values("product__sku", "product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:100]
    )
    by_user = list(qs.values("executed_by__username").annotate(movements=Count("id")).order_by("-movements")[:50])
    return {
        "counts": counts,
        "by_product": by_product,
        "by_user": by_user,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
    }


def get_top_dispatched_products(limit: int = 10, period_days: int = 30) -> list[dict[str, Any]]:
    """RF-010 — Productos más despachados (salidas) en ventana de días."""
    end = timezone.now()
    start = end - timedelta(days=period_days)
    salidas = (
        MovementType.SALIDA_VENTA_MAYOR,
        MovementType.SALIDA_VENTA_MENOR,
        MovementType.SALIDA_DANO,
        MovementType.SALIDA_VENCIMIENTO,
    )
    return list(
        Movement.objects.filter(created_at__gte=start, created_at__lte=end, movement_type__in=salidas)
        .values("product_id", "product__sku", "product__name")
        .annotate(units=Sum("quantity"))
        .order_by("-units")[:limit]
    )


def get_invoice_history(
    filters: dict[str, Any] | None = None,
    *,
    include_customer_metadata: bool = False,
):
    """
    RF-010, BR-13 — Movimientos con factura.

    Los datos personales de cliente mayorista no están en `Movement`; viven en auditoría
    (`AuditLog.metadata`). `include_customer_metadata` reserva el contrato Ley 1581 para
    vistas que enlacen con auditoría.

    Args:
        filters: `start`, `end`, `invoice_number`, `product_id` opcionales.
        include_customer_metadata: Reservado (Ley 1581); no altera el QuerySet base.

    Returns:
        QuerySet de `Movement` con relaciones cargadas.
    """
    del include_customer_metadata  # API estable; enlace a auditoría en capa de vista si aplica.
    filters = filters or {}
    qs = get_dispatches_with_invoices().select_related("product", "executed_by", "origin_location")
    if start := filters.get("start"):
        qs = qs.filter(created_at__gte=start)
    if end := filters.get("end"):
        qs = qs.filter(created_at__lte=end)
    if inv := filters.get("invoice_number"):
        qs = qs.filter(invoice_number__icontains=inv)
    if pid := filters.get("product_id"):
        qs = qs.filter(product_id=pid)
    return qs


def get_expiring_products(days: int = 30):
    """RF-010, RF-011 — Productos que vencen en los próximos `days` días."""
    return get_products_expiring_soon(days=days)


def get_kpi_dashboard() -> dict[str, Any]:
    """RF-010 — KPIs operativos para panel administrativo."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    salidas = (
        MovementType.SALIDA_VENTA_MAYOR,
        MovementType.SALIDA_VENTA_MENOR,
        MovementType.SALIDA_DANO,
        MovementType.SALIDA_VENCIMIENTO,
    )
    return {
        "movements_today": Movement.objects.filter(created_at__gte=today_start).count(),
        "low_stock_products_count": get_low_stock_products(threshold=5).count(),
        "active_alerts_unresolved": Alert.objects.filter(is_resolved=False).count(),
        "dispatches_this_month": Movement.objects.filter(
            created_at__gte=month_start,
            movement_type__in=salidas,
        ).count(),
        "generated_at": now.isoformat(),
    }
