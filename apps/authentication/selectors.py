"""Consultas de solo lectura de usuarios (RF-001, RF-002)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


def get_user_by_id(user_id: UUID | str) -> User:
    """
    RF-002 — Obtiene usuario por clave primaria.

    Args:
        user_id: `id` del usuario (UUID).

    Returns:
        Instancia de `User`.

    Raises:
        User.DoesNotExist: Si no existe.
    """
    if isinstance(user_id, str):
        import uuid

        user_id = uuid.UUID(user_id)
    return User.objects.get(pk=user_id)


def get_all_users(executor: User, *, include_inactive: bool = False) -> QuerySet[User]:
    """
    RF-002, BR-02 — Lista usuarios ordenados por fecha de creación.

    Solo debe invocarse tras validar que `executor` es almacenista (capa de servicio/vista).

    Args:
        executor: Usuario que ejecuta la consulta (debe ser almacenista).
        include_inactive: Si True, incluye usuarios deshabilitados en el resultado.

    Returns:
        QuerySet de usuarios.
    """
    qs = User.objects.all().order_by("-created_at", "-id")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs


def get_user_profile(user: User) -> dict[str, Any]:
    """
    RF-001 — Representación segura del perfil (sin credenciales).

    Args:
        user: Usuario autenticado.

    Returns:
        Diccionario serializable para API.
    """
    from apps.authentication.serializers import user_login_profile

    base = user_login_profile(user)
    return {
        **base,
        "created_at": (
            user.created_at.isoformat() if getattr(user, "created_at", None) else None
        ),
        "updated_at": (
            user.updated_at.isoformat() if getattr(user, "updated_at", None) else None
        ),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_by": user.created_by_id,
    }


def check_user_access(user: User, dt: datetime | None = None) -> bool:
    """
    Evaluates system access for a user.
    If role is not auxiliar_despacho, access is always allowed.
    If role is auxiliar_despacho, access is evaluated based on:
    1. Active temporary access permits (TemporaryAccessPermit).
    2. Active custom schedule (UserSchedule).
    3. Default system operating hours.

    Includes request-level caching if caching attributes are available on the user object.
    """
    if not user.is_authenticated:
        return False
    if not user.is_active:
        return False

    if getattr(user, "role", None) != "auxiliar_despacho":
        return True

    from datetime import datetime
    from django.utils import timezone
    from apps.authentication.models import TemporaryAccessPermit, UserSchedule
    from shared.operating_hours import (
        _AFTERNOON_END,
        _AFTERNOON_START,
        _MORNING_END,
        _MORNING_START,
        is_time_in_ranges,
    )

    tz = timezone.get_current_timezone()
    dt = dt or timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, tz)
    dt_local = dt.astimezone(tz)

    cache_attr = f"_cached_access_allowed_{dt_local.isoformat()[:16]}"
    if hasattr(user, cache_attr):
        return getattr(user, cache_attr)

    # Step 1: Active temporary permits
    active_permits = TemporaryAccessPermit.objects.filter(
        user=user,
        is_active=True,
        start_datetime__lte=dt_local,
        end_datetime__gte=dt_local,
    )

    for permit in active_permits:
        if permit.allow_24_7:
            setattr(user, cache_attr, True)
            return True
        t = dt_local.time()
        if is_time_in_ranges(
            t,
            permit.custom_morning_start,
            permit.custom_morning_end,
            permit.custom_afternoon_start,
            permit.custom_afternoon_end,
        ):
            setattr(user, cache_attr, True)
            return True

    # Step 2: Stable schedule
    try:
        schedule = UserSchedule.objects.get(user=user, is_active=True)
        t = dt_local.time()
        allowed = is_time_in_ranges(
            t,
            schedule.morning_start,
            schedule.morning_end,
            schedule.afternoon_start,
            schedule.afternoon_end,
        )
        setattr(user, cache_attr, allowed)
        return allowed
    except UserSchedule.DoesNotExist:
        pass

    # Step 3: Default system operating hours
    t = dt_local.time()
    allowed = is_time_in_ranges(
        t,
        _MORNING_START,
        _MORNING_END,
        _AFTERNOON_START,
        _AFTERNOON_END,
    )
    setattr(user, cache_attr, allowed)
    return allowed
