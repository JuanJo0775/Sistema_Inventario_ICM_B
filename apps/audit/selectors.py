"""Consultas de auditoría de solo lectura (RF-012)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db.models import QuerySet

from apps.audit.models import AuditLog


def get_audit_log(
    filters: dict[str, Any],
    *,
    executor_role: str,
) -> QuerySet[AuditLog]:
    """
    RF-012 — Lista paginable de logs (solo roles autorizados en la vista).

    Args:
        filters: `event_type`, `user_id` (ejecutor del evento), `start`, `end` ISO.
        executor_role: Rol del solicitante (validado en vista).

    Returns:
        QuerySet ordenado por fecha descendente.
    """
    del executor_role  # La vista restringe acceso; el selector permanece puro.
    qs = AuditLog.objects.select_related("user", "movement").all()
    if et := filters.get("event_type"):
        qs = qs.filter(event_type=et)
    if uid := filters.get("user_id"):
        qs = qs.filter(user_id=int(uid))
    if start := filters.get("start"):
        if isinstance(start, str):
            from django.utils.dateparse import parse_datetime

            start = parse_datetime(start)
        if start:
            qs = qs.filter(created_at__gte=start)
    if end := filters.get("end"):
        if isinstance(end, str):
            from django.utils.dateparse import parse_datetime

            end = parse_datetime(end)
        if end:
            qs = qs.filter(created_at__lte=end)
    return qs.order_by("-created_at")


def get_audit_log_by_movement(movement_id: UUID) -> QuerySet[AuditLog]:
    """RF-012 — Eventos asociados a un movimiento."""
    return (
        AuditLog.objects.filter(movement_id=movement_id)
        .select_related("user", "movement")
        .order_by("-created_at")
    )


def get_audit_log_by_user(target_user_id: int, executor_role: str) -> QuerySet[AuditLog]:
    """
    RF-012 — Eventos donde el usuario objetivo es el actor (`user`).

    Args:
        target_user_id: PK del usuario buscado.
        executor_role: Validación RBAC en la vista.
    """
    del executor_role
    return (
        AuditLog.objects.filter(user_id=target_user_id)
        .select_related("user", "movement")
        .order_by("-created_at")
    )
