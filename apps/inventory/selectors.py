"""Consultas de inventario (RF-004, RNF-004)."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from django.db.models import Prefetch, Q, Sum
from django.db.models.query import QuerySet

from apps.catalog.models import Product
from apps.inventory.models import Location, StockByLocation
from apps.movements.services import ledger_net_quantity_for_location


def get_stock_by_product(product_id: UUID) -> dict[str, Any]:
    """
    RF-004 — Stock por ubicación y total consolidado para un producto.

    `total` se obtiene con agregación en BD (RNF-004).
    """
    product = Product.objects.filter(pk=product_id).only("id", "name", "sku").first()
    rows = (
        StockByLocation.objects.filter(product_id=product_id)
        .select_related(
            "location",
            "location__storage_type",
            "location__storage_template",
        )
        .order_by("location__code")
    )
    by_location = [
        {
            "location_id": str(r.location_id),
            "location_code": r.location.code,
            "location_name": r.location.name,
            "storage_type_id": str(r.location.storage_type_id)
            if r.location.storage_type_id
            else None,
            "storage_type_code": getattr(r.location.storage_type, "code", None),
            "storage_template_id": str(r.location.storage_template_id)
            if r.location.storage_template_id
            else None,
            "storage_template_code": getattr(
                r.location.storage_template, "code", None
            ),
            "operational_status": r.location.operational_status,
            "capacity_mode": r.location.capacity_mode,
            "capacity_level": r.location.capacity_level,
            "capacity_score": r.location.capacity_score,
            "occupancy_estimate_pct": r.location.occupancy_estimate_pct,
            "quantity": r.current_stock,
        }
        for r in rows
    ]
    total = int(
        StockByLocation.objects.filter(product_id=product_id).aggregate(
            s=Sum("current_stock")
        )["s"]
        or 0
    )
    return {
        "product_id": str(product_id),
        "product_name": getattr(product, "name", "") if product else "",
        "sku": getattr(product, "sku", "") if product else "",
        "by_location": by_location,
        "per_location": by_location,
        "total": total,
    }


def get_stock_by_location(location_id: UUID) -> QuerySet[StockByLocation]:
    """RF-004 — Stock de todos los productos en una ubicación."""
    return (
        StockByLocation.objects.filter(location_id=location_id, current_stock__gt=0)
        .select_related("product", "product__category")
        .order_by("product__sku")
    )


def search_products(
    query: str,
    *,
    category_id: UUID | None = None,
    subcategory_id: UUID | None = None,
) -> QuerySet[Product]:
    """
    RF-004, RNF-004 — Búsqueda por SKU, código de barras o nombre (autocompletado).

    Usa `select_related` para evitar N+1.
    """
    q = (query or "").strip()
    qs = Product.objects.filter(is_active=True).select_related(
        "category", "subcategory"
    )
    if category_id:
        qs = qs.filter(category_id=category_id)
    if subcategory_id:
        qs = qs.filter(subcategory_id=subcategory_id)
    if not q:
        return qs.order_by("sku")[:50]
    return qs.filter(
        Q(sku__icontains=q) | Q(barcode__icontains=q) | Q(name__icontains=q)
    ).order_by("sku")[:50]


def reconstruct_stock_from_ledger(
    product_id: UUID, location_id: UUID
) -> dict[str, Any]:
    """
    RF-004, BR-11 — Compara stock derivado con suma del ledger para producto/ubicación.

    Returns:
        dict con `status` CONSISTENT|DISCREPANCY, `reconstructed` y `actual`.
    """
    reconstructed = ledger_net_quantity_for_location(
        product_id=product_id, location_id=location_id
    )
    row = StockByLocation.objects.filter(
        product_id=product_id, location_id=location_id
    ).first()
    actual = int(row.current_stock) if row else 0
    status = "CONSISTENT" if reconstructed == actual else "DISCREPANCY"
    return {"status": status, "reconstructed": reconstructed, "actual": actual}


def consolidated_stock_total(product_id: UUID) -> int:
    """Total consolidado en una sola agregación (RNF-004)."""
    return int(
        StockByLocation.objects.filter(product_id=product_id).aggregate(
            total=Sum("current_stock")
        )["total"]
        or 0
    )


def get_full_inventory(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    RF-004 — Inventario consolidado por producto y ubicación.

    Args:
        filters: `category_id`, `location_id`, `storage_type_id`, `operational_status`,
                 `only_in_stock`, `stock_below_reorder` (bool).

    Returns:
        Lista de dicts con producto, totales y desglose por ubicación.
    """
    filters = filters or {}
    qs = Product.objects.filter(is_active=True).select_related(
        "category", "subcategory"
    )
    if filters.get("category_id"):
        qs = qs.filter(category_id=filters["category_id"])
    if filters.get("location_id"):
        qs = qs.filter(stock_by_location__location_id=filters["location_id"]).distinct()
    if filters.get("storage_type_id"):
        qs = qs.filter(
            stock_by_location__location__storage_type_id=filters["storage_type_id"]
        ).distinct()
    if filters.get("operational_status"):
        qs = qs.filter(
            stock_by_location__location__operational_status=filters["operational_status"]
        ).distinct()
    qs = qs.prefetch_related(
        Prefetch(
            "stock_by_location",
            queryset=StockByLocation.objects.select_related("location"),
        )
    )
    out: list[dict[str, Any]] = []
    for p in qs.order_by("sku"):
        rows = list(p.stock_by_location.all())
        total = sum(int(r.current_stock) for r in rows)
        if filters.get("only_in_stock") and total <= 0:
            continue
        if filters.get("stock_below_reorder") and total > int(p.reorder_point or 0):
            continue
        out.append(
            {
                "product_id": str(p.id),
                "sku": p.sku,
                "name": p.name,
                "category_id": str(p.category_id),
                "reorder_point": int(p.reorder_point or 0),
                "total": total,
                "by_location": [
                    {
                        "location_id": str(r.location_id),
                        "location_code": r.location.code,
                        "location_name": r.location.name,
                        "quantity": int(r.current_stock),
                    }
                    for r in sorted(rows, key=lambda x: x.location.code)
                ],
            }
        )
    return out


def get_low_stock_products(threshold: int = 5) -> QuerySet[Product]:
    """
    RF-004, RF-011 — Productos cuyo stock total consolidado es menor que `threshold`.

    Args:
        threshold: Umbral máximo exclusivo de stock total (por defecto 5 unidades).
    """
    ids = (
        Product.objects.filter(is_active=True)
        .annotate(t=Sum("stock_by_location__current_stock"))
        .filter(t__lt=threshold)
        .values_list("id", flat=True)
    )
    return (
        Product.objects.filter(id__in=list(ids))
        .select_related("category")
        .order_by("sku")
    )


def search_products_duration_seconds(query: str) -> tuple[list[str], float]:
    """Utilidad de diagnóstico de rendimiento (RNF-004)."""
    start = time.perf_counter()
    ids = [str(x) for x in search_products(query).values_list("id", flat=True)[:100]]
    elapsed = time.perf_counter() - start
    return ids, elapsed
