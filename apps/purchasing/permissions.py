"""Permisos RBAC para el módulo de compras."""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsPurchasingOperator(BasePermission):
    """
    Permite acceso a almacenistas.

    Diseñado para extensión futura con rol 'comprador' (ver ADR-014).
    """

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in ("almacenista",)
        )


class IsPurchasingViewer(BasePermission):
    """Lectura para almacenistas y administradores."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in ("almacenista", "administrador")
        )
