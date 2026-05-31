"""Helpers para parsear y validar query params numéricos de forma segura."""

from __future__ import annotations


def clamp_period_days(
    value, *, default: int = 30, min_val: int = 1, max_val: int = 365
) -> int:
    """Parsea `period_days` limitando el rango a [min_val, max_val]."""
    try:
        return max(min_val, min(int(value), max_val))
    except (TypeError, ValueError):
        return default


def clamp_limit(
    value, *, default: int = 10, min_val: int = 1, max_val: int = 500
) -> int:
    """Parsea `limit` limitando el rango a [min_val, max_val]."""
    try:
        return max(min_val, min(int(value), max_val))
    except (TypeError, ValueError):
        return default
