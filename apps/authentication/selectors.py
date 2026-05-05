"""Consultas de solo lectura de usuarios (RF-001, RF-002)."""

from __future__ import annotations

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


def get_all_users(executor: User) -> QuerySet[User]:
    """
    RF-002, BR-02 — Lista usuarios ordenados por fecha de creación.

    Solo debe invocarse tras validar que `executor` es almacenista (capa de servicio/vista).

    Args:
        executor: Usuario que ejecuta la consulta (debe ser almacenista).

    Returns:
        QuerySet de usuarios.
    """
    return User.objects.all().order_by("-created_at", "-id")


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
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        "updated_at": user.updated_at.isoformat() if getattr(user, "updated_at", None) else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_by": user.created_by_id,
    }
