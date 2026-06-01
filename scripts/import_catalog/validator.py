"""Validación de filas leídas del Excel antes de la transformación."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .reader import RawRow

_SKU_SAFE = re.compile(r"^[A-Za-z]{1,4}-\d{1,4}$")


@dataclass
class ValidationReport:
    ok: list[RawRow] = field(default_factory=list)
    needs_autogen: list[RawRow] = field(default_factory=list)
    invalid_sku: list[RawRow] = field(default_factory=list)
    errors: list[tuple[RawRow, str]] = field(default_factory=list)


def validate(rows: list[RawRow]) -> ValidationReport:
    """Clasifica cada fila según el estado de su SKU y nombre.

    Categorías:
      ok           — SKU válido y nombre presente.
      needs_autogen — SKU ausente o 'S/C'.
      invalid_sku  — SKU con formato no válido (ej: MPC-01A).
      errors       — Nombre vacío o SKU duplicado dentro del Excel.
    """
    report = ValidationReport()
    seen: dict[str, int] = {}  # sku_upper → índice de primera aparición

    for idx, row in enumerate(rows):
        if not row.producto:
            report.errors.append((row, "Nombre de producto vacío"))
            continue

        codigo = row.codigo.strip()

        if not codigo or codigo.upper() in ("S/C", "SC"):
            report.needs_autogen.append(row)
            continue

        if not _SKU_SAFE.match(codigo):
            report.invalid_sku.append(row)
            continue

        sku_key = codigo.upper()
        if sku_key in seen:
            report.errors.append(
                (
                    row,
                    f"SKU duplicado en Excel (primera ocurrencia en posición {seen[sku_key]})",
                )
            )
        else:
            seen[sku_key] = idx

        report.ok.append(row)

    return report
