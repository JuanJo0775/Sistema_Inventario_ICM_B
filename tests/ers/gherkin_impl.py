"""
Ejecución de escenarios Gherkin del ERS (RF/RNF) con contrato API/servicios.

Las funciones registradas en IMPLEMENTATIONS reciben solo fixtures declaradas en su firma.
"""

from __future__ import annotations

import inspect
import csv
from datetime import datetime
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditEventType, AuditLog
from apps.authentication.models import UserRole
from apps.movements.models import MovementType
from apps.movements.services import register_internal_transfer

_BOGOTA = ZoneInfo("America/Bogota")

# --- RF-001 -----------------------------------------------------------------

def impl_rf001_s01(api_client: APIClient, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "testpass123"},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert "access" in r.data and "refresh" in r.data
    assert r.data["user"]["role"] == UserRole.ALMACENISTA


def impl_rf001_s02(api_client: APIClient, auxiliar_user):
    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    url = reverse("token_obtain_pair")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.post(
            url,
            {"username": auxiliar_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["user"]["role"] == UserRole.AUXILIAR_DESPACHO


def impl_rf001_s03(api_client: APIClient, auxiliar_user):
    outer = datetime(2026, 5, 5, 13, 0, 0, tzinfo=_BOGOTA)
    url = reverse("token_obtain_pair")
    with patch("django.utils.timezone.now", return_value=outer):
        r = api_client.post(
            url,
            {"username": auxiliar_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


def impl_rf001_s04(api_client: APIClient, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "MALA_CLAVE"},
        format="json",
    )
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def impl_rf001_s05(api_client: APIClient, administrador_user):
    outer = datetime(2026, 5, 5, 22, 0, 0, tzinfo=_BOGOTA)
    url = reverse("token_obtain_pair")
    with patch("django.utils.timezone.now", return_value=outer):
        r = api_client.post(
            url,
            {"username": administrador_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["user"]["role"] == UserRole.ADMINISTRADOR


# --- RF-002 -----------------------------------------------------------------


def impl_rf002_s01(api_client: APIClient, almacenista_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-users")
    r = api_client.post(
        url,
        {
            "username": "nuevo_gherkin_rf002",
            "email": "nuevo_gherkin_rf002@example.com",
            "password": "secreto12345",
            "role": UserRole.AUXILIAR_DESPACHO,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf002_s02(api_client: APIClient, almacenista_user, auxiliar_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-user-detail", kwargs={"pk": auxiliar_user.pk})
    r = api_client.patch(url, {"password": "otraClaveSegura1"}, format="json")
    assert r.status_code == status.HTTP_200_OK


def impl_rf002_s03(api_client: APIClient, almacenista_user, auxiliar_user):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    u = User.objects.create(
        username="para_deshabilitar_rf002",
        email="para_deshabilitar_rf002@example.com",
        role=UserRole.AUXILIAR_DESPACHO,
    )
    u.set_password("xSecreto99")
    u.save()
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-user-disable", kwargs={"pk": u.pk})
    r = api_client.post(url)
    assert r.status_code == status.HTTP_204_NO_CONTENT
    u.refresh_from_db()
    assert u.is_active is False


def impl_rf002_s04(api_client: APIClient, auxiliar_user):
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("auth-user-detail", kwargs={"pk": auxiliar_user.pk})
    r = api_client.patch(url, {"first_name": "NoDebe"}, format="json")
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rf002_s05(api_client: APIClient, almacenista_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-users")
    r = api_client.post(
        url,
        {
            "username": almacenista_user.username,
            "email": "dup_rf002@example.com",
            "password": "secreto12345",
            "role": UserRole.AUXILIAR_DESPACHO,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_400_BAD_REQUEST


# --- RF-003 (servicios catálogo; API donde aplica) ---------------------------


def impl_rf003_s01(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S1", slug="cat-rf003-s1")
    p = create_product(
        almacenista_user,
        {
            "sku": "CAN-RF003S01-001",
            "name": "Producto RF003 S1",
            "category_id": cat.id,
        },
    )
    assert p.sku.startswith("CAN-")


def impl_rf003_s02(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S2", slug="cat-rf003-s2")
    p = create_product(
        almacenista_user,
        {"sku": "CAN-RF003S02-001", "name": "Marca Can", "category_id": cat.id, "brand": "Can"},
    )
    assert p.brand.lower() == "can"


def impl_rf003_s03(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import ElectroCategoryFactory

    cat = ElectroCategoryFactory()
    p = create_product(
        almacenista_user,
        {
            "sku": "CAN-RF003S03-001",
            "name": "Electro item",
            "category_id": cat.id,
        },
    )
    assert p.category.requires_serial_number is True


def impl_rf003_s04(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S4", slug="cat-rf003-s4")
    p = create_product(
        almacenista_user,
        {
            "sku": "CAN-RF003S04-001",
            "name": "Con barcode",
            "category_id": cat.id,
            "barcode": "8710999000001",
        },
    )
    assert p.barcode == "8710999000001"


def impl_rf003_s05(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S5", slug="cat-rf003-s5")
    p = create_product(
        almacenista_user,
        {
            "sku": "CAN-RF003S05-001",
            "name": "Frío",
            "category_id": cat.id,
            "requires_cold_chain": True,
        },
    )
    assert p.requires_cold_chain is True


def impl_rf003_s06(almacenista_user, db):
    from apps.catalog.services import create_combo, create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S6", slug="cat-rf003-s6")
    p1 = create_product(
        almacenista_user,
        {"sku": "CAN-RF003S6A-001", "name": "A", "category_id": cat.id},
    )
    p2 = create_product(
        almacenista_user,
        {"sku": "CAN-RF003S6B-001", "name": "B", "category_id": cat.id},
    )
    combo = create_combo(
        almacenista_user,
        {
            "name": "Kit RF003",
            "sku": "CAN-KIT-RF003S06",
            "items": [
                {"product_id": str(p1.id), "quantity": 1},
                {"product_id": str(p2.id), "quantity": 2},
            ],
        },
    )
    assert combo.combo_items.count() == 2


def impl_rf003_s07(api_client: APIClient, almacenista_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("catalog-products")
    r = api_client.post(url, {"sku": "CAN-X"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


# --- RF-004 -----------------------------------------------------------------


def impl_rf004_s01(authenticated_almacenista_client: APIClient):
    url = reverse("inventory-full")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK
    assert "results" in r.data


def impl_rf004_s02(authenticated_almacenista_client: APIClient, sample_product):
    url = reverse("inventory-search")
    r = authenticated_almacenista_client.get(url, {"q": sample_product.name[:5]})
    assert r.status_code == status.HTTP_200_OK


def impl_rf004_s03(authenticated_almacenista_client: APIClient, sample_product):
    url = reverse("catalog-resolve")
    r = authenticated_almacenista_client.get(url, {"identifier": sample_product.barcode})
    assert r.status_code == status.HTTP_200_OK


def impl_rf004_s04(authenticated_almacenista_client: APIClient, sample_product):
    impl_rf004_s03(authenticated_almacenista_client, sample_product)


def impl_rf004_s05(authenticated_almacenista_client: APIClient, sample_product):
    url = reverse("inventory-product-stock", kwargs={"product_id": sample_product.id})
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf004_s06(authenticated_almacenista_client: APIClient, sample_product):
    impl_rf004_s05(authenticated_almacenista_client, sample_product)


def impl_rf004_s07(authenticated_almacenista_client: APIClient):
    url = reverse("catalog-resolve")
    r = authenticated_almacenista_client.get(url, {"identifier": "SKU-INEXISTENTE-XYZ999"})
    assert r.status_code == status.HTTP_404_NOT_FOUND


# --- RF-005 (API movimientos / entradas) ------------------------------------


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


def impl_rf005_s01(authenticated_almacenista_client: APIClient, sample_product, sample_locations):
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(sample_product.id, loc.id, serial_number="SN-RF005-01"),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf005_s02(authenticated_almacenista_client: APIClient, sample_product, sample_locations):
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(sample_product.id, loc.id, qty_invoiced=5, serial_number="SN-RF005-02"),
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf005_s03(authenticated_almacenista_client: APIClient, sample_product, sample_locations):
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
    p = ProductFactory(category=cat, sku="CAN-RF005S04-001")
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
    p = ProductFactory(category=cat, sku="CAN-RF005S05-001")
    loc = sample_locations[0]
    url = reverse("movements-entries")
    r = authenticated_almacenista_client.post(
        url,
        _entry_payload(p.id, loc.id, serial_number="SN-ELEC-OK"),
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf005_s06(authenticated_almacenista_client: APIClient, sample_product, sample_locations):
    impl_rf005_s01(authenticated_almacenista_client, sample_product, sample_locations)


def impl_rf005_s07(authenticated_almacenista_client: APIClient, sample_product, sample_locations):
    impl_rf005_s06(authenticated_almacenista_client, sample_product, sample_locations)


# --- RF-006 -----------------------------------------------------------------

_MAJEUR_CD = {
    "customer_name": "Mayorista SA",
    "customer_email": "mayor@example.com",
    "customer_phone": "3001112233",
    "customer_address": "Carrera 1 # 2-3",
    "privacy_notice_acknowledged": True,
}


def impl_rf006_s01(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=20)
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


def impl_rf006_s02(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
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


def impl_rf006_s03(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
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


def impl_rf006_s04(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
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


def impl_rf006_s05(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
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


def impl_rf006_s06(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    sample_product.weight_grams = 500000
    sample_product.save(update_fields=["weight_grams"])
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
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


def impl_rf006_s07(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
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


def impl_rf007_s01(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
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


def impl_rf007_s02(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
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


def _create_transfer(api_client: APIClient, user, product, origin, destination, quantity: int):
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


def impl_rf007_s04(api_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
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


def impl_rf007_s05(api_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
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
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="CAN-RF008S01-001")
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=p, location=loc, current_stock=0)
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


def impl_rf008_s02(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=1)
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
    from apps.inventory.models import StockByLocation
    from tests.factories import ElectroCategoryFactory, ProductFactory
    from apps.movements.models import Movement

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0803")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=p, location=loc, current_stock=1)
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


def impl_rf008_s04(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=3)
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
    assert StockByLocation.objects.get(product=sample_product, location=loc).current_stock == 3


def impl_rf008_s05(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="P-0805")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=p, location=loc, current_stock=1)
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


def impl_rf009_s01(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
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


def impl_rf009_s02(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
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


def impl_rf009_s03(api_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
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


def impl_rf009_s04(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    impl_rf009_s01(authenticated_almacenista_client, sample_product, sample_locations, db)
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


def impl_rf009_s05(api_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
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


# --- RF-010 -----------------------------------------------------------------


def impl_rf010_s01(authenticated_almacenista_client: APIClient):
    from django.utils import timezone

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = timezone.now()
    url = reverse("reports-sales-summary")
    r = authenticated_almacenista_client.get(url, {"start": start.isoformat(), "end": end.isoformat()})
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s02(authenticated_administrador_client: APIClient):
    url = reverse("reports-kpi")
    r = authenticated_administrador_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s04(authenticated_almacenista_client: APIClient):
    from django.utils import timezone

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = timezone.now()
    url = reverse("reports-movements-history")
    r = authenticated_almacenista_client.get(url, {"start": start.isoformat(), "end": end.isoformat()})
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s05(authenticated_almacenista_client: APIClient):
    url = reverse("reports-expiring")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s03(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    sale = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-RF010-03",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    movement = Movement.objects.get(pk=sale.data["id"])
    start = movement.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
    end = movement.created_at
    report = authenticated_almacenista_client.get(
        reverse("reports-movements-history"),
        {"start": start.isoformat(), "end": end.isoformat(), "product_id": str(sample_product.id)},
    )
    assert report.status_code == status.HTTP_200_OK
    rows = report.data
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["id", "movement_type", "product_sku", "quantity", "invoice_number"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "id": row["id"],
                "movement_type": row["movement_type"],
                "product_sku": row["product_sku"],
                "quantity": row["quantity"],
                "invoice_number": row.get("invoice_number") or "",
            }
        )
    csv_output = buffer.getvalue()
    assert str(movement.id) in csv_output
    assert sample_product.sku in csv_output


def impl_rf010_s06(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    sale = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-RF010-06",
            "customer_data": _MAJEUR_CD,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    movement = Movement.objects.get(pk=sale.data["id"])
    history = authenticated_almacenista_client.get(
        reverse("reports-invoices"), {"invoice_number": movement.invoice_number}
    )
    assert history.status_code == status.HTTP_200_OK
    invoice_rows = history.data.get("results", history.data)
    assert any(row["invoice_number"] == movement.invoice_number for row in invoice_rows)
    download = authenticated_almacenista_client.get(
        reverse("movements-dispatch-invoice", kwargs={"pk": movement.id})
    )
    assert download.status_code == status.HTTP_404_NOT_FOUND


def impl_rf010_s07(api_client: APIClient, auxiliar_user):
    from datetime import timezone as dt_timezone

    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    api_client.force_authenticate(user=auxiliar_user)
    start = datetime(2026, 5, 1, tzinfo=dt_timezone.utc)
    end = datetime(2026, 5, 31, tzinfo=dt_timezone.utc)
    url = reverse("reports-sales-summary")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.get(url, {"start": start.isoformat(), "end": end.isoformat()})
    assert r.status_code == status.HTTP_403_FORBIDDEN


# --- RF-011 / RF-012 / RNF ---------------------------------------------------


def impl_rf011_s01(authenticated_almacenista_client: APIClient, sample_product, db):
    from apps.alerts.models import Alert, AlertType

    Alert.objects.create(product=sample_product, alert_type=AlertType.LOW_STOCK, message="bajo", is_resolved=False)
    url = reverse("alerts-list")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf011_s02(authenticated_almacenista_client: APIClient, sample_product, db):
    from datetime import timedelta
    from django.utils import timezone
    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_expiry_alerts_for_product

    sample_product.expiration_date = timezone.now().date() + timedelta(days=60)
    sample_product.save(update_fields=["expiration_date"])
    sync_expiry_alerts_for_product(sample_product.id)
    assert Alert.objects.filter(
        product=sample_product,
        alert_type=AlertType.EXPIRATION_60,
        is_resolved=False,
    ).exists()
    alerts = authenticated_almacenista_client.get(reverse("alerts-list"))
    assert alerts.status_code == status.HTTP_200_OK


def impl_rf011_s03(authenticated_almacenista_client: APIClient, sample_product, db):
    from datetime import timedelta
    from django.utils import timezone
    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_expiry_alerts_for_product

    sample_product.expiration_date = timezone.now().date() + timedelta(days=30)
    sample_product.save(update_fields=["expiration_date"])
    sync_expiry_alerts_for_product(sample_product.id)
    assert Alert.objects.filter(
        product=sample_product,
        alert_type=AlertType.EXPIRATION_30,
        is_resolved=False,
    ).exists()


def impl_rf011_s04(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation

    sample_product.requires_cold_chain = True
    sample_product.save(update_fields=["requires_cold_chain"])
    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=0)
    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-RF011-04",
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf011_s05(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    p = ProductFactory(category=cat, sku="ELE-1105")
    loc = sample_locations[0]
    StockByLocation.objects.create(product=p, location=loc, current_stock=0)
    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(p.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-RF011-05",
            "cold_chain_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf011_s06(authenticated_almacenista_client: APIClient, authenticated_administrador_client: APIClient, sample_product, sample_locations, db):
    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_stock_alerts_for_product
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    sample_product.reorder_point = 10
    sample_product.save(update_fields=["reorder_point"])
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=8)
    sync_stock_alerts_for_product(sample_product.id)
    active = Alert.objects.filter(product=sample_product, alert_type=AlertType.LOW_STOCK, is_resolved=False)
    assert active.exists()
    kpi = authenticated_administrador_client.get(reverse("reports-kpi"))
    assert kpi.status_code == status.HTTP_200_OK
    assert kpi.data["active_alerts_unresolved"] >= 1
    alerts = authenticated_almacenista_client.get(reverse("alerts-list"))
    assert alerts.status_code == status.HTTP_200_OK
    results = alerts.data.get("results", alerts.data)
    assert any(str(item["id"]) == str(active.first().id) for item in results)


def impl_rf011_s07(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_stock_alerts_for_product
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    sample_product.reorder_point = 10
    sample_product.save(update_fields=["reorder_point"])
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=8)
    sync_stock_alerts_for_product(sample_product.id)
    alert = Alert.objects.get(product=sample_product, alert_type=AlertType.LOW_STOCK, is_resolved=False)
    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 5,
            "serial_number": "SN-RF011-07",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    alert.refresh_from_db()
    assert alert.is_resolved is True


def impl_rf012_s01(authenticated_almacenista_client: APIClient, sample_product, sample_locations):
    impl_rf005_s01(authenticated_almacenista_client, sample_product, sample_locations)
    assert AuditLog.objects.filter(event_type=AuditEventType.MOVEMENT_CREATED).exists()


def impl_rf012_s02(api_client: APIClient, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "testpass123"},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert AuditLog.objects.filter(event_type=AuditEventType.LOGIN_SUCCESS).exists()


def impl_rf012_s05(authenticated_almacenista_client: APIClient):
    url = reverse("audit-logs")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf012_s06(api_client: APIClient, auxiliar_user):
    from django.utils import timezone

    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("audit-logs")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.get(url)
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rf012_s03(authenticated_almacenista_client: APIClient, almacenista_user, db):
    create = authenticated_almacenista_client.post(
        reverse("auth-users"),
        {
            "username": "rf012_cred_mgr",
            "email": "rf012_cred_mgr@example.com",
            "password": "secreto12345",
            "role": UserRole.AUXILIAR_DESPACHO,
        },
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    created_id = create.data["id"]
    update = authenticated_almacenista_client.patch(
        reverse("auth-user-detail", kwargs={"pk": created_id}),
        {"password": "otraClave123"},
        format="json",
    )
    assert update.status_code == status.HTTP_200_OK
    disable = authenticated_almacenista_client.post(
        reverse("auth-user-disable", kwargs={"pk": created_id})
    )
    assert disable.status_code == status.HTTP_204_NO_CONTENT
    assert AuditLog.objects.filter(event_type=AuditEventType.USER_CREATED).exists()
    assert AuditLog.objects.filter(event_type=AuditEventType.USER_UPDATED).exists()
    assert AuditLog.objects.filter(event_type=AuditEventType.USER_DISABLED).exists()


def impl_rf012_s04(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="P-1204")
    product.requires_cold_chain = True
    product.save(update_fields=["requires_cold_chain"])
    loc = sample_locations[0]
    StockByLocation.objects.create(product=product, location=loc, current_stock=0)
    entry = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-ACK-1204",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert entry.status_code == status.HTTP_201_CREATED
    movement_id = entry.data["id"]
    assert Movement.objects.filter(pk=movement_id).exists()
    assert AuditLog.objects.filter(
        event_type=AuditEventType.ALERT_ACKNOWLEDGED,
        movement_id=movement_id,
    ).exists()


def impl_rf012_s07(api_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement

    a, b = sample_locations[0], sample_locations[1]
    api_client.force_authenticate(user=auxiliar_user)
    StockByLocation.objects.create(product=sample_product, location=a, current_stock=10)
    create = api_client.post(
        reverse("movements-transfers"),
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
    assert create.status_code == status.HTTP_201_CREATED
    original = Movement.objects.get(pk=create.data["id"])
    corrected_at = original.created_at + timedelta(minutes=2)
    with patch("django.utils.timezone.now", return_value=corrected_at):
        corr = api_client.post(
            reverse("movements-corrections", kwargs={"pk": original.id}),
            {"origin_id": str(a.id), "destination_id": str(b.id), "quantity": 1},
            format="json",
        )
    assert corr.status_code == status.HTTP_201_CREATED
    assert AuditLog.objects.filter(event_type=AuditEventType.MOVEMENT_CREATED).exists()
    assert AuditLog.objects.filter(event_type=AuditEventType.MOVEMENT_CORRECTED).exists()


def impl_rf012_s08(authenticated_almacenista_client: APIClient, almacenista_user, sample_product, sample_locations, db):
    from apps.audit.services import log_event
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    movement = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-IMMUT",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert movement.status_code == status.HTTP_201_CREATED
    audit = log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Movimiento de prueba para inmutabilidad",
        user=almacenista_user,
        detail={"scenario": "RF012-S08"},
    )
    response = authenticated_almacenista_client.patch(
        reverse("audit-log-detail", kwargs={"pk": audit.id}),
        {"description": "modificado"},
        format="json",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert AuditLog.objects.filter(
        event_type=AuditEventType.MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD
    ).exists()


def impl_rnf003_s01(api_client: APIClient):
    from config.settings import production as production_settings

    assert production_settings.SECURE_SSL_REDIRECT is True
    assert production_settings.SESSION_COOKIE_SECURE is True
    assert production_settings.CSRF_COOKIE_SECURE is True
    assert "django.middleware.security.SecurityMiddleware" in production_settings.MIDDLEWARE


def impl_rnf003_s04(authenticated_almacenista_client: APIClient, almacenista_user, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    sale = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-IMM-0034",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    movement = Movement.objects.get(pk=sale.data["id"])
    response = authenticated_almacenista_client.patch(
        reverse("movements-detail", kwargs={"pk": movement.id}),
        {"quantity": 2},
        format="json",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert AuditLog.objects.filter(
        event_type=AuditEventType.MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD
    ).exists()


def impl_rnf004_s02(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation
    import time

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    t0 = time.perf_counter()
    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-RNF004-02",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    elapsed = time.perf_counter() - t0
    assert r.status_code == status.HTTP_201_CREATED
    assert elapsed < 3.0


def impl_rnf004_s03(authenticated_almacenista_client: APIClient, authenticated_administrador_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation
    import time

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    aux_client = APIClient()
    aux_client.force_authenticate(user=auxiliar_user)

    start = time.perf_counter()
    response_1 = authenticated_almacenista_client.get(reverse("inventory-full"))
    elapsed_1 = time.perf_counter() - start

    start = time.perf_counter()
    response_2 = authenticated_administrador_client.get(reverse("reports-kpi"))
    elapsed_2 = time.perf_counter() - start

    start = time.perf_counter()
    response_3 = aux_client.get(reverse("inventory-search"), {"q": sample_product.sku[:3]})
    elapsed_3 = time.perf_counter() - start

    assert response_1.status_code == status.HTTP_200_OK
    assert response_2.status_code == status.HTTP_200_OK
    assert response_3.status_code == status.HTTP_200_OK
    assert elapsed_1 < 3.0
    assert elapsed_2 < 3.0
    assert elapsed_3 < 3.0


def impl_rnf005_s02(api_client: APIClient):
    schema = api_client.get(reverse("schema"), {"format": "json"})
    assert schema.status_code == status.HTTP_200_OK
    data = schema.json()
    paths = data["paths"]
    expected = [
        "/api/v1/auth/users/",
        "/api/v1/movements/entries/",
        "/api/v1/movements/dispatches/",
        "/api/v1/movements/transfers/",
        "/api/v1/reports/sales/summary/",
        "/api/v1/alerts/",
        "/api/v1/audit/",
    ]
    for path in expected:
        assert path in paths


def impl_rnf005_s03(db):
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    architecture = (root / "docs" / "README_ARQUITECTURA.md").read_text(encoding="utf-8")
    assert "services.py" in architecture
    assert "selectors.py" in architecture
    assert "Negocio" in architecture or "Business logic" in architecture


def impl_rnf006_s02(api_client: APIClient, auxiliar_user, sample_product, sample_locations, db):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=5)
    api_client.force_authenticate(user=auxiliar_user)
    response = api_client.get(reverse("reports-invoices"))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def impl_rnf006_s03(db):
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    scenario = (root / "docs" / "test" / "scenarios" / "RNF006-S03.md").read_text(encoding="utf-8")
    ers = (root / "docs" / "ERS_ICM_Requisitos.md").read_text(encoding="utf-8")
    assert "autorización expresa" in scenario.lower()
    assert "no deben ejecutarse" in scenario.lower()
    assert "autorización expresa" in ers.lower()


def impl_rnf003_s02(api_client: APIClient, auxiliar_user):
    from django.utils import timezone

    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("auth-users")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.post(
            url,
            {
                "username": "hack_aux",
                "email": "hack_aux@example.com",
                "password": "secreto12345",
                "role": UserRole.ALMACENISTA,
            },
            format="json",
        )
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rnf003_s03(almacenista_user):
    assert not almacenista_user.password.startswith("plaintext")
    assert len(almacenista_user.password) > 20


def impl_rnf004_s01(authenticated_almacenista_client: APIClient, sample_product):
    import time

    url = reverse("inventory-product-stock", kwargs={"product_id": sample_product.id})
    t0 = time.perf_counter()
    r = authenticated_almacenista_client.get(url)
    elapsed = time.perf_counter() - t0
    assert r.status_code == status.HTTP_200_OK
    assert elapsed < 2.0


def impl_rnf005_s01(api_client: APIClient):
    """Contrato OpenAPI: el esquema es accesible sin autenticación."""
    url = reverse("schema")
    r = api_client.get(url)
    assert r.status_code == status.HTTP_200_OK
    assert r.headers.get("Content-Type", "").startswith("application/vnd.oai.openapi")


def impl_rnf006_s01(authenticated_almacenista_client: APIClient, sample_product, sample_locations, db):
    """Ley 1581: venta mayor sin consentimiento explícito → error de dominio."""
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=sample_product, location=loc, current_stock=10)
    url = reverse("movements-dispatches")
    cd = {k: v for k, v in _MAJEUR_CD.items() if k != "privacy_notice_acknowledged"}
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-1581",
            "customer_data": cd,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


IMPLEMENTATIONS: dict[str, object] = {
    "RF001-S01": impl_rf001_s01,
    "RF001-S02": impl_rf001_s02,
    "RF001-S03": impl_rf001_s03,
    "RF001-S04": impl_rf001_s04,
    "RF001-S05": impl_rf001_s05,
    "RF002-S01": impl_rf002_s01,
    "RF002-S02": impl_rf002_s02,
    "RF002-S03": impl_rf002_s03,
    "RF002-S04": impl_rf002_s04,
    "RF002-S05": impl_rf002_s05,
    "RF003-S01": impl_rf003_s01,
    "RF003-S02": impl_rf003_s02,
    "RF003-S03": impl_rf003_s03,
    "RF003-S04": impl_rf003_s04,
    "RF003-S05": impl_rf003_s05,
    "RF003-S06": impl_rf003_s06,
    "RF003-S07": impl_rf003_s07,
    "RF004-S01": impl_rf004_s01,
    "RF004-S02": impl_rf004_s02,
    "RF004-S03": impl_rf004_s03,
    "RF004-S04": impl_rf004_s04,
    "RF004-S05": impl_rf004_s05,
    "RF004-S06": impl_rf004_s06,
    "RF004-S07": impl_rf004_s07,
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
    "RF010-S01": impl_rf010_s01,
    "RF010-S02": impl_rf010_s02,
    "RF010-S03": impl_rf010_s03,
    "RF010-S04": impl_rf010_s04,
    "RF010-S05": impl_rf010_s05,
    "RF010-S06": impl_rf010_s06,
    "RF010-S07": impl_rf010_s07,
    "RF011-S01": impl_rf011_s01,
    "RF011-S02": impl_rf011_s02,
    "RF011-S03": impl_rf011_s03,
    "RF011-S04": impl_rf011_s04,
    "RF011-S05": impl_rf011_s05,
    "RF011-S06": impl_rf011_s06,
    "RF011-S07": impl_rf011_s07,
    "RF012-S03": impl_rf012_s03,
    "RF012-S04": impl_rf012_s04,
    "RF012-S01": impl_rf012_s01,
    "RF012-S02": impl_rf012_s02,
    "RF012-S05": impl_rf012_s05,
    "RF012-S06": impl_rf012_s06,
    "RF012-S07": impl_rf012_s07,
    "RF012-S08": impl_rf012_s08,
    "RNF003-S01": impl_rnf003_s01,
    "RNF003-S02": impl_rnf003_s02,
    "RNF003-S03": impl_rnf003_s03,
    "RNF003-S04": impl_rnf003_s04,
    "RNF004-S02": impl_rnf004_s02,
    "RNF004-S03": impl_rnf004_s03,
    "RNF004-S01": impl_rnf004_s01,
    "RNF005-S02": impl_rnf005_s02,
    "RNF005-S03": impl_rnf005_s03,
    "RNF005-S01": impl_rnf005_s01,
    "RNF006-S02": impl_rnf006_s02,
    "RNF006-S03": impl_rnf006_s03,
    "RNF006-S01": impl_rnf006_s01,
}


def run_gherkin_scenario(sid: str, request: pytest.FixtureRequest) -> None:
    fn = IMPLEMENTATIONS.get(sid)
    if fn is None:
        pytest.skip(
            f"[{sid}] Automatización pendiente (UI, exportación Excel, concurrencia, "
            f"flujo aprobación devoluciones, etc.). Ver `docs/test/scenarios/{sid}.md`."
        )
    sig = inspect.signature(fn)
    kwargs = {}
    for name in sig.parameters:
        kwargs[name] = request.getfixturevalue(name)
    fn(**kwargs)
