"""Implementaciones Gherkin — RF005-RF009 (Movimientos: entradas, despachos, traslados, devoluciones, ajustes)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.movements.models import MovementType
from apps.movements.services import register_internal_transfer

# Datos de cliente mayorista reutilizados en RF006 y RF010
_MAJEUR_CD = {
    "customer_name": "Mayorista SA",
    "customer_email": "mayor@example.com",
    "customer_phone": "3001112233",
    "customer_address": "Carrera 1 # 2-3",
    "privacy_notice_acknowledged": True,
}


def _entry_payload(product_id, location_id, **extra):
    base = {
        "product_id": str(product_id),
        "location_id": str(location_id),
        "quantity": 3,
        "cold_chain_acknowledged": True,
        "electrical_safety_acknowledged": True,
    }
    base.update(extra)
    return base


def _create_transfer(
    api_client: APIClient, user, product, origin, destination, quantity: int
):
    from apps.inventory.models import StockByLocation

    api_client.force_authenticate(user=user)
    StockByLocation.objects.create(product=product, location=origin, current_stock=10)
    url = reverse("movements-transfers")
    return api_client.post(
        url,
        {
            "product_id": str(product.id),
            "origin_id": str(origin.id),
            "destination_id": str(destination.id),
            "quantity": quantity,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )


# --- RF-005 (API movimientos / entradas) ------------------------------------


def impl_rf005_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations
):
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(sample_product.id, loc.id, serial_number="SN-RF005-01"),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf005_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations
):
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(
            sample_product.id, loc.id, qty_invoiced=5, serial_number="SN-RF005-02"
        ),
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf005_s03(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations
):
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(
            sample_product.id,
            loc.id,
            quantity=4,
            qty_invoiced=5,
            discrepancy_note="Faltó una unidad",
            serial_number="SN-RF005-03",
        ),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf005_s04(authenticated_almacenista_client: APIClient, sample_locations, db):
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0004")
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(p.id, loc.id),
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf005_s05(authenticated_almacenista_client: APIClient, sample_locations, db):
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0005")
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(p.id, loc.id, serial_number="SN-ELEC-OK"),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf005_s06(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations
):
    loc = sample_locations[0]
    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        _entry_payload(
            sample_product.id,
            loc.id,
            scanned_code=sample_product.barcode,
            serial_number="SN-RF005-06",
        ),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf005_s07(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations
):
    loc = sample_locations[0]
    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        _entry_payload(sample_product.id, loc.id, serial_number="SN-RF005-07"),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


# --- RF-006 -----------------------------------------------------------------


def impl_rf006_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=20
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-DESP-MAY",
            "customer_data": _MAJEUR_CD,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data.get("invoice_number")


def impl_rf006_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "scanned_code": sample_product.barcode,
            "order_sku": "OTRO-SKU-999",
            "serial_number": "SN-X",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf006_s03(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "serial_number": "SN-MIN",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf006_s04(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_DANO,
            "note": "Empaque roto",
            "serial_number": "SN-DANO",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf006_s05(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENCIMIENTO,
            "serial_number": "SN-VENC",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf006_s06(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    sample_product.weight_grams = 500000
    sample_product.save(update_fields=["weight_grams"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-RF006-06",
            "customer_data": _MAJEUR_CD,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data["invoice_number"]


def impl_rf006_s07(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "serial_number": "SN-RF006-07",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


# --- RF-007 -----------------------------------------------------------------


def impl_rf007_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    a, b = sample_locations[0], sample_locations[1]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=a, current_stock=8)
    url = reverse("movements-transfers")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "origin_id": str(a.id),
            "destination_id": str(b.id),
            "quantity": 2,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf007_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    a, b = sample_locations[0], sample_locations[1]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=a, current_stock=2)
    url = reverse("movements-transfers")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "origin_id": str(a.id),
            "destination_id": str(b.id),
            "quantity": 9,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_409_CONFLICT


def impl_rf007_s03(almacenista_user, sample_product, sample_locations, db):
    a = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=a, current_stock=3)
    with pytest.raises(ValueError, match="distintos"):
        register_internal_transfer(
            almacenista_user,
            sample_product.id,
            a.id,
            a.id,
            1,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )


def impl_rf007_s04(
    api_client: APIClient, auxiliar_user, sample_product, sample_locations, db
):
    a, b = sample_locations[0], sample_locations[1]
    r = _create_transfer(api_client, auxiliar_user, sample_product, a, b, 3)
    assert r.status_code == status.HTTP_201_CREATED
    from apps.movements.models import Movement

    original = Movement.objects.get(pk=r.data["id"])
    corrected_at = original.created_at + timedelta(minutes=2)
    with patch("django.utils.timezone.now", return_value=corrected_at):
        corr = api_client.post(
            reverse("movements-corrections", kwargs={"pk": original.id}),
            {"origin_id": str(a.id), "destination_id": str(b.id), "quantity": 2},
            format="json",
        )
    assert corr.status_code == status.HTTP_201_CREATED
    assert Movement.objects.filter(related_movement=original).exists()


def impl_rf007_s05(
    api_client: APIClient, auxiliar_user, sample_product, sample_locations, db
):
    a, b = sample_locations[0], sample_locations[1]
    r = _create_transfer(api_client, auxiliar_user, sample_product, a, b, 3)
    assert r.status_code == status.HTTP_201_CREATED
    from apps.movements.models import Movement

    original = Movement.objects.get(pk=r.data["id"])
    corrected_at = original.created_at + timedelta(minutes=6)
    with patch("django.utils.timezone.now", return_value=corrected_at):
        corr = api_client.post(
            reverse("movements-corrections", kwargs={"pk": original.id}),
            {"origin_id": str(a.id), "destination_id": str(b.id), "quantity": 2},
            format="json",
        )
    assert corr.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert Movement.objects.filter(related_movement=original).count() == 0


# --- RF-008 / RF-009 --------------------------------------------------------


def impl_rf008_s01(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.catalog.models import ProductSerial
    from tests.factories import (
        ElectroCategoryFactory,
        ProductFactory,
        ProductSerialFactory,
    )

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0001")
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=p, location=loc, current_stock=0)
    # Crear ProductSerial para que la devolución pueda identificarlo
    ProductSerialFactory(
        product=p,
        serial_number="SN-DEVOL",
        current_location=loc,
        status=ProductSerial.Status.DISPATCHED,
    )
    url = reverse("movements-returns")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(p.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-DEVOL",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf008_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=1
    )
    url = reverse("movements-returns")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-NO",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf008_s03(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.catalog.models import ProductSerial
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement
    from tests.factories import (
        ElectroCategoryFactory,
        ProductFactory,
        ProductSerialFactory,
    )

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0803")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=p, location=loc, current_stock=1)
    # Crear serial disponible para el despacho
    ProductSerialFactory(
        product=p,
        serial_number="SN-RET-ORIG",
        current_location=loc,
        status=ProductSerial.Status.AVAILABLE,
    )
    sale = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(p.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "serial_number": "SN-RET-ORIG",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    original = Movement.objects.get(pk=sale.data["id"])
    # Crear serial para la devolución (simula equipo que retorna)
    ProductSerialFactory(
        product=p,
        serial_number="SN-RET-APPROVED",
        current_location=loc,
        status=ProductSerial.Status.DISPATCHED,
    )
    r = authenticated_almacenista_client.post(
        reverse("movements-returns"),
        {
            "product_id": str(p.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-RET-APPROVED",
            "related_movement_id": str(original.id),
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert Movement.objects.filter(related_movement=original).exists()


def impl_rf008_s04(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=3
    )
    r = authenticated_almacenista_client.post(
        reverse("movements-returns"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-RET-REJECT",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        StockByLocation.objects.get(product=sample_product, location=loc).current_stock
        == 3
    )


def impl_rf008_s05(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.catalog.models import ProductSerial
    from apps.inventory.models import StockByLocation
    from tests.factories import (
        ElectroCategoryFactory,
        ProductFactory,
        ProductSerialFactory,
    )

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0805")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=p, location=loc, current_stock=1)
    # Crear serial disponible para el despacho
    ProductSerialFactory(
        product=p,
        serial_number="SN-RET-HIST",
        current_location=loc,
        status=ProductSerial.Status.AVAILABLE,
    )
    sale = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(p.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "serial_number": "SN-RET-HIST",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    original = sale.data["id"]
    # Crear serial para la devolución
    ProductSerialFactory(
        product=p,
        serial_number="SN-RET-HIST-01",
        current_location=loc,
        status=ProductSerial.Status.DISPATCHED,
    )
    return_movement = authenticated_almacenista_client.post(
        reverse("movements-returns"),
        {
            "product_id": str(p.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-RET-HIST-01",
            "related_movement_id": str(original),
        },
        format="json",
    )
    assert return_movement.status_code == status.HTTP_201_CREATED
    r = authenticated_almacenista_client.get(reverse("movements-returns"))
    assert r.status_code == status.HTTP_200_OK
    results = r.data.get("results", r.data)
    assert any(str(item.get("related_movement")) == str(original) for item in results)


def impl_rf009_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    url = reverse("movements-adjustments")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "new_quantity": 8,
            "justification": "Conteo físico diferente",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf009_s02(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    url = reverse("movements-adjustments")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "new_quantity": 9,
            "justification": "   ",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf009_s03(
    api_client: APIClient, auxiliar_user, sample_product, sample_locations, db
):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("movements-adjustments")
    r = api_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "new_quantity": 5,
            "justification": "No permitido",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rf009_s04(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    impl_rf009_s01(
        authenticated_almacenista_client, sample_product, sample_locations, db
    )
    loc = sample_locations[0]
    url = reverse("movements-adjustments")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "new_quantity": 7,
            "justification": "Segundo ajuste corrige conteo anterior",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf009_s05(
    api_client: APIClient, auxiliar_user, sample_product, sample_locations, db
):
    a, b = sample_locations[0], sample_locations[1]
    r = _create_transfer(api_client, auxiliar_user, sample_product, a, b, 4)
    assert r.status_code == status.HTTP_201_CREATED
    from apps.movements.models import Movement

    original = Movement.objects.get(pk=r.data["id"])
    corrected_at = original.created_at + timedelta(minutes=3)
    with patch("django.utils.timezone.now", return_value=corrected_at):
        corr = api_client.post(
            reverse("movements-corrections", kwargs={"pk": original.id}),
            {"origin_id": str(a.id), "destination_id": str(b.id), "quantity": 2},
            format="json",
        )
    assert corr.status_code == status.HTTP_201_CREATED
    assert Movement.objects.filter(related_movement=original).exists()


def impl_rf009_s06(authenticated_almacenista_client: APIClient):
    url = reverse("movements-adjustments")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


IMPLEMENTATIONS: dict[str, object] = {
    "RF005-S01": impl_rf005_s01,
    "RF005-S02": impl_rf005_s02,
    "RF005-S03": impl_rf005_s03,
    "RF005-S04": impl_rf005_s04,
    "RF005-S05": impl_rf005_s05,
    "RF005-S06": impl_rf005_s06,
    "RF005-S07": impl_rf005_s07,
    "RF006-S01": impl_rf006_s01,
    "RF006-S02": impl_rf006_s02,
    "RF006-S03": impl_rf006_s03,
    "RF006-S04": impl_rf006_s04,
    "RF006-S05": impl_rf006_s05,
    "RF006-S06": impl_rf006_s06,
    "RF006-S07": impl_rf006_s07,
    "RF007-S01": impl_rf007_s01,
    "RF007-S02": impl_rf007_s02,
    "RF007-S03": impl_rf007_s03,
    "RF007-S04": impl_rf007_s04,
    "RF007-S05": impl_rf007_s05,
    "RF008-S01": impl_rf008_s01,
    "RF008-S02": impl_rf008_s02,
    "RF008-S03": impl_rf008_s03,
    "RF008-S04": impl_rf008_s04,
    "RF008-S05": impl_rf008_s05,
    "RF009-S01": impl_rf009_s01,
    "RF009-S02": impl_rf009_s02,
    "RF009-S03": impl_rf009_s03,
    "RF009-S04": impl_rf009_s04,
    "RF009-S05": impl_rf009_s05,
    "RF009-S06": impl_rf009_s06,
}
