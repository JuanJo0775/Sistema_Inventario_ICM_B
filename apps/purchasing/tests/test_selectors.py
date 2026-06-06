"""Tests de selectores del módulo de compras (sin side effects)."""

from __future__ import annotations

import pytest

from apps.purchasing.models import PurchaseOrderStatus, ReceptionStatus
from apps.purchasing.selectors import (
    get_purchase_order,
    get_purchase_orders,
    get_reception,
    get_receptions,
    get_supplier,
    get_suppliers,
)

from .factories import (
    PurchaseOrderFactory,
    PurchaseOrderItemFactory,
    ReceptionFactory,
    ReceptionItemFactory,
    SupplierFactory,
)

# ---------------------------------------------------------------------------
# Supplier selectors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_suppliers_returns_all():
    SupplierFactory.create_batch(3)
    qs = get_suppliers()
    assert qs.count() >= 3


@pytest.mark.django_db
def test_get_suppliers_filter_active():
    SupplierFactory(is_active=True)
    SupplierFactory(is_active=True)
    SupplierFactory(is_active=False)
    active = get_suppliers(is_active=True)
    inactive = get_suppliers(is_active=False)
    assert all(s.is_active for s in active)
    assert all(not s.is_active for s in inactive)


@pytest.mark.django_db
def test_get_suppliers_ordered_by_nombre_comercial():
    SupplierFactory(nombre_comercial="Zeta Supplies")
    SupplierFactory(nombre_comercial="Alpha Distribuidora")
    names = [s.nombre_comercial for s in get_suppliers()]
    assert names == sorted(names)


@pytest.mark.django_db
def test_get_supplier_returns_correct_instance():
    supplier = SupplierFactory(nit="999888777-1")
    result = get_supplier(supplier.id)
    assert result.id == supplier.id
    assert result.nit == "999888777-1"


@pytest.mark.django_db
def test_get_supplier_raises_for_nonexistent():
    import uuid

    from django.core.exceptions import ObjectDoesNotExist

    with pytest.raises(ObjectDoesNotExist):
        get_supplier(uuid.uuid4())


# ---------------------------------------------------------------------------
# PurchaseOrder selectors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_purchase_orders_returns_all():
    PurchaseOrderFactory.create_batch(3)
    qs = get_purchase_orders()
    assert qs.count() >= 3


@pytest.mark.django_db
def test_get_purchase_orders_filter_by_status():
    PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    PurchaseOrderFactory(status=PurchaseOrderStatus.BORRADOR)
    PurchaseOrderFactory(status=PurchaseOrderStatus.CANCELADA)
    result = get_purchase_orders(status=PurchaseOrderStatus.PENDIENTE)
    assert all(po.status == PurchaseOrderStatus.PENDIENTE for po in result)


@pytest.mark.django_db
def test_get_purchase_orders_filter_by_supplier():
    s1 = SupplierFactory()
    s2 = SupplierFactory()
    PurchaseOrderFactory(supplier=s1)
    PurchaseOrderFactory(supplier=s1)
    PurchaseOrderFactory(supplier=s2)
    result = get_purchase_orders(supplier_id=s1.id)
    assert result.count() == 2
    assert all(po.supplier_id == s1.id for po in result)


@pytest.mark.django_db
def test_get_purchase_order_prefetches_items():
    po = PurchaseOrderFactory()
    PurchaseOrderItemFactory.create_batch(2, purchase_order=po)
    result = get_purchase_order(po.id)
    # Prefetch already loaded — accessing items should not hit DB again
    assert result.items.count() == 2


@pytest.mark.django_db
def test_get_purchase_order_includes_receptions():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    ReceptionFactory(purchase_order=po)
    result = get_purchase_order(po.id)
    assert result.receptions.count() == 1


# ---------------------------------------------------------------------------
# Reception selectors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_receptions_returns_all():
    ReceptionFactory.create_batch(2)
    qs = get_receptions()
    assert qs.count() >= 2


@pytest.mark.django_db
def test_get_receptions_filter_by_po():
    po1 = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    po2 = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    ReceptionFactory(purchase_order=po1)
    ReceptionFactory(purchase_order=po1)
    ReceptionFactory(purchase_order=po2)
    result = get_receptions(po_id=po1.id)
    assert result.count() == 2
    assert all(r.purchase_order_id == po1.id for r in result)


@pytest.mark.django_db
def test_get_receptions_filter_by_status():
    ReceptionFactory(status=ReceptionStatus.CONFIRMADA)
    ReceptionFactory(status=ReceptionStatus.BORRADOR)
    result = get_receptions(status=ReceptionStatus.CONFIRMADA)
    assert all(r.status == ReceptionStatus.CONFIRMADA for r in result)


@pytest.mark.django_db
def test_get_reception_prefetches_items():
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    poi = PurchaseOrderItemFactory(purchase_order=po)
    reception = ReceptionFactory(purchase_order=po)
    ReceptionItemFactory(reception=reception, purchase_order_item=poi)
    result = get_reception(reception.id)
    assert result.items.count() == 1


@pytest.mark.django_db
def test_get_reception_select_related_supplier():
    reception = ReceptionFactory()
    result = get_reception(reception.id)
    # select_related chain: reception → purchase_order → supplier
    assert result.purchase_order.supplier is not None
