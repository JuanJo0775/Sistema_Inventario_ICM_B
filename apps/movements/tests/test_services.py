from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.inventory.models import StockByLocation
from apps.movements.models import Movement, MovementType
from apps.movements.services import (
    correct_movement_within_window,
    ledger_net_quantity_for_location,
    register_adjustment,
    register_dispatch,
    register_entry,
    register_internal_transfer,
    register_return,
)
from shared.exceptions import (
    AdjustmentJustificationRequiredError,
    CrossValidationFailedError,
    DiscrepancyNoteRequiredError,
    LocationStateNotAllowedError,
    ProductNotReturnableError,
    SerialNumberRequiredError,
)
from tests.factories import ElectroCategoryFactory, LotFactory, ProductFactory


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
def test_entry_with_lot_persists_lot_on_movement(almacenista_user, sample_locations):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="PRD-0100", requires_expiration=True)
    loc = sample_locations[0]
    lot = LotFactory(
        product=product,
        code="L001",
        expiration_date=timezone.now().date() + timedelta(days=90),
    )
    movement = register_entry(
        almacenista_user,
        product.id,
        loc.id,
        8,
        lot_code=lot.code,
        lot_expiration_date=lot.expiration_date,
        serial_number="SN-LOT",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert movement.lot_id == lot.id
    assert movement.lot.code == "L001"


@pytest.mark.django_db
def test_dispatch_chooses_earliest_lot_when_expiring_product(
    almacenista_user, sample_locations
):
    from datetime import timedelta

    from django.utils import timezone

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="PRD-0200", requires_expiration=True)
    loc = sample_locations[0]
    lot_early = LotFactory(
        product=product,
        code="L-EARLY",
        expiration_date=timezone.now().date() + timedelta(days=15),
    )
    lot_late = LotFactory(
        product=product,
        code="L-LATE",
        expiration_date=timezone.now().date() + timedelta(days=90),
    )
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        10,
        lot_code=lot_late.code,
        lot_expiration_date=lot_late.expiration_date,
        serial_number="SN-LATE",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        8,
        lot_code=lot_early.code,
        lot_expiration_date=lot_early.expiration_date,
        serial_number="SN-EARLY",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    movements = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        3,
        MovementType.SALIDA_VENTA_MENOR,
        scanned_code=product.barcode,
        order_sku=product.sku,
        serial_number="SN-DSP",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    # should produce at least one movement; the earliest lot is consumed first
    assert isinstance(movements, list)
    assert movements[0].lot_id == lot_early.id


@pytest.mark.django_db
def test_entry_electroterapia_without_serial_fails(almacenista_user, sample_locations):
    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="ELEC-0001")
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


@pytest.mark.django_db
def test_dispatch_consumes_across_multiple_lots(almacenista_user, sample_locations):
    """FEFO multi-lote: consumir cantidad mayor que la del lote más temprano.

    Crea dos lotes (early, late) y entradas; solicita despacho que requiere
    consumir parte de ambos lotes y verifica que el primer movimiento
    corresponde al lote con vencimiento más cercano.
    """
    from datetime import timedelta

    from django.utils import timezone

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="PRD-0300", requires_expiration=True)
    loc = sample_locations[0]
    lot_early = LotFactory(
        product=product,
        code="L-EARLY-2",
        expiration_date=timezone.now().date() + timedelta(days=10),
    )
    lot_late = LotFactory(
        product=product,
        code="L-LATE-2",
        expiration_date=timezone.now().date() + timedelta(days=90),
    )
    # entry: late then early (order shouldn't matter for FEFO)
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        10,
        lot_code=lot_late.code,
        lot_expiration_date=lot_late.expiration_date,
        serial_number="SN-LATE-2",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        8,
        lot_code=lot_early.code,
        lot_expiration_date=lot_early.expiration_date,
        serial_number="SN-EARLY-2",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    # Ensure InvoiceCounter exists to avoid invoice_number uniqueness collisions in tests
    from apps.movements.models import InvoiceCounter

    InvoiceCounter.objects.all().delete()
    InvoiceCounter.objects.create(last_number=1000000)

    # dispatch 12 should consume 8 from early, 4 from late
    from unittest.mock import patch as _patch

    with _patch("apps.movements.services.generate_invoice_number", return_value=None):
        movements = register_dispatch(
            almacenista_user,
            product.id,
            loc.id,
            12,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=product.barcode,
            order_sku=product.sku,
            serial_number="SN-DSP-2",
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )
    assert isinstance(movements, list)
    assert len(movements) == 2
    # first movement must take from earliest-expiring lot
    assert movements[0].lot_id == lot_early.id
    assert movements[0].quantity == 8
    assert movements[1].lot_id == lot_late.id
    assert movements[1].quantity == 4


