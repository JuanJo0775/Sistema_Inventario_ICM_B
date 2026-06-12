from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.catalog.models import ProductSerial
from apps.inventory.models import StockByLocation
from apps.movements.models import Movement, MovementType
from apps.movements.services import (
    _normalize_serial,
    _validate_serial_required,
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
    ImmutableRecordError,
    InsufficientStockError,
    LocationStateNotAllowedError,
    LotCodeRequiredError,
    LotExpirationDateRequiredError,
    ProductNotReturnableError,
    SerialNumberRequiredError,
)
from tests.factories import (
    ElectroCategoryFactory,
    LocationFactory,
    LotFactory,
    ProductFactory,
    ProductSerialFactory,
)


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
            almacenista_user,
            sample_product.id,
            loc.id,
            1,
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


@pytest.mark.django_db
def test_register_entry_raises_lot_code_required_for_expiring_product(
    almacenista_user, sample_locations
):
    """Fix #1: omitir lot_code en producto con requires_expiration=True debe lanzar
    LotCodeRequiredError (422), no InsufficientStockError (409)."""
    product = ProductFactory(requires_expiration=True, sku="EXP-0001")
    loc = sample_locations[0]

    with pytest.raises(LotCodeRequiredError):
        register_entry(
            almacenista_user,
            product.id,
            loc.id,
            5,
            # lot_code deliberadamente omitido
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


@pytest.mark.django_db
def test_register_entry_raises_lot_expiration_date_required(
    almacenista_user, sample_locations
):
    """Fix #1: omitir lot_expiration_date en producto con requires_expiration=True debe lanzar
    LotExpirationDateRequiredError (422)."""
    product = ProductFactory(requires_expiration=True, sku="EXP-0002")
    loc = sample_locations[0]

    with pytest.raises(LotExpirationDateRequiredError):
        register_entry(
            almacenista_user,
            product.id,
            loc.id,
            5,
            lot_code="L-TEST",
            lot_expiration_date=None,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


# ── BR-06: corrección dentro de ventana (ENTRADA y SALIDA) ───────────────────


@pytest.mark.django_db
def test_correct_entrada_within_window(
    almacenista_user, sample_product, sample_locations
):
    """BR-06 — Corrección de ENTRADA: reversal + nueva entrada con cantidad corregida."""
    loc_a, loc_b = sample_locations[0], sample_locations[1]

    original = register_entry(
        almacenista_user,
        sample_product.id,
        loc_a.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert original.movement_type == MovementType.ENTRADA

    stock_before = StockByLocation.objects.get(
        product=sample_product, location=loc_a
    ).current_stock
    assert stock_before == 10

    fixed_time = original.created_at + timedelta(seconds=45)
    with patch("django.utils.timezone.now", return_value=fixed_time):
        result = correct_movement_within_window(
            almacenista_user,
            original.id,
            {"location_id": loc_a.id, "quantity": 7},
        )

    assert len(result) == 2
    reversal, corrected = result
    # El reversal debe ser SALIDA_DANO (undo de la entrada original)
    assert reversal.movement_type == MovementType.SALIDA_DANO
    assert reversal.related_movement == original
    # El corregido debe ser una nueva ENTRADA
    assert corrected.movement_type == MovementType.ENTRADA
    assert corrected.quantity == 7

    # El ledger original no se modificó (inmutabilidad)
    original.refresh_from_db()
    assert original.quantity == 10

    # Stock neto debe reflejar la corrección: 10 - 10 + 7 = 7
    stock_after = StockByLocation.objects.get(
        product=sample_product, location=loc_a
    ).current_stock
    assert stock_after == 7


@pytest.mark.django_db
def test_correct_salida_within_window(
    almacenista_user, sample_product, sample_locations
):
    """BR-06 — Corrección de SALIDA_VENTA_MENOR: reversal + nueva salida con cantidad corregida."""
    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=20
    )

    dispatches = register_dispatch(
        almacenista_user,
        sample_product.id,
        loc.id,
        8,
        MovementType.SALIDA_VENTA_MENOR,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
        privacy_notice_acknowledged=True,
    )
    original = dispatches[0] if isinstance(dispatches, list) else dispatches
    assert original.movement_type == MovementType.SALIDA_VENTA_MENOR

    # Stock tras dispatch: 20 - 8 = 12
    stock_mid = StockByLocation.objects.get(
        product=sample_product, location=loc
    ).current_stock
    assert stock_mid == 12

    fixed_time = original.created_at + timedelta(seconds=60)
    with patch("django.utils.timezone.now", return_value=fixed_time):
        result = correct_movement_within_window(
            almacenista_user,
            original.id,
            {
                "location_id": loc.id,
                "quantity": 5,
                "movement_type": MovementType.SALIDA_VENTA_MENOR,
            },
        )

    assert len(result) == 2
    reversal, corrected = result
    # El reversal restituye el stock (ENTRADA interna)
    assert reversal.movement_type == MovementType.ENTRADA
    assert reversal.related_movement == original
    # La corrección es una nueva SALIDA con cantidad 5
    assert corrected.movement_type == MovementType.SALIDA_VENTA_MENOR
    assert corrected.quantity == 5

    # Stock neto: 12 + 8 (reversal) - 5 (nueva salida) = 15
    stock_final = StockByLocation.objects.get(
        product=sample_product, location=loc
    ).current_stock
    assert stock_final == 15


@pytest.mark.django_db
def test_correct_movement_outside_window_raises(
    almacenista_user, sample_product, sample_locations
):
    """BR-06 — Corrección fuera de la ventana de 5 minutos debe lanzar ImmutableRecordError."""
    loc = sample_locations[0]
    original = register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        5,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    expired_time = original.created_at + timedelta(minutes=6)
    with patch("django.utils.timezone.now", return_value=expired_time):
        with pytest.raises(ImmutableRecordError):
            correct_movement_within_window(
                almacenista_user,
                original.id,
                {"location_id": loc.id, "quantity": 3},
            )


@pytest.mark.django_db
def test_dispatch_raises_insufficient_stock_when_stock_is_zero(
    almacenista_user, sample_product, sample_locations
):
    from shared.exceptions import InsufficientStockError

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=0
    )
    with pytest.raises(InsufficientStockError):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            1,
            MovementType.SALIDA_VENTA_MENOR,
        )


