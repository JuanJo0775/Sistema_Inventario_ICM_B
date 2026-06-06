"""Factories para tests del módulo de compras."""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory

from apps.purchasing.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    Reception,
    ReceptionItem,
    ReceptionStatus,
    Supplier,
)
from tests.factories import AlmacenistaFactory, LocationFactory, ProductFactory


class SupplierFactory(DjangoModelFactory):
    class Meta:
        model = Supplier

    nombre_comercial = factory.Sequence(lambda n: f"Proveedor {n} S.A.S.")
    razon_social = factory.LazyAttribute(lambda o: o.nombre_comercial)
    nit = factory.Sequence(lambda n: f"9{n:08d}-{n%9}")
    contacto = factory.Faker("name")
    correo = factory.LazyAttribute(lambda o: f"contacto@proveedor{o.nit[:3]}.com")
    telefono = factory.Sequence(lambda n: f"30{n:08d}")
    ciudad = "Bogotá"
    is_active = True


class PurchaseOrderFactory(DjangoModelFactory):
    class Meta:
        model = PurchaseOrder

    number = factory.Sequence(lambda n: f"OC-{n:04d}")
    supplier = factory.SubFactory(SupplierFactory)
    status = PurchaseOrderStatus.BORRADOR
    created_by = factory.SubFactory(AlmacenistaFactory)


class PurchaseOrderItemFactory(DjangoModelFactory):
    class Meta:
        model = PurchaseOrderItem

    purchase_order = factory.SubFactory(PurchaseOrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity_ordered = 10
    unit_cost = "15000.0000"
    quantity_received = 0


class ReceptionFactory(DjangoModelFactory):
    class Meta:
        model = Reception

    purchase_order = factory.SubFactory(
        PurchaseOrderFactory,
        status=PurchaseOrderStatus.PENDIENTE,
    )
    status = ReceptionStatus.BORRADOR
    destination_location = factory.SubFactory(LocationFactory)
    received_by = factory.SubFactory(AlmacenistaFactory)


class ReceptionItemFactory(DjangoModelFactory):
    class Meta:
        model = ReceptionItem

    reception = factory.SubFactory(ReceptionFactory)
    purchase_order_item = factory.SubFactory(PurchaseOrderItemFactory)
    quantity_received = 5
    lot_code = ""
    discrepancy_note = ""
