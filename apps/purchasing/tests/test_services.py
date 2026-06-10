"""Tests de servicios del módulo de compras."""

from __future__ import annotations

import pytest

from apps.audit.models import AuditEventType, AuditLog
from apps.inventory.models import StockByLocation
from apps.movements.models import Movement, MovementType
from apps.purchasing.exceptions import (
    InvalidPOStatusTransitionError,
    POCancellationReasonRequiredError,
    POHasConfirmedReceptionsError,
    POItemQuantityExceededError,
    PONotReceivableError,
    PurchaseOrderImmutableError,
    ReceptionDiscrepancyNoteRequiredError,
    ReceptionAllocationQuantityMismatchError,
    ReceptionEmptyError,
    ReceptionNotInBorradorError,
    SupplierInactiveError,
    SupplierNITDuplicateError,
)
from apps.purchasing.models import PurchaseOrderStatus, ReceptionStatus
from apps.purchasing.services import (
    activate_supplier,
    cancel_purchase_order,
    cancel_reception,
    confirm_purchase_order,
    confirm_reception,
    create_purchase_order,
    create_reception,
    create_supplier,
    deactivate_supplier,
    update_supplier,
)
from tests.factories import AlmacenistaFactory, LocationFactory, ProductFactory

from .factories import (
    PurchaseOrderFactory,
    PurchaseOrderItemFactory,
    ReceptionFactory,
    ReceptionItemFactory,
    ReceptionItemAllocationFactory,
    SupplierFactory,
)

# ---------------------------------------------------------------------------
# Supplier tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_supplier_valid(almacenista_user):
    supplier = create_supplier(
        almacenista_user,
        {
            "nombre_comercial": "Distribuidora ICM",
            "razon_social": "Distribuidora ICM S.A.S.",
            "nit": "900123456-1",
            "correo": "info@icm.com",
        },
    )
    assert supplier.pk is not None
    assert supplier.nit == "900123456-1"
    assert AuditLog.objects.filter(event_type=AuditEventType.SUPPLIER_CREATED).exists()


@pytest.mark.django_db
def test_create_supplier_duplicate_nit_raises(almacenista_user):
    SupplierFactory(nit="900000001-1")
    with pytest.raises(SupplierNITDuplicateError):
        create_supplier(
            almacenista_user,
            {"nombre_comercial": "Otro", "nit": "900000001-1"},
        )


@pytest.mark.django_db
def test_deactivate_supplier(almacenista_user):
    supplier = SupplierFactory(is_active=True)
    deactivate_supplier(almacenista_user, supplier.id)
    supplier.refresh_from_db()
    assert not supplier.is_active
    assert AuditLog.objects.filter(
        event_type=AuditEventType.SUPPLIER_DEACTIVATED
    ).exists()


@pytest.mark.django_db
def test_activate_supplier(almacenista_user):
    supplier = SupplierFactory(is_active=False)
    activate_supplier(almacenista_user, supplier.id)
    supplier.refresh_from_db()
    assert supplier.is_active


@pytest.mark.django_db
def test_update_supplier_changes_fields(almacenista_user):
    supplier = SupplierFactory(ciudad="Cali")
    updated = update_supplier(almacenista_user, supplier.id, {"ciudad": "Medellín"})
    assert updated.ciudad == "Medellín"


@pytest.mark.django_db
def test_create_supplier_without_nit(almacenista_user):
    supplier = create_supplier(
        almacenista_user,
        {"nombre_comercial": "Importadora Internacional", "pais": "México"},
    )
    assert supplier.pk is not None
    assert supplier.nit is None


@pytest.mark.django_db
def test_patch_supplier_without_nit_preserves_existing(almacenista_user):
    supplier = SupplierFactory(nit="900000001-1")
    updated = update_supplier(almacenista_user, supplier.id, {"ciudad": "Medellín"})
    updated.refresh_from_db()
    assert updated.nit == "900000001-1"


@pytest.mark.django_db
def test_patch_supplier_with_empty_nit_clears_value(almacenista_user):
    supplier = SupplierFactory(nit="900000001-1")
    updated = update_supplier(almacenista_user, supplier.id, {"nit": ""})
    updated.refresh_from_db()
    assert updated.nit is None


# ---------------------------------------------------------------------------
# PurchaseOrder tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_purchase_order(almacenista_user):
    supplier = SupplierFactory()
    product = ProductFactory()
    po = create_purchase_order(
        almacenista_user,
        {
            "supplier_id": supplier.id,
            "items": [
                {"product_id": product.id, "quantity_ordered": 5, "unit_cost": "10000"}
            ],
        },
    )
    assert po.status == PurchaseOrderStatus.BORRADOR
    assert po.items.count() == 1
    assert po.number.startswith("OC-")
    assert AuditLog.objects.filter(
        event_type=AuditEventType.PURCHASE_ORDER_CREATED
    ).exists()


