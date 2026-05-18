"""Validadores reutilizables."""

from __future__ import annotations

import re


def validate_can_sku(
    sku: str, *, brand: str | None = None, is_own_brand: bool | None = None
) -> None:
    """Compatibilidad retroactiva: no exigir prefijo específico.

    Antes el negocio obligaba a un prefijo concreto para la marca propia.
    La regla fue cambiada: el SKU lo define el usuario y su formato se valida
    en `validate_sku_format`. Esta función queda como puente retrocompatible.
    """
    return None


def normalize_sku(value: str) -> str:
    return (value or "").strip()


_SKU_SAFE = re.compile(r"^[A-Za-z]{1,4}-\d{1,4}$")


def validate_sku_format(sku: str) -> None:
    """Valida que el SKU siga el patrón: 1–4 letras, un guion, 1–4 dígitos.

    Ejemplos válidos: `A-1`, `PRD-0001`, `ABCD-1234`.
    """
    if not sku or len(sku) > 100:
        raise ValueError("Formato SKU inválido.")
    if not _SKU_SAFE.match(sku):
        raise ValueError(
            "Formato SKU inválido. Debe ser 1-4 letras, guion, 1-4 dígitos (ej: ABC-1234)."
        )