@pytest.mark.django_db
def test_dispatch_raises_insufficient_stock_when_quantity_exceeds_stock(
    almacenista_user, sample_product, sample_locations
):
    from shared.exceptions import InsufficientStockError

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=2
    )
    with pytest.raises(InsufficientStockError):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            5,
            MovementType.SALIDA_VENTA_MENOR,
        )


@pytest.mark.django_db
def test_register_entry_rolls_back_on_movement_save_failure(
    almacenista_user, sample_product, sample_locations
):
    from unittest.mock import patch

    from apps.movements.models import Movement

    loc = sample_locations[0]
    with patch.object(
        Movement.objects, "create", side_effect=RuntimeError("DB error simulated")
    ):
        with pytest.raises(RuntimeError):
            register_entry(almacenista_user, sample_product.id, loc.id, 5)
    assert not Movement.objects.filter(
        product=sample_product, destination_location=loc
    ).exists()
    row = StockByLocation.objects.filter(product=sample_product, location=loc).first()
    assert row is None or row.current_stock == 0


# ── Serial helpers unit tests ────────────────────────────────────────────────


@pytest.mark.django_db
def test_normalize_serial_none():
    assert _normalize_serial(None) is None


@pytest.mark.django_db
def test_normalize_serial_empty_string():
    assert _normalize_serial("") is None


@pytest.mark.django_db
def test_normalize_serial_whitespace_only():
    assert _normalize_serial("   ") is None


@pytest.mark.django_db
def test_normalize_serial_strips_whitespace():
    assert _normalize_serial("  SN-123  ") == "SN-123"


@pytest.mark.django_db
def test_normalize_serial_preserves_content():
    assert _normalize_serial("SN-001") == "SN-001"