@pytest.mark.django_db
def test_create_po_with_inactive_supplier_raises(almacenista_user):
    supplier = SupplierFactory(is_active=False)
    product = ProductFactory()
    with pytest.raises(SupplierInactiveError):
        create_purchase_order(
            almacenista_user,
            {
                "supplier_id": supplier.id,
                "items": [
                    {
                        "product_id": product.id,
                        "quantity_ordered": 1,
                        "unit_cost": "5000",
                    }
                ],
            },
        )


@pytest.mark.django_db
def test_confirm_po_changes_status(almacenista_user):
    po = PurchaseOrderFactory(created_by=almacenista_user)
    PurchaseOrderItemFactory(purchase_order=po)
    confirm_purchase_order(almacenista_user, po.id)
    po.refresh_from_db()
    assert po.status == PurchaseOrderStatus.PENDIENTE
    assert po.confirmed_by == almacenista_user
    assert AuditLog.objects.filter(
        event_type=AuditEventType.PURCHASE_ORDER_CONFIRMED
    ).exists()


@pytest.mark.django_db
def test_confirm_already_pendiente_raises(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    with pytest.raises(InvalidPOStatusTransitionError):
        confirm_purchase_order(almacenista_user, po.id)


@pytest.mark.django_db
def test_cancel_po_borrador(almacenista_user):
    po = PurchaseOrderFactory(created_by=almacenista_user)
    cancel_purchase_order(almacenista_user, po.id, reason="No se necesita")
    po.refresh_from_db()
    assert po.status == PurchaseOrderStatus.CANCELADA
    assert po.cancellation_reason == "No se necesita"


@pytest.mark.django_db
def test_cancel_po_requires_reason(almacenista_user):
    po = PurchaseOrderFactory()
    with pytest.raises(POCancellationReasonRequiredError):
        cancel_purchase_order(almacenista_user, po.id, reason="")


@pytest.mark.django_db
def test_cancel_po_completada_raises(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.COMPLETADA)
    with pytest.raises(InvalidPOStatusTransitionError):
        cancel_purchase_order(almacenista_user, po.id, reason="Motivo válido")


@pytest.mark.django_db
def test_cancel_po_with_confirmed_reception_raises(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    ReceptionFactory(purchase_order=po, status=ReceptionStatus.CONFIRMADA)
    with pytest.raises(POHasConfirmedReceptionsError):
        cancel_purchase_order(almacenista_user, po.id, reason="Motivo válido")


# ---------------------------------------------------------------------------
# Reception tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_reception_borrador(almacenista_user):
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=10)
    location = LocationFactory(name="Bodega Test", code="bodega-test")

    reception = create_reception(
        almacenista_user,
        po.id,
        {
            "destination_location_id": location.id,
            "items": [
                {
                    "purchase_order_item_id": poi.id,
                    "quantity_received": 5,
                }
            ],
        },
    )

    assert reception.status == ReceptionStatus.BORRADOR
    assert reception.items.count() == 1
    assert AuditLog.objects.filter(event_type=AuditEventType.RECEPTION_CREATED).exists()


@pytest.mark.django_db
def test_create_reception_po_not_receivable_raises(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.BORRADOR)
    location = LocationFactory(name="Loc Test", code="loc-test")
    with pytest.raises(PONotReceivableError):
        create_reception(
            almacenista_user,
            po.id,
            {"destination_location_id": location.id, "items": []},
        )


@pytest.mark.django_db
def test_create_reception_exceeds_quantity_raises(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=5)
    location = LocationFactory(name="Loc Test2", code="loc-test2")
    with pytest.raises(POItemQuantityExceededError):
        create_reception(
            almacenista_user,
            po.id,
            {
                "destination_location_id": location.id,
                "items": [{"purchase_order_item_id": poi.id, "quantity_received": 10}],
            },
        )


@pytest.mark.django_db
def test_confirm_reception_creates_movements_and_updates_stock(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    location = LocationFactory(name="Bodega Confirm", code="bodega-confirm")
    reception = ReceptionFactory(
        purchase_order=po,
        destination_location=location,
        received_by=almacenista_user,
    )
    ReceptionItemFactory(
        reception=reception,
        purchase_order_item=poi,
        quantity_received=10,
    )

    confirm_reception(almacenista_user, reception.id)

    reception.refresh_from_db()
    assert reception.status == ReceptionStatus.CONFIRMADA

    # Stock actualizado
    stock = StockByLocation.objects.get(product=product, location=location)
    assert stock.current_stock == 10

    # Movement ENTRADA creado
    assert Movement.objects.filter(
        product=product,
        movement_type=MovementType.ENTRADA,
        destination_location=location,
        quantity=10,
    ).exists()

    # PO.status actualizado
    po.refresh_from_db()
    assert po.status == PurchaseOrderStatus.COMPLETADA

    assert AuditLog.objects.filter(
        event_type=AuditEventType.RECEPTION_CONFIRMED
    ).exists()


@pytest.mark.django_db
def test_confirm_reception_partial_marks_po_partial(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=20
    )
    location = LocationFactory(name="Bodega Parcial", code="bodega-parcial")
    reception = ReceptionFactory(
        purchase_order=po,
        destination_location=location,
        received_by=almacenista_user,
    )
    ReceptionItemFactory(
        reception=reception,
        purchase_order_item=poi,
        quantity_received=5,
        discrepancy_note="Solo llegaron 5 unidades",
    )

    confirm_reception(almacenista_user, reception.id)

    po.refresh_from_db()
    assert po.status == PurchaseOrderStatus.PARCIALMENTE_RECIBIDA


@pytest.mark.django_db
def test_confirm_reception_partial_second_delivery_matches_pending_without_note(
    almacenista_user,
):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=20, quantity_received=5
    )
    location = LocationFactory(
        name="Bodega Segunda Parcial", code="bodega-segunda-parcial"
    )
    reception = create_reception(
        almacenista_user,
        po.id,
        {
            "destination_location_id": location.id,
            "items": [
                {
                    "purchase_order_item_id": poi.id,
                    "quantity_received": 15,
                }
            ],
        },
    )

    confirm_reception(almacenista_user, reception.id)

    po.refresh_from_db()
    poi.refresh_from_db()
    assert po.status == PurchaseOrderStatus.COMPLETADA
    assert poi.quantity_received == 20


@pytest.mark.django_db
def test_confirm_reception_discrepancy_requires_note(almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    location = LocationFactory(name="Bodega Disc", code="bodega-disc")
    reception = ReceptionFactory(
        purchase_order=po,
        destination_location=location,
        received_by=almacenista_user,
    )
    ReceptionItemFactory(
        reception=reception,
        purchase_order_item=poi,
        quantity_received=7,
        discrepancy_note="",
    )

    with pytest.raises(ReceptionDiscrepancyNoteRequiredError):
        confirm_reception(almacenista_user, reception.id)


@pytest.mark.django_db
def test_confirm_reception_is_atomic_on_error(almacenista_user, monkeypatch):
    """Si register_entry falla, rollback total: ni stock ni Movement ni Reception.status cambian."""
    from apps.movements import services as mvt_services

    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=5
    )
    location = LocationFactory(name="Bodega Atomic", code="bodega-atomic")
    reception = ReceptionFactory(
        purchase_order=po,
        destination_location=location,
        received_by=almacenista_user,
    )
    ReceptionItemFactory(
        reception=reception, purchase_order_item=poi, quantity_received=5
    )

    def explode(*args, **kwargs):
        raise RuntimeError("Simulated failure in register_entry")

    monkeypatch.setattr(mvt_services, "register_entry", explode)

    with pytest.raises(RuntimeError):
        confirm_reception(almacenista_user, reception.id)

    reception.refresh_from_db()
    assert reception.status == ReceptionStatus.BORRADOR
    assert not StockByLocation.objects.filter(
        product=product, location=location
    ).exists()


@pytest.mark.django_db
def test_confirm_reception_unit_cost_flows_to_movement(almacenista_user):
    """BR-021: el costo de compra del POI queda congelado en Movement.unit_cost."""
    from decimal import Decimal

    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=5, unit_cost="12500.5000"
    )
    location = LocationFactory(name="Bodega Cost", code="bodega-cost")
    reception = ReceptionFactory(
        purchase_order=po,
        destination_location=location,
        received_by=almacenista_user,
    )
    ReceptionItemFactory(
        reception=reception, purchase_order_item=poi, quantity_received=5
    )

    confirm_reception(almacenista_user, reception.id)

    from apps.movements.models import Movement, MovementType

    movement = Movement.objects.get(
        product=product,
        movement_type=MovementType.ENTRADA,
        destination_location=location,
    )
    assert movement.unit_cost == Decimal("12500.5000")


