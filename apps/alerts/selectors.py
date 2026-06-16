"""Consultas de alertas (RF-011)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db.models import Count, QuerySet
from django.utils import timezone

from apps.alerts.models import Alert


def get_active_alerts(filters: dict[str, Any] | None = None) -> QuerySet[Alert]:
    """
    RF-011 — Alertas no resueltas con producto (y ubicación si aplica).

    Filtros soportados: alert_type, product_id, severity, category, location_id, date_from, date_to.
    """
    filters = filters or {}
    qs = Alert.objects.filter(is_resolved=False).select_related(
        "product", "lot", "location"
    )
    if at := filters.get("alert_type"):
        qs = qs.filter(alert_type=at)
    if pid := filters.get("product_id"):
        qs = qs.filter(product_id=pid)
    if sv := filters.get("severity"):
        qs = qs.filter(severity=sv)
    if cat := filters.get("category"):
        qs = qs.filter(category=cat)
    if lid := filters.get("location_id"):
        qs = qs.filter(location_id=lid)
    if df := filters.get("date_from"):
        qs = qs.filter(created_at__date__gte=df)
    if dt := filters.get("date_to"):
        qs = qs.filter(created_at__date__lte=dt)
    return qs.order_by("-created_at")


def get_resolved_alerts(filters: dict[str, Any] | None = None) -> QuerySet[Alert]:
    """RF-011 — Alertas resueltas (historial) con soporte de filtros."""
    filters = filters or {}
    qs = Alert.objects.filter(is_resolved=True).select_related(
        "product", "lot", "location", "resolved_by"
    )
    if at := filters.get("alert_type"):
        qs = qs.filter(alert_type=at)
    if pid := filters.get("product_id"):
        qs = qs.filter(product_id=pid)
    if sv := filters.get("severity"):
        qs = qs.filter(severity=sv)
    if cat := filters.get("category"):
        qs = qs.filter(category=cat)
    if lid := filters.get("location_id"):
        qs = qs.filter(location_id=lid)
    if df := filters.get("date_from"):
        qs = qs.filter(created_at__date__gte=df)
    if dt := filters.get("date_to"):
        qs = qs.filter(created_at__date__lte=dt)
    return qs.order_by("-resolved_at")


def get_alert_stats() -> dict[str, Any]:
    """RF-011 — Conteos de alertas activas agrupados por severidad y categoría."""
    active_qs = Alert.objects.filter(is_resolved=False)
    by_severity = dict(
        active_qs.values("severity")
        .annotate(n=Count("id"))
        .values_list("severity", "n")
    )
    by_category = dict(
        active_qs.values("category")
        .annotate(n=Count("id"))
        .values_list("category", "n")
    )
    return {
        "total_active": active_qs.count(),
        "by_severity": by_severity,
        "by_category": by_category,
        "generated_at": timezone.now().isoformat(),
    }


def get_alerts_by_product(product_id: UUID) -> QuerySet[Alert]:
    """RF-011 — Todas las alertas de un producto (activas e histórico)."""
    return (
        Alert.objects.filter(product_id=product_id)
        .select_related("lot", "location")
        .order_by("-created_at")
    )
