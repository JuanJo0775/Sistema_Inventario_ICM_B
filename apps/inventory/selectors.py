"""Consultas de inventario (RF-004, RNF-004)."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from django.db.models import Q, Sum
from django.db.models.query import QuerySet

from apps.catalog.models import Product
from apps.inventory.models import Location, StockByLocation
from apps.movements.services import ledger_net_quantity_for_location


def get_stock_by_product(product_id: UUID) -> dict[str, Any]:
    """
    RF-004 — Stock por ubicación y total consolidado para un producto.
    """
    rows = (
        StockByLocation.objects.filter(product_id=product_id)
        .select_related("location")
        .order_by("location__code")
    )
    per_location = [
        {
            "location_id": str(r.location_id),
            "location_code": r.location.code,
            "quantity": r.current_stock,
        }
        for r in rows
    ]
    total = sum(r["quantity"] for r in per_location)
    return {"product_id": str(product_id), "per_location": per_location, "total": total}


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
    qs = Product.objects.filter(is_active=True).select_related("category", "subcategory")
    if category_id:
        qs = qs.filter(category_id=category_id)
    if subcategory_id:
        qs = qs.filter(subcategory_id=subcategory_id)
    if not q:
        return qs.order_by("sku")[:50]
    return qs.filter(Q(sku__icontains=q) | Q(barcode__icontains=q) | Q(name__icontains=q)).order_by("sku")[:50]


def reconstruct_stock_from_ledger(product_id: UUID, location_id: UUID) -> int:
    """
    RF-004 / arquitectura híbrida — Reconstruye stock desde el ledger.

    Debe coincidir con `StockByLocation` si el caché está sincronizado.
    """
    return ledger_net_quantity_for_location(product_id=product_id, location_id=location_id)


def consolidated_stock_total(product_id: UUID) -> int:
    """Total consolidado en una sola agregación (RNF-004)."""
    return int(
        StockByLocation.objects.filter(product_id=product_id).aggregate(total=Sum("current_stock"))["total"] or 0
    )


def search_products_duration_seconds(query: str) -> tuple[list[str], float]:
    """Utilidad de diagnóstico de rendimiento (RNF-004)."""
    start = time.perf_counter()
    ids = [str(x) for x in search_products(query).values_list("id", flat=True)[:100]]
    elapsed = time.perf_counter() - start
    return ids, elapsed
