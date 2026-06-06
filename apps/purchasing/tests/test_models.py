"""Tests de modelos del módulo de compras: constraints, propiedades y validaciones."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.purchasing.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    Reception,
    ReceptionItem,
    ReceptionStatus,
    Supplier,
)
from tests.factories import LocationFactory, ProductFactory

from .factories import (
    PurchaseOrderFactory,
    PurchaseOrderItemFactory,
    ReceptionFactory,
    ReceptionItemFactory,
    SupplierFactory,
)


# ---------------------------------------------------------------------------
# Supplier model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_supplier_str():
    supplier = SupplierFactory(nombre_comercial="ICM Supplies", nit="900000001-1")
    assert "ICM Supplies" in str(supplier)
    assert "900000001-1" in str(supplier)


@pytest.mark.django_db
def test_supplier_nit_unique_constraint():
    SupplierFactory(nit="123456789-0")
    with pytest.raises(IntegrityError):
        Supplier.objects.create(
            nombre_comercial="Duplicado",
            razon_social="Duplicado S.A.S.",
            nit="123456789-0",
        )


@pytest.mark.django_db
def test_supplier_default_is_active():
    supplier = SupplierFactory()
    assert supplier.is_active is True


@pytest.mark.django_db
def test_supplier_uuid_pk():
    supplier = SupplierFactory()
    import uuid
    assert isinstance(supplier.id, uuid.UUID)


# ---------------------------------------------------------------------------
# PurchaseOrder model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_purchase_order_default_status():
    po = PurchaseOrderFactory()
    assert po.status == PurchaseOrderStatus.BORRADOR


@pytest.mark.django_db
def test_purchase_order_is_editable_only_in_borrador():
    po_borrador = PurchaseOrderFactory(status=PurchaseOrderStatus.BORRADOR)
    po_pendiente = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    po_completada = PurchaseOrderFactory(status=PurchaseOrderStatus.COMPLETADA)
    po_cancelada = PurchaseOrderFactory(status=PurchaseOrderStatus.CANCELADA)

    assert po_borrador.is_editable is True
    assert po_pendiente.is_editable is False
    assert po_completada.is_editable is False
    assert po_cancelada.is_editable is False


@pytest.mark.django_db
def test_purchase_order_is_receivable():
    po_pendiente = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    po_parcial = PurchaseOrderFactory(status=PurchaseOrderStatus.PARCIALMENTE_RECIBIDA)
    po_borrador = PurchaseOrderFactory(status=PurchaseOrderStatus.BORRADOR)
    po_cancelada = PurchaseOrderFactory(status=PurchaseOrderStatus.CANCELADA)

    assert po_pendiente.is_receivable is True
    assert po_parcial.is_receivable is True
    assert po_borrador.is_receivable is False
    assert po_cancelada.is_receivable is False


@pytest.mark.django_db
def test_purchase_order_number_unique():
    PurchaseOrderFactory(number="OC-9999")
    with pytest.raises(IntegrityError):
        PurchaseOrder.objects.create(
            number="OC-9999",
            supplier=SupplierFactory(),
            status=PurchaseOrderStatus.BORRADOR,
            created_by=None,
        )


# ---------------------------------------------------------------------------
# PurchaseOrderItem model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_poi_quantity_pending_property():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=10, quantity_received=3)
    assert poi.quantity_pending == 7


@pytest.mark.django_db
def test_poi_is_fully_received_true():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=5, quantity_received=5)
    assert poi.is_fully_received is True


@pytest.mark.django_db
def test_poi_is_fully_received_false():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=5, quantity_received=3)
    assert poi.is_fully_received is False


@pytest.mark.django_db
def test_poi_unique_together_product_per_po():
    po = PurchaseOrderFactory()
    product = ProductFactory()
    PurchaseOrderItemFactory(purchase_order=po, product=product)
    with pytest.raises(IntegrityError):
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity_ordered=5,
            unit_cost="10000",
        )


@pytest.mark.django_db
def test_poi_quantity_ordered_check_constraint():
    po = PurchaseOrderFactory()
    product = ProductFactory()
    with pytest.raises(Exception):
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity_ordered=0,
            unit_cost="5000",
        )


# ---------------------------------------------------------------------------
# Reception model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reception_default_status():
    reception = ReceptionFactory()
    assert reception.status == ReceptionStatus.BORRADOR


@pytest.mark.django_db
def test_reception_is_editable_only_borrador():
    r_borrador = ReceptionFactory(status=ReceptionStatus.BORRADOR)
    r_confirmada = ReceptionFactory(status=ReceptionStatus.CONFIRMADA)
    r_cancelada = ReceptionFactory(status=ReceptionStatus.CANCELADA)

    assert r_borrador.is_editable is True
    assert r_confirmada.is_editable is False
    assert r_cancelada.is_editable is False


# ---------------------------------------------------------------------------
# ReceptionItem model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reception_item_quantity_expected_property():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=8, quantity_received=2)
    reception = ReceptionFactory(purchase_order=po)
    item = ReceptionItemFactory(reception=reception, purchase_order_item=poi, quantity_received=3)
    # quantity_expected = ordered - received_so_far = 8 - 2 = 6
    assert item.quantity_expected == 6


@pytest.mark.django_db
def test_reception_item_has_discrepancy_true():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=10, quantity_received=0)
    reception = ReceptionFactory(purchase_order=po)
    item = ReceptionItemFactory(
        reception=reception,
        purchase_order_item=poi,
        quantity_received=7,
        discrepancy_note="Solo 7 disponibles",
    )
    assert item.has_discrepancy is True


@pytest.mark.django_db
def test_reception_item_has_discrepancy_false_when_matches_ordered():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po, quantity_ordered=10, quantity_received=0)
    reception = ReceptionFactory(purchase_order=po)
    item = ReceptionItemFactory(
        reception=reception,
        purchase_order_item=poi,
        quantity_received=10,
        discrepancy_note="",
    )
    assert item.has_discrepancy is False


@pytest.mark.django_db
def test_reception_item_unique_together_per_reception():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po)
    reception = ReceptionFactory(purchase_order=po)
    ReceptionItemFactory(reception=reception, purchase_order_item=poi)
    with pytest.raises(IntegrityError):
        ReceptionItem.objects.create(
            reception=reception,
            purchase_order_item=poi,
            quantity_received=1,
        )