@pytest.mark.django_db
def test_confirm_reception_advanced_distribution_by_lots_and_locations(
    almacenista_user,
):
    from datetime import timedelta

    from apps.catalog.models import Lot
    from django.utils import timezone

    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory(requires_expiration=True)
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    lot_a = Lot.objects.create(
        product=product,
        code="LOTE-A",
        expiration_date=timezone.now().date() + timedelta(days=90),
    )
    lot_b = Lot.objects.create(
        product=product,
        code="LOTE-B",
        expiration_date=timezone.now().date() + timedelta(days=180),
    )
    b1 = LocationFactory(name="Bodega 1", code="bodega-1-adv")
    b2 = LocationFactory(name="Bodega 2", code="bodega-2-adv")
    vit = LocationFactory(name="Vitrina", code="vitrina-adv")

    reception = create_reception(
        almacenista_user,
        po.id,
        {
            "destination_location_id": vit.id,
            "items": [
                {
                    "purchase_order_item_id": poi.id,
                    "quantity_received": 10,
                    "allocations": [
                        {
                            "location_id": b1.id,
                            "quantity_received": 2,
                            "lot_code": lot_a.code,
                            "lot_expiration_date": lot_a.expiration_date,
                        },
                        {
                            "location_id": b2.id,
                            "quantity_received": 3,
                            "lot_code": lot_a.code,
                            "lot_expiration_date": lot_a.expiration_date,
                        },
                        {
                            "location_id": vit.id,
                            "quantity_received": 5,
                            "lot_code": lot_b.code,
                            "lot_expiration_date": lot_b.expiration_date,
                        },
                    ],
                }
            ],
        },
    )

    confirm_reception(almacenista_user, reception.id)

    assert Movement.objects.filter(
        product=product, movement_type=MovementType.ENTRADA
    ).count() == 3
    assert (
        StockByLocation.objects.get(product=product, location=b1).current_stock == 2
    )
    assert (
        StockByLocation.objects.get(product=product, location=b2).current_stock == 3
    )
    assert (
        StockByLocation.objects.get(product=product, location=vit).current_stock == 5
    )
    assert Movement.objects.filter(product=product, lot=lot_a).count() == 2
    assert Movement.objects.filter(product=product, lot=lot_b).count() == 1


