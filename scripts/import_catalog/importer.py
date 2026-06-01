"""Inserción de datos en la base de datos usando los servicios del catálogo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.db import transaction

from apps.catalog.models import Category, Product
from apps.catalog.services import create_category, create_product

from .transformer import ImportRow

if TYPE_CHECKING:
    from apps.authentication.models import User


@dataclass
class ImportResult:
    categories_created: int = 0
    categories_skipped: int = 0
    products_created: int = 0
    products_skipped: int = 0
    products_with_prices: int = 0
    products_generated_sku: list[str] = field(default_factory=list)
    products_transformed_sku: list[tuple[str, str]] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


def import_rows(
    user: User,
    rows: list[ImportRow],
    *,
    dry_run: bool = False,
) -> ImportResult:
    """Importa filas de catálogo a la base de datos de forma idempotente.

    - Categorías: get_or_create por nombre (case-insensitive).
    - Productos: se omiten si el SKU ya existe en BD.
    - Si las columnas de precio están presentes en el Excel, se guardan en el producto.
    - Un error en un producto no cancela los demás (atomic por fila).
    - dry_run=True lee la BD pero no escribe nada.
    """
    result = ImportResult()
    category_cache: dict[str, Category | None] = {}

    for row in rows:
        cat_name = row.category_name
        if cat_name not in category_cache:
            category_cache[cat_name] = _ensure_category(
                user, cat_name, result, dry_run=dry_run
            )

        cat = category_cache[cat_name]

        # Verificar si el producto ya existe
        if Product.objects.filter(sku__iexact=row.sku).exists():
            result.products_skipped += 1
            continue

        has_prices = any(
            getattr(row, f) is not None
            for f in (
                "sale_price_retail",
                "sale_price_wholesale",
                "unit_cost",
                "tax_rate_pct",
            )
        )

        if dry_run:
            result.products_created += 1
            if has_prices:
                result.products_with_prices += 1
            _record_sku_flags(row, result)
            continue

        try:
            with transaction.atomic():
                product_data = {
                    "sku": row.sku,
                    "name": row.name,
                    "category_id": str(cat.id),
                }
                # Agregar campos de precio solo si tienen valor
                if row.sale_price_retail is not None:
                    product_data["sale_price_retail"] = row.sale_price_retail
                if row.sale_price_wholesale is not None:
                    product_data["sale_price_wholesale"] = row.sale_price_wholesale
                if row.unit_cost is not None:
                    product_data["unit_cost"] = row.unit_cost
                if row.tax_rate_pct is not None:
                    product_data["tax_rate_pct"] = row.tax_rate_pct
                if row.currency is not None:
                    product_data["currency"] = row.currency

                create_product(user, product_data)

            result.products_created += 1
            if has_prices:
                result.products_with_prices += 1
            _record_sku_flags(row, result)
        except Exception as exc:
            result.errors.append((row.sku, str(exc)))

    return result


def _ensure_category(
    user: User,
    name: str,
    result: ImportResult,
    *,
    dry_run: bool,
) -> Category | None:
    existing = Category.objects.filter(name__iexact=name).first()
    if existing:
        result.categories_skipped += 1
        return existing

    result.categories_created += 1
    if dry_run:
        return None

    return create_category(user, name=name)


def _record_sku_flags(row: ImportRow, result: ImportResult) -> None:
    if row.sku_was_generated:
        result.products_generated_sku.append(row.sku)
    if row.sku_was_transformed:
        result.products_transformed_sku.append((row.original_sku, row.sku))
