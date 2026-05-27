"""Consultas de catálogo de solo lectura (RF-003, RNF-004)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.catalog.models import Category, Lot, Product


def get_product_by_id(product_id: UUID) -> Product:
    """
    RF-003 — Producto con categoría y subcategoría precargadas.

    Raises:
        Product.DoesNotExist: Si el UUID no existe.
    """
    return Product.objects.select_related("category", "subcategory").get(pk=product_id)


def get_all_products(filters: dict[str, Any] | None = None) -> QuerySet[Product]:
    """
    RF-003 — Listado filtrable de productos activos/inactivos y categoría.

    Args:
        filters: Opcional: `category_id`, `is_active`, `search` (nombre/SKU).

    Returns:
        QuerySet ordenado por SKU.
    """
    filters = filters or {}
    qs = Product.objects.select_related("category", "subcategory").all()
    if filters.get("category_id"):
        qs = qs.filter(category_id=filters["category_id"])
    if filters.get("is_active") is not None:
        qs = qs.filter(is_active=bool(filters["is_active"]))
    if search := (filters.get("search") or "").strip():
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(sku__icontains=search)
            | Q(barcode__icontains=search)
        )
    return qs.order_by("sku")


def get_categories() -> QuerySet[Category]:
    """RF-003 — Todas las categorías ordenadas por nombre."""
    return Category.objects.all().order_by("name")


def get_products_expiring_soon(days: int = 30) -> QuerySet[Product]:
    """
    RF-003, RF-011 — Productos con vencimiento en los próximos `days` días.

    Args:
        days: Ventana hacia adelante desde hoy (fecha local del servidor).

    Returns:
        Productos activos con `expiration_date` en rango.
    """
    today = timezone.now().date()
    until = today + timedelta(days=days)
    return (
        Product.objects.filter(is_active=True, expiration_date__isnull=False)
        .filter(expiration_date__gte=today, expiration_date__lte=until)
        .select_related("category")
        .order_by("expiration_date", "sku")
    )


def get_lots_expiring_soon(days: int = 30) -> QuerySet[Lot]:
    """RF-003, RF-011 — Lotes con vencimiento en los próximos `days` días."""
    today = timezone.now().date()
    until = today + timedelta(days=days)
    return (
        Lot.objects.filter(
            expiration_date__gte=today,
            expiration_date__lte=until,
            product__is_active=True,
        )
        .select_related("product", "product__category")
        .order_by("expiration_date", "code")
    )
