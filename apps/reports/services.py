"""Capa de servicio fina para reportes (RF-010); delega en selectores de solo lectura."""

from __future__ import annotations

from typing import Any

from apps.reports import selectors as report_selectors


def generate_kpis() -> dict[str, Any]:
    """
    RF-010 — KPIs para panel administrativo.

    Mantiene el nombre histórico `generate_kpis` usado en tests; implementación en selectores.
    """
    return report_selectors.get_kpi_dashboard()