@pytest.mark.django_db
def test_confirm_reception_advanced_distribution_by_locations_only(
    almacenista_user,
):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    b1 = LocationFactory(name="Bodega 1", code="bodega-1-loc")
    b2 = LocationFactory(name="Bodega 2", code="bodega-2-loc")
    vit = LocationFactory(name="Vitrina", code="vitrina-loc")

    reception = create_reception(
        almacenista_user,
        po.id,
        {
            "destination_location_id": vit.id,
            "items": [
                {
                    "purchase_order_item_id": poi.id,
                    "quantity_received": 10,
                    "allocations": [
                        {"location_id": b1.id, "quantity_received": 2},
                        {"location_id": b2.id, "quantity_received": 2},
                        {"location_id": vit.id, "quantity_received": 6},
                    ],
                }
            ],
        },
    )

    confirm_reception(almacenista_user, reception.id)

    assert (
        StockByLocation.objects.get(product=product, location=b1).current_stock == 2
    )
    assert (
        StockByLocation.objects.get(product=product, location=b2).current_stock == 2
    )
    assert (
        StockByLocation.objects.get(product=product, location=vit).current_stock == 6
    )
    assert (
        Movement.objects.filter(
            product=product, movement_type=MovementType.ENTRADA
        ).count()
        == 3
    )


@pytest.mark.django_db
def test_create_reception_advanced_distribution_requires_matching_quantity(
    almacenista_user,
):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    location = LocationFactory(name="Bodega Qty", code="bodega-qty")

    with pytest.raises(ReceptionAllocationQuantityMismatchError):
        create_reception(
            almacenista_user,
            po.id,
            {
                "destination_location_id": location.id,
                "items": [
                    {
                        "purchase_order_item_id": poi.id,
                        "quantity_received": 10,
                        "allocations": [
                            {"location_id": location.id, "quantity_received": 4}
                        ],
                    }
                ],
            },
        )


@pytest.mark.django_db
def test_confirm_already_confirmed_reception_raises(almacenista_user):
    reception = ReceptionFactory(status=ReceptionStatus.CONFIRMADA)
    with pytest.raises(ReceptionNotInBorradorError):
        confirm_reception(almacenista_user, reception.id)


@pytest.mark.django_db
def test_cancel_reception_borrador(almacenista_user):
    reception = ReceptionFactory(status=ReceptionStatus.BORRADOR)
    cancel_reception(almacenista_user, reception.id)
    reception.refresh_from_db()
    assert reception.status == ReceptionStatus.CANCELADA
    assert AuditLog.objects.filter(
        event_type=AuditEventType.RECEPTION_CANCELLED
    ).exists()


@pytest.mark.django_db
def test_cancel_confirmed_reception_raises(almacenista_user):
    reception = ReceptionFactory(status=ReceptionStatus.CONFIRMADA)
    with pytest.raises(ReceptionNotInBorradorError):
        cancel_reception(almacenista_user, reception.id)
