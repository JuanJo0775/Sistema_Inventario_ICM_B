"""Permisos RBAC para autenticación y gestión de usuarios (RF-001, RF-002).

Re-exporta desde shared.permissions, que es la fuente canónica única.
Permite importar cualquier clase de permiso desde este módulo sin duplicar
implementaciones ni perder acceso a IsWithinOperatingHours.
"""

from __future__ import annotations

from shared.permissions import (  # noqa: F401
    IsAdministrador,
    IsAlmacenista,
    IsAlmacenistaOrAdministrador,
    IsAlmacenistaOrAuxiliar,
    IsAuxiliarDespacho,
    IsReadOnly,
    IsWithinOperatingHours,
)

__all__ = [
    "IsAdministrador",
    "IsAlmacenista",
    "IsAlmacenistaOrAdministrador",
    "IsAlmacenistaOrAuxiliar",
    "IsAuxiliarDespacho",
    "IsReadOnly",
    "IsWithinOperatingHours",
]
