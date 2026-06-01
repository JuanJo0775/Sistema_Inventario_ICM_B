"""Lectura del Excel de clasificación de productos."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

import openpyxl

# Nombres de columna de precio reconocidos (case-insensitive, sin tildes)
_PRICE_HEADERS = {
    "precio venta": "sale_price_retail",
    "precio menor": "sale_price_retail",
    "precio minorista": "sale_price_retail",
    "precio mayorista": "sale_price_wholesale",
    "precio mayor": "sale_price_wholesale",
    "costo": "unit_cost",
    "costo unitario": "unit_cost",
    "iva": "tax_rate_pct",
    "iva%": "tax_rate_pct",
    "tasa iva": "tax_rate_pct",
    "moneda": "currency",
}


@dataclass
class RawRow:
    sheet_name: str
    codigo: str
    numero: int | None
    producto: str
    # Campos de precio — None si la columna no existe en la hoja
    sale_price_retail: Decimal | None = None
    sale_price_wholesale: Decimal | None = None
    unit_cost: Decimal | None = None
    tax_rate_pct: Decimal | None = None
    currency: str | None = None


def _normalize_header(value: object) -> str:
    """Normaliza texto de encabezado para comparar sin importar mayúsculas/tildes."""
    import unicodedata

    raw = str(value or "").strip().lower()
    # Quitar tildes/diacríticos
    normalized = unicodedata.normalize("NFD", raw)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def _parse_decimal(value: object) -> Decimal | None:
    """Convierte un valor de celda a Decimal; retorna None si no es numérico."""
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.0001"))
    except (InvalidOperation, ValueError):
        return None


def _detect_price_columns(header_row: tuple) -> dict[int, str]:
    """
    Examina la fila de encabezados (columna 3 en adelante) y retorna
    {col_index: field_name} para cada columna de precio reconocida.
    """
    mapping: dict[int, str] = {}
    if header_row is None:
        return mapping
    for idx, cell in enumerate(header_row):
        if idx < 3:
            continue  # Columnas 0-2 son Código, #, Producto
        normalized = _normalize_header(cell)
        if normalized in _PRICE_HEADERS:
            mapping[idx] = _PRICE_HEADERS[normalized]
    return mapping


def read_excel(path: str | Path) -> list[RawRow]:
    """Lee todas las hojas de productos del Excel y retorna filas normalizadas.

    Estructura esperada por hoja:
      Fila 0: Título de la categoría (ej. 'CAMILLAS')
      Fila 1: Encabezados ('Código', '#', 'Producto' [, 'Precio Venta', ...])
      Filas 2+: Datos de productos
      Última fila: 'Total: X productos' (se omite)

    Las columnas de precio (D en adelante) son opcionales — si no existen,
    los campos de precio en RawRow quedan como None.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows: list[RawRow] = []

    for sheet in wb.worksheets:
        if sheet.title.strip().lower() == "resumen":
            continue

        ws_rows = list(sheet.iter_rows(values_only=True))
        if len(ws_rows) < 2:
            continue

        # Fila 1 contiene los encabezados
        header_row = ws_rows[1]
        price_cols = _detect_price_columns(header_row)

        # Filas 2+ son datos
        for raw in ws_rows[2:]:
            if not raw:
                continue
            codigo_raw = raw[0] if len(raw) > 0 else None
            numero_raw = raw[1] if len(raw) > 1 else None
            producto_raw = raw[2] if len(raw) > 2 else None

            codigo = str(codigo_raw).strip() if codigo_raw is not None else ""
            if not codigo or str(codigo).lower().startswith("total"):
                continue

            try:
                numero = int(numero_raw) if numero_raw is not None else None
            except (ValueError, TypeError):
                numero = None

            # Leer campos de precio si existen
            price_values: dict[str, Decimal | str | None] = {
                "sale_price_retail": None,
                "sale_price_wholesale": None,
                "unit_cost": None,
                "tax_rate_pct": None,
                "currency": None,
            }
            for col_idx, field_name in price_cols.items():
                cell_value = raw[col_idx] if col_idx < len(raw) else None
                if field_name == "currency":
                    price_values["currency"] = (
                        str(cell_value).strip().upper() if cell_value else None
                    )
                else:
                    price_values[field_name] = _parse_decimal(cell_value)

            rows.append(
                RawRow(
                    sheet_name=sheet.title.strip(),
                    codigo=codigo,
                    numero=numero,
                    producto=(
                        str(producto_raw).strip() if producto_raw is not None else ""
                    ),
                    sale_price_retail=price_values["sale_price_retail"],
                    sale_price_wholesale=price_values["sale_price_wholesale"],
                    unit_cost=price_values["unit_cost"],
                    tax_rate_pct=price_values["tax_rate_pct"],
                    currency=price_values["currency"],
                )
            )

    wb.close()
    return rows