@pytest.mark.django_db
def test_dispatch_single_movement_nonexpiring_product(
    almacenista_user, sample_product, sample_locations
):
    """Producto sin vencimiento: despacho genera un único movimiento y ajusta stock.

    Esto cubre el comportamiento FIFO en el sentido de que sin lotes el sistema
    crea un único movimiento que reduce el `StockByLocation` correctamente.
    """
    loc = sample_locations[0]
    # Ensure initial stock
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=15
    )
    # Ensure InvoiceCounter safe state
    from apps.movements.models import InvoiceCounter as IC2

    IC2.objects.all().delete()
    IC2.objects.create(last_number=2000000)

    from unittest.mock import patch as _patch2

    with _patch2("apps.movements.services.generate_invoice_number", return_value=None):
        movements = register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            5,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=sample_product.barcode,
            order_sku=sample_product.sku,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )
    assert isinstance(movements, list)
    assert len(movements) == 1
    m = movements[0]
    assert m.quantity == 5
    row = StockByLocation.objects.get(product=sample_product, location=loc)
    assert row.current_stock == 10


@pytest.mark.django_db
def test_dispatch_fails_when_origin_location_is_in_maintenance(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    loc.operational_status = "maintenance"
    loc.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )

    with pytest.raises(LocationStateNotAllowedError):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            1,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=sample_product.barcode,
            order_sku=sample_product.sku,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


@pytest.mark.django_db
def test_entry_allows_destination_location_in_maintenance(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    loc.operational_status = "maintenance"
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


@pytest.mark.django_db
def test_internal_transfer_fails_when_destination_is_blocked(
    almacenista_user, sample_product, sample_locations
):
    origin, destination = sample_locations[0], sample_locations[1]
    destination.operational_status = "blocked"
    destination.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(
        product=sample_product,
        location=origin,
        current_stock=6,
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


# ── Edge cases: archived ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_entry_fails_when_destination_is_archived(
    almacenista_user, sample_product, sample_locations
):
    """Archived location blocks all inbound stock (entry)."""
    loc = sample_locations[0]
    loc.operational_status = "archived"
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


@pytest.mark.django_db
def test_dispatch_fails_when_origin_is_archived(
    almacenista_user, sample_product, sample_locations
):
    """Archived location blocks all outbound stock (dispatch)."""
    loc = sample_locations[0]
    loc.operational_status = "archived"
    loc.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )

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


@pytest.mark.django_db
def test_return_fails_when_destination_is_archived(almacenista_user, sample_locations):
    """Archived location blocks returns (destination check)."""
    from tests.factories import CategoryFactory, ProductFactory

    cat = CategoryFactory(is_returnable=True)
    product = ProductFactory(category=cat)
    loc = sample_locations[0]
    loc.operational_status = "archived"
    loc.save(update_fields=["operational_status", "updated_at"])

    with pytest.raises(LocationStateNotAllowedError):
        register_return(
            almacenista_user,
            product.id,
            loc.id,
            1,
        )


@pytest.mark.django_db
def test_return_fails_when_destination_is_blocked(almacenista_user, sample_locations):
    """Blocked location blocks returns (destination check)."""
    from tests.factories import CategoryFactory, ProductFactory

    cat = CategoryFactory(is_returnable=True)
    product = ProductFactory(category=cat)
    loc = sample_locations[0]
    loc.operational_status = "blocked"
    loc.save(update_fields=["operational_status", "updated_at"])

    with pytest.raises(LocationStateNotAllowedError):
        register_return(
            almacenista_user,
            product.id,
            loc.id,
            1,
        )


# ── Edge cases: restricted ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_dispatch_fails_when_origin_is_restricted(
    almacenista_user, sample_product, sample_locations
):
    """Restricted location blocks dispatch from origin."""
    loc = sample_locations[0]
    loc.operational_status = "restricted"
    loc.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )

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


@pytest.mark.django_db
def test_entry_allows_destination_in_restricted(
    almacenista_user, sample_product, sample_locations
):
    """Restricted location still accepts inbound stock (only origin is blocked)."""
    loc = sample_locations[0]
    loc.operational_status = "restricted"
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
