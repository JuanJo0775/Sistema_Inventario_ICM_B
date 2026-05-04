"""Permisos RBAC base (RF-001, RF-002, BR-03)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsAlmacenista(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", None) == "almacenista")


class IsAuxiliarDespacho(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", None) == "auxiliar_despacho")


class IsAdministrador(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", None) == "administrador")


class IsAlmacenistaOrAuxiliar(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) in ("almacenista", "auxiliar_despacho")
        )


class IsAlmacenistaOrAdministrador(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) in ("almacenista", "administrador")
        )


class IsWithinOperatingHours(BasePermission):
    """
    BR-03: Auxiliares de despacho solo operan en franjas permitidas.

    Para otros roles, no aplica restricción adicional (tras autenticación JWT).
    """

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, "role", None) != "auxiliar_despacho":
            return True
        from apps.authentication.services import is_within_operating_hours

        return is_within_operating_hours()
