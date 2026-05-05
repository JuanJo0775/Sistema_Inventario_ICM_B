"""Permisos específicos del catálogo (RF-003, BR-02)."""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAlmacenistaOrReadOnly(BasePermission):
    """
    Lectura autenticada; escritura solo almacenista (RF-003).

    Usado en detalle de producto y listados que admiten POST puntuales en vistas dedicadas.
    """

    def has_permission(self, request, view) -> bool:
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(u, "role", None) == "almacenista"
