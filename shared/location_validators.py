"""Validadores de estado operativo de ubicación reutilizables (BR-14)."""

from __future__ import annotations

from apps.inventory.models import Location
from shared.exceptions import LocationStateNotAllowedError


def validate_location_for_origin(location: Location, operation: str = "operación") -> None:
    """BR-14 — Valida que la ubicación pueda actuar como origen de un movimiento."""
    if location.operational_status in {
        Location.OperationalStatus.BLOCKED,
        Location.OperationalStatus.ARCHIVED,
    }:
        raise LocationStateNotAllowedError(
            f"La ubicación '{location.name}' no puede operar como origen en {operation}.",
            detail={
                "location_id": str(location.id),
                "operational_status": location.operational_status,
                "operation": operation,
                "role": "origin",
            },
        )
    if location.operational_status in {
        Location.OperationalStatus.MAINTENANCE,
        Location.OperationalStatus.RESTRICTED,
    }:
        raise LocationStateNotAllowedError(
            f"La ubicación '{location.name}' está en estado {location.operational_status} "
            f"y no puede despachar stock.",
            detail={
                "location_id": str(location.id),
                "operational_status": location.operational_status,
                "operation": operation,
                "role": "origin",
            },
        )


def validate_location_for_destination(location: Location, operation: str = "operación") -> None:
    """BR-14 — Valida que la ubicación pueda actuar como destino de un movimiento."""
    if location.operational_status in {
        Location.OperationalStatus.BLOCKED,
        Location.OperationalStatus.ARCHIVED,
    }:
        raise LocationStateNotAllowedError(
            f"La ubicación '{location.name}' no puede recibir stock en {operation}.",
            detail={
                "location_id": str(location.id),
                "operational_status": location.operational_status,
                "operation": operation,
                "role": "destination",
            },
        )
