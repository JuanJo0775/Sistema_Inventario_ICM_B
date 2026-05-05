from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.inventory.models import StockByLocation
from apps.movements.models import Movement, MovementType
from apps.movements.services import (correct_movement_within_window,
                                     ledger_net_quantity_for_location,
                                     register_adjustment, register_dispatch,
                                     register_entry,
                                     register_internal_transfer,
                                     register_return)
from shared.exceptions import (AdjustmentJustificationRequiredError,
                               CrossValidationFailedError,
                               DiscrepancyNoteRequiredError,
                               ProductNotReturnableError,
                               SerialNumberRequiredError)
from tests.factories import ElectroCategoryFactory, ProductFactory


@pytest.mark.django_db
def test_entry_increments_stock_and_creates_ledger_record(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    m = register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        5,
        serial_number="SN-1",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert m.movement_type == MovementType.ENTRADA
    row = StockByLocation.objects.get(product=sample_product, location=loc)
    assert row.current_stock == 5


@pytest.mark.django_db
def test_entry_electroterapia_without_serial_fails(almacenista_user, sample_locations):
    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="CAN-ELEC-00001")
    loc = sample_locations[0]
    with pytest.raises(SerialNumberRequiredError):
        register_entry(
            almacenista_user,
            p.id,
            loc.id,
            1,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


@pytest.mark.django_db
def test_entry_discrepancy_note_required_when_qty_mismatch(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    with pytest.raises(DiscrepancyNoteRequiredError):
        register_entry(
            almacenista_user,
            sample_product.id,
            loc.id,
            5,
            qty_invoiced=4,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


@pytest.mark.django_db
def test_dispatch_cross_validation_fails_wrong_sku(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    with pytest.raises(CrossValidationFailedError):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            1,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=sample_product.barcode,
            order_sku="OTRO-SKU",
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


@pytest.mark.django_db
def test_internal_transfer_does_not_change_global_stock(
    almacenista_user, sample_product, sample_locations
):
    a, b = sample_locations[0], sample_locations[1]
    StockByLocation.objects.create(product=sample_product, location=a, current_stock=10)
    before_total = sum(
        StockByLocation.objects.filter(product=sample_product).values_list(
            "current_stock", flat=True
        )
    )
    register_internal_transfer(
        almacenista_user,
        sample_product.id,
        a.id,
        b.id,
        4,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    after_total = sum(
        StockByLocation.objects.filter(product=sample_product).values_list(
            "current_stock", flat=True
        )
    )
    assert before_total == after_total


@pytest.mark.django_db
def test_return_blocked_for_non_returnable_category(
    almacenista_user, sample_product, sample_locations
):
    assert sample_product.category.is_returnable is False
    loc = sample_locations[0]
    with pytest.raises(ProductNotReturnableError):
        register_return(
            almacenista_user, sample_product.id, loc.id, 1, serial_number="SN"
        )


@pytest.mark.django_db
def test_adjustment_requires_justification(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    with pytest.raises(AdjustmentJustificationRequiredError):
        register_adjustment(almacenista_user, sample_product.id, loc.id, 3, "   ")


@pytest.mark.django_db
def test_stock_can_be_reconstructed_from_ledger(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        7,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    cached = StockByLocation.objects.get(
        product=sample_product, location=loc
    ).current_stock
    rebuilt = ledger_net_quantity_for_location(
        product_id=sample_product.id, location_id=loc.id
    )
    assert rebuilt == cached == 7


@pytest.mark.django_db
def test_correction_within_window_creates_reversal_and_fixed(
    almacenista_user, sample_product, sample_locations
):
    a, b = sample_locations[0], sample_locations[1]
    StockByLocation.objects.create(product=sample_product, location=a, current_stock=10)
    m = register_internal_transfer(
        almacenista_user,
        sample_product.id,
        a.id,
        b.id,
        3,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    fixed_time = m.created_at + timedelta(seconds=30)
    with patch("django.utils.timezone.now", return_value=fixed_time):
        out = correct_movement_within_window(
            almacenista_user,
            m.id,
            {"origin_id": a.id, "destination_id": b.id, "quantity": 2},
        )
    assert len(out) == 2
    assert Movement.objects.filter(related_movement=m).exists()
