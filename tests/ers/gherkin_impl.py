"""
Ejecución de escenarios Gherkin del ERS (RF/RNF) con contrato API/servicios.

Las funciones registradas en IMPLEMENTATIONS reciben solo fixtures declaradas en su firma.
"""

from __future__ import annotations

import inspect
from datetime import datetime
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
    "RF007-S01": impl_rf007_s01,
    "RF007-S02": impl_rf007_s02,
    "RF007-S03": impl_rf007_s03,
    "RF008-S01": impl_rf008_s01,
    "RF008-S02": impl_rf008_s02,
    "RF009-S01": impl_rf009_s01,
    "RF009-S02": impl_rf009_s02,
    "RF009-S03": impl_rf009_s03,
    "RF009-S04": impl_rf009_s04,
    "RF009-S06": impl_rf009_s06,
    "RF010-S01": impl_rf010_s01,
    "RF010-S02": impl_rf010_s02,
    "RF010-S04": impl_rf010_s04,
    "RF010-S05": impl_rf010_s05,
    "RF010-S07": impl_rf010_s07,
    "RF011-S01": impl_rf011_s01,
    "RF012-S01": impl_rf012_s01,
    "RF012-S02": impl_rf012_s02,
    "RF012-S05": impl_rf012_s05,
    "RF012-S06": impl_rf012_s06,
    "RNF003-S02": impl_rnf003_s02,
    "RNF003-S03": impl_rnf003_s03,
    "RNF004-S01": impl_rnf004_s01,
    "RNF005-S01": impl_rnf005_s01,
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
