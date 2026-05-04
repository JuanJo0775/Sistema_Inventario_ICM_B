"""Servicios de autenticación y gestión de usuarios (RF-001, RF-002, BR-02, BR-03)."""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from shared.exceptions import OutsideOperatingHoursError, UnauthorizedCredentialManagementError

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.authentication.models import User


BOGOTA = ZoneInfo("America/Bogota")


def is_within_operating_hours(*, now: datetime | None = None) -> bool:
    """
    BR-03 — Determina si la hora actual está en franja permitida para auxiliares.

    Franjas (hora local America/Bogota): 07:00–12:00 y 14:00–17:00 (inclusive).
    """
    now = now or timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, BOGOTA)
    local = now.astimezone(BOGOTA)
    t = local.time()
    morning = time(7, 0) <= t <= time(12, 0)
    afternoon = time(14, 0) <= t <= time(17, 0)
    return morning or afternoon


def _require_almacenista(user: User) -> None:
    if getattr(user, "role", None) != "almacenista":
        raise UnauthorizedCredentialManagementError()


def authenticate_user(
    username: str,
    password: str,
    *,
    request_time: datetime | None = None,
    request: HttpRequest | None = None,
) -> User | None:
    """
    RF-001 — Autentica credenciales y aplica restricción horaria BR-03 para auxiliares.
    """
    user = authenticate(username=username, password=password)
    if user is None:
        log_event(
            AuditEventType.LOGIN_FAILED,
            user=None,
            request=request,
            username_attempted=username,
            detail={"reason": "bad_credentials"},
        )
        return None
    if not user.is_active:
        log_event(
            AuditEventType.LOGIN_FAILED,
            user=user,
            request=request,
            detail={"reason": "inactive"},
        )
        return None
    if getattr(user, "role", None) == "auxiliar_despacho":
        rt = request_time or timezone.now()
        if not is_within_operating_hours(now=rt):
            log_event(
                AuditEventType.LOGIN_FAILED,
                user=user,
                request=request,
                detail={"reason": "outside_operating_hours"},
            )
            raise OutsideOperatingHoursError()
    log_event(
        AuditEventType.LOGIN_SUCCESS,
        description="Login exitoso",
        user=user,
        request=request,
        detail={"username": user.username},
    )
    return user


@transaction.atomic
def create_user(almacenista_user: User, data: dict[str, Any], *, request: HttpRequest | None = None) -> User:
    """
    RF-002, BR-02 — Crea usuario; solo almacenista.
    """
    from apps.authentication.models import User

    _require_almacenista(almacenista_user)
    user = User(
        username=data["username"],
        email=data.get("email", ""),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        role=data["role"],
        created_by=almacenista_user,
    )
    user.set_password(data["password"])
    user.save()
    log_event(
        AuditEventType.USER_CREATED,
        description=f"Usuario creado: {user.username}",
        user=almacenista_user,
        request=request,
        user_affected=user,
        detail={"created_username": user.username, "role": user.role},
    )
    return user


@transaction.atomic
def disable_user(almacenista_user: User, target_user_id, *, request: HttpRequest | None = None) -> None:
    """
    RF-002, BR-02 — Deshabilita usuario y revoca tokens JWT en lista negra.
    """
    from apps.authentication.models import User

    _require_almacenista(almacenista_user)
    target = User.objects.select_for_update().get(pk=target_user_id)
    target.is_active = False
    target.save(update_fields=["is_active", "updated_at"])
    for token in OutstandingToken.objects.filter(user=target):
        BlacklistedToken.objects.get_or_create(token=token)
    log_event(
        AuditEventType.USER_DISABLED,
        description=f"Usuario deshabilitado: {target.username}",
        user=almacenista_user,
        request=request,
        user_affected=target,
        detail={"disabled_username": target.username},
    )


@transaction.atomic
def update_user_password(
    almacenista_user: User,
    target_user_id,
    new_password: str,
    *,
    request: HttpRequest | None = None,
) -> None:
    """RF-002 — Cambio de contraseña solo por almacenista."""
    from apps.authentication.models import User

    _require_almacenista(almacenista_user)
    target = User.objects.select_for_update().get(pk=target_user_id)
    target.set_password(new_password)
    target.save(update_fields=["password", "updated_at"])
    log_event(
        AuditEventType.USER_UPDATED,
        description=f"Cambio de contraseña: {target.username}",
        user=almacenista_user,
        request=request,
        user_affected=target,
        detail={"target_username": target.username, "change": "password"},
    )
