"""Permisos RBAC para autenticación y gestión de usuarios (RF-001, RF-002).

El rol rector del sistema es `almacenista`; `administrador` conserva lectura limitada.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission


def _has_role(request, role: str) -> bool:
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and getattr(user, "role", None) == role)


class IsAlmacenista(BasePermission):
    """BR-02 — Rol rector del sistema para escrituras y gestión de credenciales."""

    def has_permission(self, request, view) -> bool:
        return _has_role(request, "almacenista")


class IsAdministrador(BasePermission):
    """RBAC de lectura limitada para rol `administrador`."""

    def has_permission(self, request, view) -> bool:
        return _has_role(request, "administrador")


class IsAlmacenistaOrAdministrador(BasePermission):
    """Lectura compartida entre almacenista y administrador; no concede privilegios de escritura al administrador."""

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in ("almacenista", "administrador")
        )


class IsAuxiliarDespacho(BasePermission):
    """BR-01 — Solo rol `auxiliar_despacho`."""

    def has_permission(self, request, view) -> bool:
        return _has_role(request, "auxiliar_despacho")
