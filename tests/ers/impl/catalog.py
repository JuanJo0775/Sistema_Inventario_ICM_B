"""Implementaciones Gherkin — RF003 (Catálogo de productos)."""

from __future__ import annotations

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# --- RF-003 (servicios catálogo; API donde aplica) ---------------------------


def impl_rf003_s01(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S1", slug="cat-rf003-s1")
    p = create_product(
        almacenista_user,
        {
            "sku": "RFS-0001",
            "name": "Producto RF003 S1",
            "category_id": cat.id,
        },
    )
    assert p.sku == "RFS-0001"


def impl_rf003_s02(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S2", slug="cat-rf003-s2")
    p = create_product(
        almacenista_user,
        {"sku": "RFS-0002", "name": "Marca Can", "category_id": cat.id, "brand": "Can"},
    )
    assert p.brand.lower() == "can"


def impl_rf003_s03(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import ElectroCategoryFactory

    cat = ElectroCategoryFactory()
    p = create_product(
        almacenista_user,
        {"sku": "RFE-0003", "name": "Electro item", "category_id": cat.id},
    )
    assert p.category.requires_serial_number is True


def impl_rf003_s04(almacenista_user, db):
    from apps.catalog.services import create_product
    from tests.factories import CategoryFactory

    cat = CategoryFactory(name="Cat RF003 S4", slug="cat-rf003-s4")
    p = create_product(
        almacenista_user,
        {
            "sku": "RFB-0004",
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
            "sku": "RFF-0005",
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
        {"sku": "RFA-0006", "name": "A", "category_id": cat.id},
    )
    p2 = create_product(
        almacenista_user,
        {"sku": "RFB-0007", "name": "B", "category_id": cat.id},
    )
    from apps.inventory.models import StockByLocation
    from tests.factories import LocationFactory

    loc = LocationFactory()
    StockByLocation.objects.create(product=p1, location=loc, current_stock=1)
    StockByLocation.objects.create(product=p2, location=loc, current_stock=2)
    combo = create_combo(
        almacenista_user,
        {
            "name": "Kit RF003",
            "sku": "KIT-0001",
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
    r = api_client.post(url, {"sku": "X-1"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


IMPLEMENTATIONS: dict[str, object] = {
    "RF003-S01": impl_rf003_s01,
    "RF003-S02": impl_rf003_s02,
    "RF003-S03": impl_rf003_s03,
    "RF003-S04": impl_rf003_s04,
    "RF003-S05": impl_rf003_s05,
    "RF003-S06": impl_rf003_s06,
    "RF003-S07": impl_rf003_s07,
}