@pytest.mark.django_db
def test_validate_serial_required_raises_when_missing(db):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="VAL-SER")
    with pytest.raises(SerialNumberRequiredError):
        _validate_serial_required(product, None)


@pytest.mark.django_db
def test_validate_serial_required_raises_when_empty(db):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="VAL-SER2")
    with pytest.raises(SerialNumberRequiredError):
        _validate_serial_required(product, "")


@pytest.mark.django_db
def test_validate_serial_required_raises_when_whitespace(db):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="VAL-SER3")
    with pytest.raises(SerialNumberRequiredError):
        _validate_serial_required(product, "   ")


@pytest.mark.django_db
def test_validate_serial_required_passes_with_serial(db):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="VAL-SER4")
    _validate_serial_required(product, "SN-OK")


@pytest.mark.django_db
def test_validate_serial_required_passes_when_not_required(db):
    product = ProductFactory(sku="VAL-SER5")
    _validate_serial_required(product, None)


# ── BR-04: Serial en Traslados ────────────────────────────────────────────────


@pytest.mark.django_db
def test_internal_transfer_electroterapia_without_serial_fails(
    almacenista_user, sample_locations
):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="TRF-SER-01")
    origin, destination = sample_locations[0], sample_locations[1]
    StockByLocation.objects.create(product=product, location=origin, current_stock=10)
    with pytest.raises(InsufficientStockError):
        register_internal_transfer(
            almacenista_user,
            product.id,
            origin.id,
            destination.id,
            3,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


@pytest.mark.django_db
def test_internal_transfer_with_serial_persists(almacenista_user, sample_locations):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="TRF-SER-02")
    origin, destination = sample_locations[0], sample_locations[1]
    StockByLocation.objects.create(product=product, location=origin, current_stock=10)
    serial = ProductSerialFactory(
        product=product,
        serial_number="SN-TRF-01",
        current_location=origin,
        status=ProductSerial.Status.AVAILABLE,
    )
    movement = register_internal_transfer(
        almacenista_user,
        product.id,
        origin.id,
        destination.id,
        3,
        serial_id=serial.id,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert movement.serial_number == "SN-TRF-01"
    assert movement.movement_type == MovementType.TRASLADO


@pytest.mark.django_db
def test_internal_transfer_serial_optional_when_not_required(
    almacenista_user, sample_product, sample_locations
):
    origin, destination = sample_locations[0], sample_locations[1]
    StockByLocation.objects.create(
        product=sample_product, location=origin, current_stock=10
    )
    movement = register_internal_transfer(
        almacenista_user,
        sample_product.id,
        origin.id,
        destination.id,
        2,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert movement.serial_number is None


# ── BR-04: Serial en Ajustes ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_adjustment_electroterapia_without_serial_fails(
    almacenista_user, sample_locations
):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="ADJ-SER-01")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=product, location=loc, current_stock=10)
    with pytest.raises(SerialNumberRequiredError):
        register_adjustment(
            almacenista_user,
            product.id,
            loc.id,
            5,
            "Ajuste de prueba",
        )


@pytest.mark.django_db
def test_adjustment_with_serial_persists(almacenista_user, sample_locations):
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="ADJ-SER-02")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=product, location=loc, current_stock=10)
    serial = ProductSerialFactory(
        product=product,
        serial_number="SN-ADJ-01",
        current_location=loc,
        status=ProductSerial.Status.AVAILABLE,
    )
    movement = register_adjustment(
        almacenista_user,
        product.id,
        loc.id,
        5,
        "Ajuste con serial",
        serial_id=serial.id,
    )
    assert movement.serial_number == "SN-ADJ-01"
    assert movement.movement_type == MovementType.AJUSTE


@pytest.mark.django_db
def test_adjustment_downwards_without_serial_optional_when_not_required(
    almacenista_user, sample_product, sample_locations
):
    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    movement = register_adjustment(
        almacenista_user,
        sample_product.id,
        loc.id,
        3,
        "Ajuste sin serial",
    )
    assert movement.serial_number is None
