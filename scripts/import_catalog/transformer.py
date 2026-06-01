"""Transformación de filas validadas al formato de importación del sistema."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from .reader import RawRow
from .validator import ValidationReport

_SKU_SAFE = re.compile(r"^[A-Za-z]{1,4}-\d{1,4}$")
# Captura la parte numérica y el posible sufijo letra: "01A" → ("01", "A")
_REST_PATTERN = re.compile(r"^(\d{1,4})([A-Za-z]?)$")


@dataclass
class ImportRow:
    category_name: str
    sku: str
    name: str
    sku_was_generated: bool = False
    sku_was_transformed: bool = False
    original_sku: str = ""
    # Campos de precio — None si no vienen del Excel
    sale_price_retail: Decimal | None = None
    sale_price_wholesale: Decimal | None = None
    unit_cost: Decimal | None = None
    tax_rate_pct: Decimal | None = None
    currency: str | None = None


def _autogen_sku(row: RawRow) -> str:
    """Genera SKU para productos sin código.

    Regla: primeras 2 letras del primer word del nombre (uppercase)
    + guion + número de fila del Excel (column '#') con zero-padding a 4 dígitos.

    Ejemplo: 'Flexbar Amarillo', fila 32 → 'FL-0032'
    """
    first_word = row.producto.split()[0] if row.producto else "XX"
    prefix = re.sub(r"[^A-Za-z]", "", first_word)[:2].upper() or "XX"
    num = row.numero or 1
    return f"{prefix}-{num:04d}"


def _transform_invalid_sku(row: RawRow) -> str | None:
    """Intenta reparar SKUs con sufijo letra después del número.

    Estrategia: mueve el sufijo letra al final del prefijo.
    Ejemplos:
      MPC-01A  →  MPCA-01  (A se une al prefijo MPC → MPCA)
      MPC-02A  →  MPCA-02
      EC-01b   →  ECB-01   (b uppercase)

    Retorna None si no puede reparar.
    """
    parts = row.codigo.split("-", 1)
    if len(parts) != 2:
        return None

    prefix, rest = parts
    m = _REST_PATTERN.match(rest)
    if not m:
        return None

    digits, suffix_letter = m.group(1), m.group(2).upper()
    if suffix_letter:
        new_prefix = (prefix + suffix_letter)[:4]
    else:
        new_prefix = prefix

    candidate = f"{new_prefix}-{digits.zfill(2)}"
    return candidate if _SKU_SAFE.match(candidate) else None


def _price_fields(row: RawRow) -> dict:
    """Extrae los campos de precio de una RawRow."""
    return {
        "sale_price_retail": row.sale_price_retail,
        "sale_price_wholesale": row.sale_price_wholesale,
        "unit_cost": row.unit_cost,
        "tax_rate_pct": row.tax_rate_pct,
        "currency": row.currency,
    }


def transform(
    report: ValidationReport,
) -> tuple[list[ImportRow], list[tuple[RawRow, str]]]:
    """Convierte un ValidationReport en filas listas para importar.

    Returns:
        (import_rows, transform_errors)
    """
    import_rows: list[ImportRow] = []
    errors: list[tuple[RawRow, str]] = []

    for row in report.ok:
        import_rows.append(
            ImportRow(
                category_name=row.sheet_name.title(),
                sku=row.codigo.strip(),
                name=row.producto.strip(),
                **_price_fields(row),
            )
        )

    for row in report.needs_autogen:
        sku = _autogen_sku(row)
        import_rows.append(
            ImportRow(
                category_name=row.sheet_name.title(),
                sku=sku,
                name=row.producto.strip(),
                sku_was_generated=True,
                original_sku=row.codigo,
                **_price_fields(row),
            )
        )

    for row in report.invalid_sku:
        sku = _transform_invalid_sku(row)
        if sku:
            import_rows.append(
                ImportRow(
                    category_name=row.sheet_name.title(),
                    sku=sku,
                    name=row.producto.strip(),
                    sku_was_transformed=True,
                    original_sku=row.codigo,
                    **_price_fields(row),
                )
            )
        else:
            errors.append((row, f"No se pudo transformar SKU inválido: {row.codigo!r}"))

    return import_rows, errors
