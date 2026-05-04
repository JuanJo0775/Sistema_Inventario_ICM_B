"""Servicios de auditoría (RF-012)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.http import HttpRequest

from apps.audit.models import AuditEventType, AuditLog

if TYPE_CHECKING:
    from apps.authentication.models import User
    from apps.movements.models import Movement


def _client_ip(request: HttpRequest | None) -> str | None:
    if not request:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_event(
    event_type: str,
    *,
    description: str = "",
    user: User | None = None,
    request: HttpRequest | None = None,
    movement: Movement | None = None,
    user_affected: User | None = None,
    username_attempted: str | None = None,
    detail: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """
    RF-012 — Registra un evento de auditoría inmutable.

    `detail` se fusiona en `metadata` por compatibilidad con llamadas existentes.
    """
    meta: dict[str, Any] = {**(metadata or {}), **(detail or {})}
    if username_attempted:
        meta.setdefault("username_attempted", username_attempted)
    if user_affected is not None:
        meta.setdefault("affected_user_id", str(user_affected.pk))
        meta.setdefault("affected_username", user_affected.username)
    desc = description or str(event_type)
    return AuditLog.objects.create(
        event_type=event_type,
        user=user if user and getattr(user, "is_authenticated", False) else None,
        movement=movement,
        description=desc,
        metadata=meta,
        ip_address=_client_ip(request),
    )


def log_unauthorized_access_attempt(*, user: User | None, request: HttpRequest | None, detail: dict | None) -> AuditLog:
    """RNF-003 — Registra intentos de acceso a recursos no permitidos."""
    return log_event(
        AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
        description="Intento de acceso no autorizado",
        user=user,
        request=request,
        detail=detail or {},
    )


def log_immutable_modification_attempt(*, user: User | None, request: HttpRequest | None, detail: dict | None) -> AuditLog:
    """BR-10 / RF-012 — Intento de modificar registros inmutables."""
    return log_event(
        AuditEventType.MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD,
        description="Intento de modificación sobre registro inmutable",
        user=user,
        request=request,
        detail=detail or {},
    )
