"""Servicios centrales del dashboard operacional y ownership de KPIs."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.cache import cache
from django.db.models import Count, F, Max, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.alerts.models import Alert, AlertType
from apps.catalog.models import Product
from apps.inventory.models import Location, StockByLocation
from apps.movements.models import Movement, MovementType

_SALES_MOVEMENT_TYPES = (
    MovementType.SALIDA_VENTA_MAYOR,
    MovementType.SALIDA_VENTA_MENOR,
)

_QUALITY_MOVEMENT_TYPES = (
    MovementType.SALIDA_DANO,
    MovementType.SALIDA_VENCIMIENTO,
    MovementType.DEVOLUCION,
)

_MOVEMENT_LABELS = {
    MovementType.ENTRADA: "Entrada",
    MovementType.SALIDA_VENTA_MAYOR: "Despacho mayor",
    MovementType.SALIDA_VENTA_MENOR: "Despacho menor",
    MovementType.SALIDA_DANO: "Salida por daño",
    MovementType.SALIDA_VENCIMIENTO: "Salida por vencimiento",
    MovementType.TRASLADO: "Traslado",
    MovementType.AJUSTE: "Ajuste",
    MovementType.DEVOLUCION: "Devolución",
    MovementType.SALIDA_COMBO: "Salida por combo",
}

_KPI_PRECISION_REAL = "real"
_KPI_PRECISION_PARTIAL = "partial"
_KPI_PRECISION_FUTURE = "future"
_METRICS_TTL_SECONDS = 120
_ALERTS_TTL_SECONDS = 120
_KPIS_TTL_SECONDS = 120
_MOVEMENTS_TTL_SECONDS = 60
_OVERVIEW_TTL_SECONDS = 60


def _window(period_days: int) -> tuple[Any, Any]:
    end = timezone.now()
    start = end - timedelta(days=period_days)
    return start, end


def _cache_key(prefix: str, *parts: object) -> str:
    suffix = ":".join(str(part) for part in parts)
    return f"dashboard:{prefix}:{suffix}"


def _cached(prefix: str, timeout: int, builder, *parts: object):
    return cache.get_or_set(_cache_key(prefix, *parts), builder, timeout)


def _revision_stamp() -> str:
    movement_stamp = Movement.objects.aggregate(last=Max("created_at"))["last"]
    alert_stamp = Alert.objects.aggregate(
        last_created=Max("created_at"), last_resolved=Max("resolved_at")
    )
    product_stamp = Product.objects.aggregate(last=Max("updated_at"))["last"]
    location_stamp = Location.objects.aggregate(last=Max("updated_at"))["last"]
    stock_stamp = StockByLocation.objects.aggregate(last=Max("updated_at"))["last"]
    parts = [
        movement_stamp.isoformat() if movement_stamp else "none",
        alert_stamp["last_created"].isoformat() if alert_stamp["last_created"] else "none",
        alert_stamp["last_resolved"].isoformat() if alert_stamp["last_resolved"] else "none",
        product_stamp.isoformat() if product_stamp else "none",
        location_stamp.isoformat() if location_stamp else "none",
        stock_stamp.isoformat() if stock_stamp else "none",
    ]
    return "|".join(parts)


def _sales_queryset(start, end):
    return Movement.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        movement_type__in=_SALES_MOVEMENT_TYPES,
    )


def _quality_queryset(start, end):
    return Movement.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        movement_type__in=_QUALITY_MOVEMENT_TYPES,
    )


def _reorder_product_count() -> int:
    return (
        Product.objects.filter(is_active=True, reorder_point__gt=0)
        .annotate(total_stock=Coalesce(Sum("stock_by_location__current_stock"), 0))
        .filter(total_stock__lte=F("reorder_point"))
        .count()
    )


def _stock_total() -> int:
    return int(
        StockByLocation.objects.aggregate(total=Coalesce(Sum("current_stock"), 0))["total"]
        or 0
    )


def _invoice_numbers(*, start, end) -> list[str]:
    return list(
        _sales_queryset(start, end)
        .exclude(invoice_number__isnull=True)
        .exclude(invoice_number__exact="")
        .values_list("invoice_number", flat=True)
        .distinct()
        .order_by("invoice_number")
    )


def _quality_rollup(*, period_days: int) -> dict[str, int]:
    start, end = _window(period_days)
    rows = list(
        _quality_queryset(start, end)
        .values("movement_type")
        .annotate(movements=Count("id"), units=Sum("quantity"))
    )

    damage_units = 0
    discard_units = 0
    return_units = 0
    quality_units = 0

    for row in rows:
        units = int(row["units"] or 0)
        quality_units += units
        if row["movement_type"] == MovementType.SALIDA_DANO:
            damage_units += units
        elif row["movement_type"] == MovementType.SALIDA_VENCIMIENTO:
            discard_units += units
        elif row["movement_type"] == MovementType.DEVOLUCION:
            return_units += units

    return {
        "quality_units": quality_units,
        "damage_units": damage_units,
        "discard_units": discard_units,
        "return_units": return_units,
    }


def _dispatch_rollup(*, period_days: int) -> dict[str, Any]:
    start, end = _window(period_days)
    sales_qs = _sales_queryset(start, end)
    shipments = sales_qs.count()
    invoice_linked_dispatches = (
        sales_qs.exclude(invoice_number__isnull=True)
        .exclude(invoice_number__exact="")
        .values("invoice_number")
        .distinct()
        .count()
    )
    invoice_linked_ratio = (
        round((invoice_linked_dispatches / shipments) * 100, 2) if shipments else 0.0
    )
    movement_counts = {
        row["movement_type"]: row["count"]
        for row in sales_qs.values("movement_type").annotate(count=Count("id"))
    }
    top_products = list(
        sales_qs.values("product_id", "product__sku", "product__name")
        .annotate(units=Sum("quantity"))
        .order_by("-units")[:10]
    )
    return {
        "start": start,
        "end": end,
        "shipments": shipments,
        "invoice_linked_dispatches": invoice_linked_dispatches,
        "invoice_linked_ratio": invoice_linked_ratio,
        "movement_counts": movement_counts,
        "top_products": top_products,
    }


def _warehouse_utilization() -> dict[str, Any]:
    configured_occupied = 0
    configured_capacity = 0
    unconfigured_occupied = 0
    configured_locations = 0
    unconfigured_locations = 0

    for location in Location.objects.filter(is_active=True).annotate(
        occupied_units=Coalesce(Sum("stock_items__current_stock"), 0)
    ):
        occupied_units = int(getattr(location, "occupied_units", 0) or 0)
        capacity_units = (
            int(location.max_capacity) if location.max_capacity is not None else None
        )
        capacity_configured = capacity_units is not None and capacity_units > 0

        if capacity_configured:
            configured_locations += 1
            configured_occupied += occupied_units
            configured_capacity += capacity_units
        else:
            unconfigured_locations += 1
            unconfigured_occupied += occupied_units

    overall_utilization_pct = (
        round((configured_occupied / configured_capacity) * 100, 2)
        if configured_capacity
        else None
    )
    return {
        "overall": {
            "occupied_units": configured_occupied,
            "capacity_units": configured_capacity,
            "utilization_pct": overall_utilization_pct,
            "configured_locations": configured_locations,
            "locations_without_capacity": unconfigured_locations,
            "unconfigured_occupied_units": unconfigured_occupied,
        }
    }


def build_dashboard_metrics(*, period_days: int = 30) -> dict[str, Any]:
    revision = _revision_stamp()

    def _builder() -> dict[str, Any]:
        start, end = _window(period_days)
        sales_today_start = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sales_today = _sales_queryset(sales_today_start, timezone.now()).count()
        invoice_numbers = _invoice_numbers(start=start, end=end)
        invoice_range = (
            f"{invoice_numbers[0]} - {invoice_numbers[-1]}" if invoice_numbers else None
        )
        return {
            "stock_total": _stock_total(),
            "dispatches_today": sales_today,
            "reorder_count": _reorder_product_count(),
            "invoices_issued": len(invoice_numbers),
            "invoice_range": invoice_range,
        }

    return _cached("metrics", _METRICS_TTL_SECONDS, _builder, period_days, revision)


def build_dashboard_alerts(*, period_days: int = 30, expiring_days: int = 30) -> dict[str, Any]:
    revision = _revision_stamp()

    def _builder() -> dict[str, Any]:
        start, end = _window(period_days)
        return {
            "active": Alert.objects.filter(is_resolved=False).count(),
            "reorder": Alert.objects.filter(
                is_resolved=False, alert_type=AlertType.LOW_STOCK
            ).count(),
            "expiring": Alert.objects.filter(
                is_resolved=False,
                alert_type__in=(AlertType.EXPIRATION_30, AlertType.EXPIRATION_60),
            ).count(),
            "expiring_days": expiring_days,
            "returns": Movement.objects.filter(
                created_at__gte=start,
                created_at__lte=end,
                movement_type=MovementType.DEVOLUCION,
            ).count(),
        }

    return _cached(
        "alerts",
        _ALERTS_TTL_SECONDS,
        _builder,
        period_days,
        expiring_days,
        revision,
    )


def build_dashboard_kpis(*, period_days: int = 30) -> dict[str, Any]:
    revision = _revision_stamp()

    def _builder() -> dict[str, Any]:
        quality = _quality_rollup(period_days=period_days)
        dispatch = _dispatch_rollup(period_days=period_days)
        warehouse = _warehouse_utilization()
        cold_chain_alerts = Alert.objects.filter(
            is_resolved=False, alert_type=AlertType.COLD_CHAIN_MISSING
        ).count()

        quality_denominator = quality["quality_units"] or 0

        def _ratio(numerator: int) -> float:
            return (
                round((numerator / quality_denominator) * 100, 2)
                if quality_denominator
                else 0.0
            )

        return {
            "warehouse_utilization": {
                "label": "Utilización de almacén",
                "value": warehouse["overall"]["utilization_pct"],
                "unit": "%",
                "precision": _KPI_PRECISION_REAL,
                "threshold": 85.0,
                "source": "apps.inventory.models.StockByLocation + Location.max_capacity",
            },
            "damaged_rate": {
                "label": "Índice de productos dañados",
                "value": _ratio(quality["damage_units"]),
                "unit": "%",
                "precision": _KPI_PRECISION_PARTIAL,
                "threshold": None,
                "source": "apps.movements.models.Movement (SALIDA_DANO)",
            },
            "return_rate": {
                "label": "Tasa de devoluciones",
                "value": _ratio(quality["return_units"]),
                "unit": "%",
                "precision": _KPI_PRECISION_PARTIAL,
                "threshold": None,
                "source": "apps.movements.models.Movement (DEVOLUCION)",
            },
            "dispatch_invoice_ratio": {
                "label": "Despachos con factura",
                "value": dispatch["invoice_linked_ratio"],
                "unit": "%",
                "precision": _KPI_PRECISION_PARTIAL,
                "threshold": None,
                "source": "apps.movements.models.Movement.invoice_number",
            },
            "discard_rate": {
                "label": "Tasa de descarte",
                "value": _ratio(quality["discard_units"]),
                "unit": "%",
                "precision": _KPI_PRECISION_PARTIAL,
                "threshold": None,
                "source": "apps.movements.models.Movement (SALIDA_DANO + SALIDA_VENCIMIENTO)",
            },
            "cold_chain_alerts": {
                "label": "Alertas de cadena de frío",
                "value": float(cold_chain_alerts),
                "unit": "alerts",
                "precision": _KPI_PRECISION_FUTURE,
                "threshold": 0.0,
                "source": "apps.alerts.models.Alert (COLD_CHAIN_MISSING)",
            },
        }

    return _cached("kpis", _KPIS_TTL_SECONDS, _builder, period_days, revision)


def build_dashboard_movements(*, period_days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    revision = _revision_stamp()

    def _builder() -> list[dict[str, Any]]:
        start, end = _window(period_days)
        rows = (
            Movement.objects.filter(created_at__gte=start, created_at__lte=end)
            .select_related("product", "executed_by")
            .order_by("-created_at")[:limit]
        )
        out: list[dict[str, Any]] = []
        for movement in rows:
            movement_type = movement.movement_type
            out.append(
                {
                    "id": str(movement.id),
                    "type": {
                        MovementType.ENTRADA: "in",
                        MovementType.SALIDA_VENTA_MAYOR: "out",
                        MovementType.SALIDA_VENTA_MENOR: "out",
                        MovementType.SALIDA_DANO: "discard",
                        MovementType.SALIDA_VENCIMIENTO: "discard",
                        MovementType.TRASLADO: "transfer",
                        MovementType.AJUSTE: "adjustment",
                        MovementType.DEVOLUCION: "return",
                        MovementType.SALIDA_COMBO: "out",
                    }.get(movement_type, "movement"),
                    "title": f"{_MOVEMENT_LABELS.get(movement_type, movement_type)} - {movement.product.name}",
                    "sku": movement.product.sku,
                    "quantity": int(movement.quantity),
                    "user": (
                        movement.executed_by.get_full_name().strip()
                        or movement.executed_by.get_username()
                    ),
                    "time": timezone.localtime(movement.created_at).strftime("%H:%M"),
                    "status": "pending"
                    if movement.movement_type in _SALES_MOVEMENT_TYPES
                    and not movement.invoice_number
                    else "ok",
                }
            )
        return out

    return _cached(
        "movements",
        _MOVEMENTS_TTL_SECONDS,
        _builder,
        period_days,
        limit,
        revision,
    )


def build_dashboard_overview(*, period_days: int = 30, movements_limit: int = 10) -> dict[str, Any]:
    revision = _revision_stamp()

    def _builder() -> dict[str, Any]:
        now = timezone.now()
        return {
            "metrics": build_dashboard_metrics(period_days=period_days),
            "alerts": build_dashboard_alerts(period_days=period_days),
            "kpis": build_dashboard_kpis(period_days=period_days),
            "movements": build_dashboard_movements(
                period_days=period_days, limit=movements_limit
            ),
            "generated_at": now.isoformat(),
        }

    return _cached(
        "overview",
        _OVERVIEW_TTL_SECONDS,
        _builder,
        period_days,
        movements_limit,
        revision,
    )


def build_legacy_kpi_panel() -> dict[str, Any]:
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return {
        "movements_today": Movement.objects.filter(created_at__gte=today_start).count(),
        "low_stock_products_count": _reorder_product_count(),
        "active_alerts_unresolved": Alert.objects.filter(is_resolved=False).count(),
        "dispatches_this_month": Movement.objects.filter(
            created_at__gte=month_start,
            movement_type__in=_SALES_MOVEMENT_TYPES,
        ).count(),
        "generated_at": now.isoformat(),
    }
