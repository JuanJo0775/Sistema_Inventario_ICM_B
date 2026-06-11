"""Tests parametrizados de restricciones por estado operativo de ubicación.

Cada combinación (operación × estado) está documentada explícitamente.
BR-14: el estado operativo de una ubicación restringe las operaciones permitidas.
"""

from __future__ import annotations

import pytest

from apps.inventory.models import StockByLocation
from apps.movements.models import MovementType
from apps.movements.services import (
    register_dispatch,
    register_entry,
    register_internal_transfer,
)
from shared.exceptions import LocationStateNotAllowedError


# ── Despacho: estados de origen que bloquean la salida ───────────────────────

@pytest.mark.parametrize(
    "blocking_state",
    ["maintenance", "blocked", "restricted", "archived"],
    ids=["maintenance", "blocked", "restricted", "archived"],
)
@pytest.mark.django_db
def test_dispatch_fails_for_all_blocking_origin_states(
    blocking_state, almacenista_user, sample_product, sample_locations
):
    """BR-14: cualquier estado bloqueante en el origen impide el despacho."""
    loc = sample_locations[0]
    loc.operational_status = blocking_state
    loc.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)

    with pytest.raises(LocationStateNotAllowedError):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            1,
            MovementType.SALIDA_VENTA_MENOR,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


# ── Entrada: estados de destino que bloquean la recepción ────────────────────

@pytest.mark.parametrize(
    "blocking_state",
    ["archived", "blocked"],
    ids=["archived", "blocked"],
)
@pytest.mark.django_db
def test_entry_fails_for_blocking_destination_states(
    blocking_state, almacenista_user, sample_product, sample_locations
):
    """BR-14: destinos en estado archivado o bloqueado rechazan entradas."""
    loc = sample_locations[0]
    loc.operational_status = blocking_state
    loc.save(update_fields=["operational_status", "updated_at"])

    with pytest.raises(LocationStateNotAllowedError):
        register_entry(
            almacenista_user,
            sample_product.id,
            loc.id,
            3,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


# ── Traslado: estados de destino que bloquean el traslado ────────────────────

@pytest.mark.parametrize(
    "blocking_state",
    ["archived", "blocked"],
    ids=["archived", "blocked"],
)
@pytest.mark.django_db
def test_internal_transfer_fails_for_blocking_destination_states(
    blocking_state, almacenista_user, sample_product, sample_locations
):
    """BR-14: destinos en estado archivado o bloqueado rechazan traslados."""
    origin = sample_locations[0]
    destination = sample_locations[1]
    destination.operational_status = blocking_state
    destination.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(
        product=sample_product, location=origin, current_stock=6
    )

    with pytest.raises(LocationStateNotAllowedError):
        register_internal_transfer(
            almacenista_user,
            sample_product.id,
            origin.id,
            destination.id,
            2,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


# ── Entrada: estado mantenimiento y restringido permiten entrada ──────────────

@pytest.mark.parametrize(
    "permissive_state",
    ["maintenance", "restricted"],
    ids=["maintenance", "restricted"],
)
@pytest.mark.django_db
def test_entry_allowed_for_permissive_destination_states(
    permissive_state, almacenista_user, sample_product, sample_locations
):
    """BR-14: mantenimiento y restricted permiten recibir mercancía en el destino."""
    loc = sample_locations[0]
    loc.operational_status = permissive_state
    loc.save(update_fields=["operational_status", "updated_at"])

    movement = register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        2,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert movement.destination_location_id == loc.id
