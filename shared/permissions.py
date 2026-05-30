"""Permisos RBAC base (RF-001, RF-002, BR-03)."""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAlmacenista(BasePermission):
    """BR-02 — Rol rector del sistema: permisos operativos y administrativos principales."""

    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) == "almacenista"
        )


class IsAuxiliarDespacho(BasePermission):
    """BR-01 — Solo rol `auxiliar_despacho` (movimientos en franja BR-03)."""

    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) == "auxiliar_despacho"
        )


class IsAdministrador(BasePermission):
    """BR-01 — Rol de lectura limitada para reportes y KPI; no desplaza al almacenista."""

    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) == "administrador"
        )


class IsAlmacenistaOrAuxiliar(BasePermission):
    """Operaciones de almacén o despacho (entrada/salida/traslado según vista)."""

    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and getattr(u, "role", None) in ("almacenista", "auxiliar_despacho")
        )


class IsAlmacenistaOrAdministrador(BasePermission):
    """RF-010 — Lectura compartida para reportes y resumenes; el almacenista conserva el control principal."""

    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and getattr(u, "role", None) in ("almacenista", "administrador")
        )


class IsWithinOperatingHours(BasePermission):
    """
    BR-03 — Auxiliares de despacho solo operan en franjas permitidas (America/Bogota).

    Horario local: 07:00–12:00 y 14:00–17:00 inclusive. Otros roles no tienen esta restricción
    adicional tras autenticación JWT.
    """

    message = "Acceso denegado: el auxiliar de despacho solo opera en horario 07:00–12:00 y 14:00–17:00 (Bogotá)."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, "role", None) != "auxiliar_despacho":
            return True
        from apps.authentication.services import is_within_operating_hours

        return is_within_operating_hours()


class IsReadOnly(BasePermission):
    """Solo métodos seguros (GET, HEAD, OPTIONS) — útil en ViewSets de solo lectura."""

    def has_permission(self, request, view) -> bool:
        return bool(request.method in SAFE_METHODS)
