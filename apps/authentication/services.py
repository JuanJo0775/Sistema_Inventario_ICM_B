"""Servicios de autenticación y gestión de usuarios (RF-001, RF-002, BR-02, BR-03)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from shared.exceptions import (
    DomainValidationError,
    OutsideOperatingHoursError,
    UnauthorizedCredentialManagementError,
)
from shared.operating_hours import (  # noqa: F401 — re-exportado para compatibilidad
    is_within_operating_hours,
)

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.authentication.models import TemporaryAccessPermit, User, UserSchedule


def _require_almacenista(user: User) -> None:
    if getattr(user, "role", None) != "almacenista":
        raise UnauthorizedCredentialManagementError()


def authenticate_user(
    username: str,
    password: str,
    *,
    request_time: datetime | None = None,
    request: HttpRequest | None = None,
) -> User:
    """
    RF-001 — Autentica credenciales y aplica restricción horaria BR-03 para auxiliares.

    Raises:
        AuthenticationFailed: Credenciales inválidas o usuario inactivo.
        OutsideOperatingHoursError: BR-03 — auxiliar fuera de franja.
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
        raise AuthenticationFailed("Credenciales inválidas.")
    if not user.is_active:
        log_event(
            AuditEventType.LOGIN_FAILED,
            user=user,
            request=request,
            detail={"reason": "inactive"},
        )
        raise AuthenticationFailed("La cuenta está deshabilitada.")
    if getattr(user, "role", None) == "auxiliar_despacho":
        rt = request_time or timezone.now()
        from apps.authentication.selectors import check_user_access

        if not check_user_access(user, rt):
            log_event(
                AuditEventType.LOGIN_FAILED,
                user=user,
                request=request,
                detail={"reason": "outside_operating_hours", "fuera_de_horario": True},
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
def create_user(
    almacenista_user: User, data: dict[str, Any], *, request: HttpRequest | None = None
) -> User:
    """
    RF-002, BR-02 — Crea usuario; solo almacenista.
    """
    from apps.authentication.models import User

    _require_almacenista(almacenista_user)
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise DomainValidationError("El correo electrónico es obligatorio.")
    user = User(
        username=(data["username"] or "").strip(),
        email=email,
        first_name=(data.get("first_name") or "").strip(),
        last_name=(data.get("last_name") or "").strip(),
        phone=(data.get("phone") or "").strip(),
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
def disable_user(
    almacenista_user: User,
    target_user_id: UUID | str,
    *,
    request: HttpRequest | None = None,
) -> User:
    """
    RF-002, BR-02 — Deshabilita usuario y revoca tokens JWT en lista negra.

    Returns:
        Usuario deshabilitado (persistido).
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
    return target


@transaction.atomic
def update_user(
    executor: User,
    user_id: UUID | str,
    update_data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> User:
    """
    RF-002, BR-02 — Actualiza campos permitidos del usuario (solo almacenista).

    No permite que el ejecutor modifique su propio rol.
    """
    from apps.authentication.models import User

    _require_almacenista(executor)
    target = User.objects.select_for_update().get(pk=user_id)
    if (
        target.pk == executor.pk
        and "role" in update_data
        and update_data["role"] != getattr(executor, "role", None)
    ):
        raise UnauthorizedCredentialManagementError("No puede modificar su propio rol.")

    allowed = {"email", "first_name", "last_name", "phone", "role", "username"}
    data = {k: v for k, v in update_data.items() if k in allowed}
    if "email" in data:
        em = (data["email"] or "").strip().lower()
        if User.objects.filter(email__iexact=em).exclude(pk=target.pk).exists():
            raise DomainValidationError("El correo electrónico ya está registrado.")
        data["email"] = em
    for key, val in data.items():
        setattr(target, key, val)
    target.save()
    log_event(
        AuditEventType.USER_UPDATED,
        description=f"Usuario actualizado: {target.username}",
        user=executor,
        request=request,
        user_affected=target,
        detail={"updated_fields": list(data.keys())},
    )
    return target


@transaction.atomic
def enable_user(
    almacenista_user: User,
    target_user_id: UUID | str,
    *,
    request: HttpRequest | None = None,
) -> User:
    """
    RF-002 — Rehabilita un usuario previamente deshabilitado.

    Returns:
        Usuario rehabilitado (persistido).
    """
    from apps.authentication.models import User

    _require_almacenista(almacenista_user)
    target = User.objects.select_for_update().get(pk=target_user_id)
    target.is_active = True
    target.save(update_fields=["is_active", "updated_at"])
    log_event(
        AuditEventType.USER_ENABLED,
        description=f"Usuario rehabilitado: {target.username}",
        user=almacenista_user,
        request=request,
        user_affected=target,
        detail={"enabled_username": target.username},
    )
    return target


@transaction.atomic
def update_user_password(
    almacenista_user: User,
    target_user_id: UUID | str,
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


@transaction.atomic
def create_or_update_user_schedule(
    almacenista_user: User,
    target_user: User,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> UserSchedule:
    """
    Creates or updates the stable operating hours schedule for an Auxiliar de Despacho.
    Only Almacenista can perform this action, and they cannot modify other roles or themselves.
    """
    _require_almacenista(almacenista_user)

    if target_user.pk == almacenista_user.pk:
        raise DomainValidationError("No puede modificar su propio horario o permisos.")
    if target_user.role != "auxiliar_despacho":
        raise DomainValidationError(
            "Solo se pueden asignar horarios personalizados a auxiliares de despacho."
        )

    from apps.audit.models import AuditEventType
    from apps.audit.services import log_event
    from apps.authentication.models import UserSchedule

    schedule, created = UserSchedule.objects.select_for_update().get_or_create(
        user=target_user
    )

    previous_values = (
        {
            "morning_start": (
                schedule.morning_start.isoformat()
                if schedule.morning_start
                else None
            ),
            "morning_end": (
                schedule.morning_end.isoformat() if schedule.morning_end else None
            ),
            "afternoon_start": (
                schedule.afternoon_start.isoformat()
                if schedule.afternoon_start
                else None
            ),
            "afternoon_end": (
                schedule.afternoon_end.isoformat()
                if schedule.afternoon_end
                else None
            ),
            "is_active": schedule.is_active,
        }
        if not created
        else None
    )

    schedule.morning_start = data.get("morning_start")
    schedule.morning_end = data.get("morning_end")
    schedule.afternoon_start = data.get("afternoon_start")
    schedule.afternoon_end = data.get("afternoon_end")
    schedule.is_active = data.get("is_active", True)
    schedule.save()

    new_values = {
        "morning_start": (
            schedule.morning_start.isoformat() if schedule.morning_start else None
        ),
        "morning_end": (
            schedule.morning_end.isoformat() if schedule.morning_end else None
        ),
        "afternoon_start": (
            schedule.afternoon_start.isoformat()
            if schedule.afternoon_start
            else None
        ),
        "afternoon_end": (
            schedule.afternoon_end.isoformat() if schedule.afternoon_end else None
        ),
        "is_active": schedule.is_active,
    }

    log_event(
        AuditEventType.PERMISSION_CHANGED,
        description=f"Horario personalizado {'creado' if created else 'actualizado'} para {target_user.username}",
        user=almacenista_user,
        request=request,
        user_affected=target_user,
        detail={
            "change_type": "schedule_created" if created else "schedule_updated",
            "target_user": {
                "id": str(target_user.id),
                "username": target_user.username,
            },
            "granted_by": {
                "id": str(almacenista_user.id),
                "username": almacenista_user.username,
            },
            "previous_values": previous_values,
            "new_values": new_values,
            "timestamp": timezone.now().isoformat(),
        },
    )
    return schedule


@transaction.atomic
def grant_temporary_permit(
    almacenista_user: User,
    target_user: User,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> TemporaryAccessPermit:
    """
    Grants a temporary access exception permit to an Auxiliar de Despacho.
    Only Almacenista can perform this action.
    """
    _require_almacenista(almacenista_user)

    if target_user.pk == almacenista_user.pk:
        raise DomainValidationError("No puede otorgarse permisos temporales a sí mismo.")
    if target_user.role != "auxiliar_despacho":
        raise DomainValidationError(
            "Solo se pueden otorgar permisos temporales a auxiliares de despacho."
        )

    from apps.audit.models import AuditEventType
    from apps.audit.services import log_event
    from apps.authentication.models import TemporaryAccessPermit

    permit = TemporaryAccessPermit(
        user=target_user,
        start_datetime=data["start_datetime"],
        end_datetime=data["end_datetime"],
        allow_24_7=data.get("allow_24_7", False),
        custom_morning_start=data.get("custom_morning_start"),
        custom_morning_end=data.get("custom_morning_end"),
        custom_afternoon_start=data.get("custom_afternoon_start"),
        custom_afternoon_end=data.get("custom_afternoon_end"),
        reason=data["reason"],
        granted_by=almacenista_user,
        is_active=True,
    )
    permit.save()

    new_values = {
        "permit_id": str(permit.id),
        "start_datetime": permit.start_datetime.isoformat(),
        "end_datetime": permit.end_datetime.isoformat(),
        "allow_24_7": permit.allow_24_7,
        "custom_morning_start": (
            permit.custom_morning_start.isoformat()
            if permit.custom_morning_start
            else None
        ),
        "custom_morning_end": (
            permit.custom_morning_end.isoformat()
            if permit.custom_morning_end
            else None
        ),
        "custom_afternoon_start": (
            permit.custom_afternoon_start.isoformat()
            if permit.custom_afternoon_start
            else None
        ),
        "custom_afternoon_end": (
            permit.custom_afternoon_end.isoformat()
            if permit.custom_afternoon_end
            else None
        ),
        "reason": permit.reason,
    }

    log_event(
        AuditEventType.PERMISSION_CHANGED,
        description=f"Permiso temporal otorgado a {target_user.username}",
        user=almacenista_user,
        request=request,
        user_affected=target_user,
        detail={
            "change_type": "permit_granted",
            "target_user": {
                "id": str(target_user.id),
                "username": target_user.username,
            },
            "granted_by": {
                "id": str(almacenista_user.id),
                "username": almacenista_user.username,
            },
            "new_values": new_values,
            "timestamp": timezone.now().isoformat(),
        },
    )
    return permit


@transaction.atomic
def revoke_temporary_permit(
    almacenista_user: User,
    permit_id: UUID | str,
    *,
    request: HttpRequest | None = None,
) -> TemporaryAccessPermit:
    """
    Revokes (deactivates) an active temporary access permit.
    Only Almacenista can perform this action.
    """
    _require_almacenista(almacenista_user)

    from apps.audit.models import AuditEventType
    from apps.audit.services import log_event
    from apps.authentication.models import TemporaryAccessPermit

    permit = TemporaryAccessPermit.objects.select_for_update().get(pk=permit_id)
    if not permit.is_active:
        return permit

    permit.is_active = False
    permit.save(update_fields=["is_active", "updated_at"])

    log_event(
        AuditEventType.PERMISSION_CHANGED,
        description=f"Permiso temporal revocado para {permit.user.username}",
        user=almacenista_user,
        request=request,
        user_affected=permit.user,
        detail={
            "change_type": "permit_revoked",
            "target_user": {
                "id": str(permit.user.id),
                "username": permit.user.username,
            },
            "revoked_by": {
                "id": str(almacenista_user.id),
                "username": almacenista_user.username,
            },
            "permit_id": str(permit.id),
            "timestamp": timezone.now().isoformat(),
        },
    )
    return permit
