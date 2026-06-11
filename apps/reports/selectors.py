"""Reportes y KPIs de solo lectura (RF-010)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.catalog.selectors import get_lots_expiring_soon
from apps.dashboard.services import build_legacy_kpi_panel
from apps.inventory.models import Location
from apps.movements.models import Movement, MovementType
from apps.movements.selectors import get_dispatches_with_invoices
from apps.movements.services import ledger_net_quantity_for_lot_location


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
        movement_type__in=[
            MovementType.SALIDA_VENTA_MAYOR,
            MovementType.SALIDA_VENTA_MENOR,
        ],
    )
    return {
        "mayor": filt.filter(movement_type=MovementType.SALIDA_VENTA_MAYOR).aggregate(
            q=Sum("quantity")
        )["q"]
        or 0,
        "menor": filt.filter(movement_type=MovementType.SALIDA_VENTA_MENOR).aggregate(
            q=Sum("quantity")
        )["q"]
        or 0,
    }


def get_dispatch_operational_summary(period_days: int = 30) -> dict[str, Any]:
    """
    RF-010 — Resumen operativo de despacho para frontend.

    No calcula OTIF porque el backend aún no modela pedidos, promesas de entrega ni
    estados logísticos completos. Entrega hechos confiables para que el frontend,
    o un ERP/OMS externo, calcule el KPI final.
    """
    end = timezone.now()
    start = end - timedelta(days=period_days)
    sales = sales_dispatch_totals(start=start, end=end)
    invoice_linked_count = (
        get_dispatches_with_invoices()
        .filter(created_at__gte=start, created_at__lte=end)
        .count()
    )
    top_products = get_top_dispatched_products(limit=10, period_days=period_days)
    movement_counts = movement_counts_by_period(start=start, end=end)
    # Número de envíos (movimientos de salida de venta)
    shipments = (
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type__in=[
                MovementType.SALIDA_VENTA_MAYOR,
                MovementType.SALIDA_VENTA_MENOR,
            ],
        ).count()
        or 0
    )
    invoice_linked_ratio = (
        round((invoice_linked_count / shipments) * 100, 2) if shipments else 0.0
    )
    # Build per-order samples using invoice_number as proxy for orders when available
    per_order_samples: list[dict[str, object]] = []
    order_qs = (
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type__in=[
                MovementType.SALIDA_VENTA_MAYOR,
                MovementType.SALIDA_VENTA_MENOR,
            ],
        )
        .exclude(invoice_number__isnull=True)
        .exclude(invoice_number__exact="")
        .values("invoice_number")
        .annotate(movements=Count("id"), total_quantity=Sum("quantity"))
        .order_by("-total_quantity")
    )

    for row in order_qs:
        inv = row["invoice_number"]
        mov_count = int(row["movements"] or 0)
        tot_qty = int(row["total_quantity"] or 0)
        # dispatched_at: approximate as latest movement created_at for that invoice
        latest = (
            Movement.objects.filter(invoice_number=inv)
            .order_by("-created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        per_order_samples.append(
            {
                "invoice_number": inv,
                "movements": mov_count,
                "total_quantity": tot_qty,
                "items": mov_count,
                "dispatched_at": latest.isoformat() if latest else None,
            }
        )

    return {
        "period": {
            "days": period_days,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "sales": sales,
        "invoice_linked_dispatches": invoice_linked_count,
        "shipments": shipments,
        "invoice_linked_ratio": invoice_linked_ratio,
        "movement_counts": movement_counts,
        "top_products": top_products,
        "order_proxy": [],
        "carriers": {},
        "per_order_samples": per_order_samples,
        "promised_date_example": None,
        "notes": [
            "KPI 4 OTIF no se calcula aquí porque faltan pedidos, fecha pactada, transportadora y entrega confirmada.",
            "El frontend puede usar este resumen como base visual y combinarlo con su fuente de pedidos o ERP.",
        ],
    }


def movement_history(
    *,
    product_id: UUID | str | None = None,
    user_id: int | None = None,
    location_id: UUID | str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
):
    """RF-010 — Historial filtrable (QuerySet lazy)."""
    qs = Movement.objects.all().select_related("product", "lot", "executed_by")
    if product_id:
        qs = qs.filter(product_id=UUID(str(product_id)))
    if user_id is not None:
        qs = qs.filter(executed_by_id=user_id)
    if location_id:
        lid = UUID(str(location_id))
        qs = qs.filter(
            models.Q(origin_location_id=lid) | models.Q(destination_location_id=lid)
        )
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
    return (
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type=MovementType.ENTRADA,
        )
        .exclude(discrepancy_note__isnull=True)
        .exclude(discrepancy_note__exact="")
        .count()
    )


def get_inventory_summary() -> dict[str, Any]:
    """
    RF-010 — Resumen de inventario por categoría y productos sin stock.

    Valor aproximado: no hay precio en catálogo; se devuelve nota y conteos.
    """
    from apps.inventory.models import StockByLocation

    by_category: list[dict[str, Any]] = []
    for cat in Category.objects.all():
        total = (
            StockByLocation.objects.filter(product__category=cat).aggregate(
                s=Sum("current_stock")
            )["s"]
            or 0
        )
        by_category.append(
            {
                "category_id": str(cat.id),
                "category": cat.name,
                "total_units": int(total),
            }
        )
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


def get_dispatch_order_samples(
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    invoice_number: str | None = None,
    limit: int = 100,
) -> list[dict[str, object]]:
    """Return a list of per-order samples using `invoice_number` as a proxy.

    Each item: invoice_number, movements, total_quantity, items, dispatched_at
    """
    end = end or timezone.now()
    start = start or (end - timedelta(days=30))
    q = (
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type__in=[
                MovementType.SALIDA_VENTA_MAYOR,
                MovementType.SALIDA_VENTA_MENOR,
            ],
        )
        .exclude(invoice_number__isnull=True)
        .exclude(invoice_number__exact="")
    )
    if invoice_number:
        q = q.filter(invoice_number=invoice_number)

    rows = (
        q.values("invoice_number")
        .annotate(movements=Count("id"), total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:limit]
    )

    samples: list[dict[str, object]] = []
    for row in rows:
        inv = row["invoice_number"]
        mov_count = int(row["movements"] or 0)
        tot_qty = int(row["total_quantity"] or 0)
        latest = (
            Movement.objects.filter(invoice_number=inv)
            .order_by("-created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        samples.append(
            {
                "invoice_number": inv,
                "movements": mov_count,
                "total_quantity": tot_qty,
                "items": mov_count,
                "dispatched_at": latest.isoformat() if latest else None,
            }
        )
    return samples


def get_warehouse_utilization() -> dict[str, Any]:
    """
    RF-010 — Utilización de almacén por capacidad configurada.

    Calcula ocupación sobre ubicaciones activas con `max_capacity` definido.
    Las ubicaciones sin capacidad configurada se reportan aparte para no distorsionar
    el porcentaje global.
    """
    locations = list(
        Location.objects.filter(is_active=True)
        .annotate(occupied_units=Sum("stock_items__current_stock"))
        .order_by("code")
    )

    by_location: list[dict[str, Any]] = []
    by_storage_type: dict[str, dict[str, Any]] = {}
    by_operational_status: dict[str, dict[str, Any]] = {}
    configured_occupied = 0
    configured_capacity = 0
    unconfigured_occupied = 0
    configured_locations = 0
    unconfigured_locations = 0

    for location in locations:
        occupied_units = int(getattr(location, "occupied_units", 0) or 0)
        utilization_pct = None
        capacity_configured = False
        capacity_units = None

        if (
            location.capacity_mode
            in [Location.CapacityMode.ABSOLUTE_LEGACY, Location.CapacityMode.NONE]
            and location.max_capacity is not None
            and int(location.max_capacity) > 0
        ):
            capacity_units = int(location.max_capacity)
            capacity_configured = True
            utilization_pct = round((occupied_units / capacity_units) * 100, 2)
        elif (
            location.capacity_mode == Location.CapacityMode.RELATIVE_SCALE
            and location.capacity_score is not None
            and int(location.capacity_score) > 0
        ):
            capacity_units = int(location.capacity_score)
            capacity_configured = True
            utilization_pct = round((occupied_units / capacity_units) * 100, 2)
        elif location.occupancy_estimate_pct is not None:
            utilization_pct = round(float(location.occupancy_estimate_pct), 2)

        if capacity_configured:
            configured_locations += 1
            configured_occupied += occupied_units
            configured_capacity += capacity_units or 0
        else:
            unconfigured_locations += 1
            unconfigured_occupied += occupied_units

        storage_bucket_key = (
            location.storage_type.code
            if getattr(location, "storage_type", None) and location.storage_type.code
            else "untyped"
        )
        storage_bucket_label = (
            location.storage_type.name
            if getattr(location, "storage_type", None) and location.storage_type.name
            else "Sin tipo"
        )
        storage_bucket = by_storage_type.setdefault(
            storage_bucket_key,
            {
                "storage_type_code": storage_bucket_key,
                "storage_type_name": storage_bucket_label,
                "locations": 0,
                "occupied_units": 0,
            },
        )
        storage_bucket["locations"] += 1
        storage_bucket["occupied_units"] += occupied_units

        status_bucket = by_operational_status.setdefault(
            location.operational_status,
            {
                "operational_status": location.operational_status,
                "locations": 0,
                "occupied_units": 0,
            },
        )
        status_bucket["locations"] += 1
        status_bucket["occupied_units"] += occupied_units

        by_location.append(
            {
                "location_id": str(location.id),
                "code": location.code,
                "name": location.name,
                "occupied_units": occupied_units,
                "capacity_units": capacity_units,
                "utilization_pct": utilization_pct,
                "is_retail": bool(location.is_retail),
                "capacity_configured": capacity_configured,
                "capacity_mode": location.capacity_mode,
                "capacity_level": location.capacity_level,
                "capacity_score": location.capacity_score,
                "occupancy_estimate_pct": location.occupancy_estimate_pct,
                "operational_status": location.operational_status,
                "storage_type_code": (
                    location.storage_type.code
                    if getattr(location, "storage_type", None)
                    else None
                ),
                "storage_type_name": (
                    location.storage_type.name
                    if getattr(location, "storage_type", None)
                    else None
                ),
            }
        )

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
        },
        "by_location": by_location,
        "by_storage_type": sorted(
            by_storage_type.values(), key=lambda item: item["storage_type_code"]
        ),
        "by_operational_status": sorted(
            by_operational_status.values(), key=lambda item: item["operational_status"]
        ),
    }


def get_warehouse_occupancy_distribution() -> dict[str, Any]:
    """
    RF-010 — Distribución de ocupación por tipo de almacenamiento y estado operativo.

    Reutiliza el cálculo de utilización para exponer un payload frontend-ready
    enfocado en distribución, sin alterar el comportamiento del KPI legacy.
    """
    utilization = get_warehouse_utilization()
    return {
        "overall": utilization["overall"],
        "by_storage_type": utilization["by_storage_type"],
        "by_operational_status": utilization["by_operational_status"],
    }


def get_quality_operational_summary(period_days: int = 30) -> dict[str, Any]:
    """
    RF-010 — Resumen operativo de calidad para frontend.

    El backend no modela aún incidentes de calidad, PQRSF ni causales de descarte.
    Esta vista entrega los hechos derivados disponibles hoy para que el frontend
    construya la interpretación, alertas y visualizaciones.
    """
    end = timezone.now()
    start = end - timedelta(days=period_days)
    quality_types = (
        MovementType.SALIDA_DANO,
        MovementType.SALIDA_VENCIMIENTO,
        MovementType.DEVOLUCION,
    )
    rows = list(
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type__in=quality_types,
        )
        .values("movement_type", "product__sku", "product__name")
        .annotate(movements=Count("id"), units=Sum("quantity"))
        .order_by("movement_type", "-units", "product__sku")
    )

    by_type: dict[str, dict[str, Any]] = {}
    by_product: list[dict[str, Any]] = []
    total_units = 0
    total_movements = 0
    incident_units = 0
    damage_units = 0
    discard_units = 0
    return_units = 0

    for row in rows:
        movement_type = row["movement_type"]
        movements = int(row["movements"] or 0)
        units = int(row["units"] or 0)
        total_movements += movements
        total_units += units
        if movement_type == MovementType.SALIDA_DANO:
            damage_units += units
        elif movement_type == MovementType.SALIDA_VENCIMIENTO:
            discard_units += units
        elif movement_type == MovementType.DEVOLUCION:
            return_units += units
        incident_units += units
        bucket = by_type.setdefault(
            movement_type,
            {"movement_type": movement_type, "movements": 0, "units": 0},
        )
        bucket["movements"] += movements
        bucket["units"] += units
        by_product.append(
            {
                "movement_type": movement_type,
                "product_sku": row["product__sku"],
                "product_name": row["product__name"],
                "movements": movements,
                "units": units,
            }
        )

    # KPI 2 se expresa como un proxy operativo: hechos de calidad sobre total de hechos de calidad.
    # El frontend puede combinarlo con otro denominador de negocio si incorpora pedidos o salidas totales.
    quality_index_pct = (
        round((incident_units / total_units) * 100, 2) if total_units else 0.0
    )

    return {
        "period": {
            "days": period_days,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "totals": {"movements": total_movements, "units": total_units},
        "breakdown": {
            "incident_units": incident_units,
            "damage_units": damage_units,
            "discard_units": discard_units,
            "return_units": return_units,
            "quality_index_pct": quality_index_pct,
        },
        "by_type": list(by_type.values()),
        "by_product": by_product[:50],
        "notes": [
            "KPI 2 y KPI 6 siguen siendo parciales: el backend entrega hechos derivados, no incidentes ni PQRSF formales.",
            "quality_index_pct es un proxy operativo calculado solo con hechos de calidad visibles en el ledger.",
            "La clasificación de causas y un denominador comercial más fino deben resolverse en frontend o en un bounded context adicional.",
        ],
    }


def get_discard_operational_summary(period_days: int = 30) -> dict[str, Any]:
    """
    RF-010 — Resumen operativo de descarte para frontend.

    KPI 5 se alimenta con salidas por daño y vencimiento. Las devoluciones se
    excluyen para no mezclar descarte con logística inversa.
    """
    end = timezone.now()
    start = end - timedelta(days=period_days)
    discard_types = (MovementType.SALIDA_DANO, MovementType.SALIDA_VENCIMIENTO)
    rows = list(
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type__in=discard_types,
        )
        .values("movement_type", "product__sku", "product__name")
        .annotate(movements=Count("id"), units=Sum("quantity"))
        .order_by("movement_type", "-units", "product__sku")
    )

    by_type: dict[str, dict[str, Any]] = {}
    by_product: list[dict[str, Any]] = []
    total_units = 0
    total_movements = 0

    for row in rows:
        movement_type = row["movement_type"]
        movements = int(row["movements"] or 0)
        units = int(row["units"] or 0)
        total_movements += movements
        total_units += units
        bucket = by_type.setdefault(
            movement_type,
            {"movement_type": movement_type, "movements": 0, "units": 0},
        )
        bucket["movements"] += movements
        bucket["units"] += units
        by_product.append(
            {
                "movement_type": movement_type,
                "product_sku": row["product__sku"],
                "product_name": row["product__name"],
                "movements": movements,
                "units": units,
            }
        )

    return {
        "period": {
            "days": period_days,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "totals": {"movements": total_movements, "units": total_units},
        "by_type": list(by_type.values()),
        "by_product": by_product[:50],
        "notes": [
            "KPI 5 se calcula con salidas por daño y vencimiento; las devoluciones quedan fuera de este resumen.",
            "La tasa final y el costo proxy deben resolverse en frontend o en una capa analítica si se agregan valores monetarios.",
        ],
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
    counts = {
        row["movement_type"]: row["c"]
        for row in qs.values("movement_type").annotate(c=Count("id"))
    }
    by_product = list(
        qs.values("product__sku", "product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:100]
    )
    by_user = list(
        qs.values("executed_by__username")
        .annotate(movements=Count("id"))
        .order_by("-movements")[:50]
    )
    return {
        "counts": counts,
        "by_product": by_product,
        "by_user": by_user,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
    }


def get_top_dispatched_products(
    limit: int = 10, period_days: int = 30
) -> list[dict[str, Any]]:
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
        Movement.objects.filter(
            created_at__gte=start, created_at__lte=end, movement_type__in=salidas
        )
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
    qs = get_dispatches_with_invoices().select_related(
        "product", "lot", "executed_by", "origin_location"
    )
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
    """RF-010, RF-011 — Lotes que vencen en los próximos `days` días."""
    rows: list[dict[str, Any]] = []
    for lot in get_lots_expiring_soon(days=days):
        location_ids = {
            lid
            for row in Movement.objects.filter(
                product_id=lot.product_id, lot_id=lot.id
            ).values_list("origin_location_id", "destination_location_id")
            for lid in row
            if lid is not None
        }
        for location_id in {x for x in location_ids if x is not None}:
            qty = ledger_net_quantity_for_lot_location(
                product_id=lot.product_id, lot_id=lot.id, location_id=location_id
            )
            if qty <= 0:
                continue
            location = (
                Location.objects.filter(pk=location_id)
                .only("id", "code", "name")
                .first()
            )
            if not location:
                continue
            rows.append(
                {
                    "product_id": lot.product_id,
                    "sku": lot.product.sku,
                    "name": lot.product.name,
                    "lot_id": lot.id,
                    "lot_code": lot.code,
                    "expiration_date": lot.expiration_date,
                    "days_left": (lot.expiration_date - timezone.now().date()).days,
                    "location_id": location.id,
                    "location_code": location.code,
                    "location_name": location.name,
                    "available_quantity": int(qty),
                }
            )
    return rows


def get_kpi_dashboard() -> dict[str, Any]:
    """RF-010 — KPIs operativos para panel administrativo.

    Mantiene compatibilidad histórica, pero el cálculo queda centralizado en el
    servicio de dashboard para evitar drift entre reports y dashboard.
    """
    return build_legacy_kpi_panel()


# ---------------------------------------------------------------------------
# Reportes financieros (Fase 5)
# ---------------------------------------------------------------------------


def sales_revenue_summary(*, start: datetime, end: datetime) -> dict[str, Any]:
    """
    Resumen de revenue por tipo de venta en el período.

    Retorna subtotales, impuestos y totales separados por venta mayor/menor.
    Los movements sin precio (históricos o sin precio configurado) contribuyen con 0.
    """
    from decimal import Decimal

    from django.db.models import DecimalField
    from django.db.models.functions import Coalesce

    zero = Decimal("0")
    sale_types = [MovementType.SALIDA_VENTA_MAYOR, MovementType.SALIDA_VENTA_MENOR]
    qs = Movement.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        movement_type__in=sale_types,
    )

    def _agg(movement_type: str) -> dict[str, Any]:
        row = qs.filter(movement_type=movement_type).aggregate(
            qty=Sum("quantity"),
            subtotal=Sum(Coalesce("subtotal", 0, output_field=DecimalField())),
            discount=Sum(Coalesce("discount_amount", 0, output_field=DecimalField())),
            tax=Sum(Coalesce("tax_amount", 0, output_field=DecimalField())),
            total=Sum(Coalesce("total_amount", 0, output_field=DecimalField())),
        )
        return {
            "units": row["qty"] or 0,
            "subtotal": row["subtotal"] or zero,
            "discount": row["discount"] or zero,
            "tax": row["tax"] or zero,
            "total": row["total"] or zero,
        }

    mayor = _agg(MovementType.SALIDA_VENTA_MAYOR)
    menor = _agg(MovementType.SALIDA_VENTA_MENOR)
    return {
        "wholesale": mayor,
        "retail": menor,
        "combined": {
            "units": mayor["units"] + menor["units"],
            "subtotal": mayor["subtotal"] + menor["subtotal"],
            "discount": mayor["discount"] + menor["discount"],
            "tax": mayor["tax"] + menor["tax"],
            "total": mayor["total"] + menor["total"],
        },
        "period": {"start": start.isoformat(), "end": end.isoformat()},
    }


def gross_margin_by_product(
    *, start: datetime, end: datetime, limit: int = 50
) -> list[dict[str, Any]]:
    """
    Margen bruto por SKU en el período.

    margen = total_amount - (unit_cost * quantity)
    Solo incluye despachos de venta (SALIDA_VENTA_MAYOR / MENOR) con precio configurado.
    """
    from decimal import Decimal

    from django.db.models import DecimalField, ExpressionWrapper, F
    from django.db.models.functions import Coalesce

    sale_types = [MovementType.SALIDA_VENTA_MAYOR, MovementType.SALIDA_VENTA_MENOR]
    qs = (
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type__in=sale_types,
            total_amount__isnull=False,
        )
        .values("product__sku", "product__name")
        .annotate(
            revenue=Sum(Coalesce("total_amount", 0, output_field=DecimalField())),
            cogs=Sum(
                ExpressionWrapper(
                    Coalesce("unit_cost", 0, output_field=DecimalField())
                    * F("quantity"),
                    output_field=DecimalField(),
                )
            ),
            units=Sum("quantity"),
        )
        .order_by("-revenue")[:limit]
    )

    result = []
    for row in qs:
        revenue = row["revenue"] or Decimal("0")
        cogs = row["cogs"] or Decimal("0")
        margin = revenue - cogs
        margin_pct = (
            (margin / revenue * 100).quantize(Decimal("0.01"))
            if revenue
            else Decimal("0")
        )
        result.append(
            {
                "sku": row["product__sku"],
                "name": row["product__name"],
                "units": row["units"],
                "revenue": revenue,
                "cogs": cogs,
                "gross_margin": margin,
                "gross_margin_pct": margin_pct,
            }
        )
    return result


def sales_by_customer(
    *, start: datetime, end: datetime, limit: int = 50
) -> list[dict[str, Any]]:
    """
    Ventas mayores agrupadas por cliente (customer_snapshot.customer_name).

    Retorna los N clientes con mayor revenue en el período.
    """
    from decimal import Decimal

    from django.db.models import DecimalField
    from django.db.models.functions import Coalesce

    qs = (
        Movement.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            movement_type=MovementType.SALIDA_VENTA_MAYOR,
            customer_snapshot__isnull=False,
        )
        .values("customer_snapshot__customer_name")
        .annotate(
            revenue=Sum(Coalesce("total_amount", 0, output_field=DecimalField())),
            units=Sum("quantity"),
            orders=Count("invoice_number", distinct=True),
        )
        .order_by("-revenue")[:limit]
    )

    return [
        {
            "customer_name": row["customer_snapshot__customer_name"] or "—",
            "units": row["units"],
            "orders": row["orders"],
            "revenue": row["revenue"] or Decimal("0"),
        }
        for row in qs
    ]
