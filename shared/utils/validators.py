"""Validadores reutilizables."""

from __future__ import annotations

import re


def validate_can_sku(sku: str, *, brand: str | None = None, is_own_brand: bool | None = None) -> None:
    """BR-12: SKU de marca propia Can debe usar prefijo CAN-."""
    if is_own_brand is not None:
        own = is_own_brand
    else:
        own = (brand or "").strip().lower() == "can"
    if own and not sku.upper().startswith("CAN-"):
        raise ValueError('Los productos de marca propia "Can" deben usar prefijo CAN- en el SKU.')


def normalize_sku(value: str) -> str:
    return (value or "").strip()


_SKU_SAFE = re.compile(r"^[A-Za-z0-9._\-]+$")


def validate_sku_format(sku: str) -> None:
    if not sku or len(sku) > 100:
        raise ValueError("SKU inválido.")
    if not _SKU_SAFE.match(sku):
        raise ValueError("El SKU solo puede contener letras, números y - _ .")
