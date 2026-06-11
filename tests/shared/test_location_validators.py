"""Tests para shared/location_validators.py (BR-14)."""

from __future__ import annotations

import pytest

from apps.inventory.models import Location
from shared.exceptions import LocationStateNotAllowedError
from shared.location_validators import (
    validate_location_for_destination,
    validate_location_for_origin,
)
from tests.factories import LocationFactory


def _location_with_status(status: str) -> Location:
    loc = LocationFactory(
        code=f"LOC-{status.upper()}",
        name=f"Ubicación {status}",
        operational_status=status,
    )
    return loc


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["blocked", "archived"])
def test_validate_origin_raises_for_blocked_archived(status):
    loc = _location_with_status(status)
    with pytest.raises(LocationStateNotAllowedError) as exc_info:
        validate_location_for_origin(loc, "test_op")
    assert exc_info.value.detail_payload["role"] == "origin"


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["maintenance", "restricted"])
def test_validate_origin_raises_for_maintenance_restricted(status):
    loc = _location_with_status(status)
    with pytest.raises(LocationStateNotAllowedError) as exc_info:
        validate_location_for_origin(loc, "test_op")
    assert exc_info.value.detail_payload["role"] == "origin"


@pytest.mark.django_db
def test_validate_origin_passes_for_active():
    loc = _location_with_status("active")
    validate_location_for_origin(loc, "test_op")  # no debe lanzar


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["blocked", "archived"])
def test_validate_destination_raises_for_blocked_archived(status):
    loc = _location_with_status(status)
    with pytest.raises(LocationStateNotAllowedError) as exc_info:
        validate_location_for_destination(loc, "test_op")
    assert exc_info.value.detail_payload["role"] == "destination"


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["active", "maintenance", "restricted"])
def test_validate_destination_passes_for_non_blocked(status):
    """Mantenimiento/restringido bloquea origen pero no destino."""
    loc = _location_with_status(status)
    validate_location_for_destination(loc, "test_op")  # no debe lanzar
