"""Consultas de alertas (RF-011)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db.models import QuerySet

from apps.alerts.models import Alert


def get_active_alerts(filters: dict[str, Any] | None = None) -> QuerySet[Alert]:
    """
    RF-011 — Alertas no resueltas con producto (y ubicación si aplica).

    Args:
        filters: `alert_type`, `product_id` opcionales.
    """
    filters = filters or {}
    qs = Alert.objects.filter(is_resolved=False).select_related(
        "product", "lot", "location"
    )
    if at := filters.get("alert_type"):
        qs = qs.filter(alert_type=at)
    if pid := filters.get("product_id"):
        qs = qs.filter(product_id=pid)
    return qs.order_by("-created_at")


def get_alerts_by_product(product_id: UUID) -> QuerySet[Alert]:
    """RF-011 — Todas las alertas de un producto (activas e histórico)."""
    return (
        Alert.objects.filter(product_id=product_id)
        .select_related("lot", "location")
        .order_by("-created_at")
    )
