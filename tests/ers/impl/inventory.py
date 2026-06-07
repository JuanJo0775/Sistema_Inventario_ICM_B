"""Implementaciones Gherkin — RF004 (Inventario / consulta de stock + dominio de almacenamiento S08-S18)."""

from __future__ import annotations

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# --- RF-004 S01-S07 ---------------------------------------------------------


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
    r = authenticated_almacenista_client.get(
        url, {"identifier": sample_product.barcode}
    )
    assert r.status_code == status.HTTP_200_OK


def impl_rf004_s04(authenticated_almacenista_client: APIClient, sample_product):
    # Mismo flujo que S03: resolución por código (escaneado o manual es igual backend)
    impl_rf004_s03(authenticated_almacenista_client, sample_product)


def impl_rf004_s05(authenticated_almacenista_client: APIClient, sample_product):
    url = reverse("inventory-product-stock", kwargs={"product_id": sample_product.id})
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf004_s06(authenticated_almacenista_client: APIClient, sample_product):
    # Mismo flujo que S05: ficha de producto con alertas de seguridad eléctrica
    impl_rf004_s05(authenticated_almacenista_client, sample_product)


def impl_rf004_s07(authenticated_almacenista_client: APIClient):
    url = reverse("catalog-resolve")
    r = authenticated_almacenista_client.get(
        url, {"identifier": "SKU-INEXISTENTE-XYZ999"}
    )
    assert r.status_code == status.HTTP_404_NOT_FOUND


# --- RF-004 S08-S18 (dominio de almacenamiento) -----------------------------


def impl_rf004_s08(authenticated_almacenista_client: APIClient, db):
    """Crear tipo de almacenamiento y asignarlo a una ubicacion."""
    r_type = authenticated_almacenista_client.post(
        reverse("inventory-storage-types"),
        {
            "code": "bodega-gherkin-s08",
            "name": "Bodega Gherkin S08",
            "category": "warehouse",
        },
        format="json",
    )
    assert r_type.status_code == status.HTTP_201_CREATED
    storage_type_id = r_type.data["id"]

    r_loc = authenticated_almacenista_client.post(
        reverse("inventory-locations"),
        {"name": "Ubicacion Gherkin S08", "storage_type_id": storage_type_id},
        format="json",
    )
    assert r_loc.status_code == status.HTTP_201_CREATED
    assert r_loc.data["storage_type_code"] == "bodega-gherkin-s08"


def impl_rf004_s09(authenticated_almacenista_client: APIClient, db):
    """Tipo inactivo rechazado al crear ubicacion."""
    r_type = authenticated_almacenista_client.post(
        reverse("inventory-storage-types"),
        {"code": "tipo-inactivo-s09", "name": "Tipo Inactivo S09"},
        format="json",
    )
    assert r_type.status_code == status.HTTP_201_CREATED
    tid = r_type.data["id"]

    authenticated_almacenista_client.delete(
        reverse("inventory-storage-type-detail", kwargs={"pk": tid})
    )

    r_loc = authenticated_almacenista_client.post(
        reverse("inventory-locations"),
        {"name": "Loc Inactiva S09", "storage_type_id": tid},
        format="json",
    )
    assert r_loc.status_code in (400, 422)


def impl_rf004_s10(authenticated_almacenista_client: APIClient, db):
    """Plantilla aplica defaults al crear ubicacion."""
    r_type = authenticated_almacenista_client.post(
        reverse("inventory-storage-types"),
        {"code": "tipo-s10", "name": "Tipo S10"},
        format="json",
    )
    assert r_type.status_code == status.HTTP_201_CREATED

    r_tmpl = authenticated_almacenista_client.post(
        reverse("inventory-storage-templates"),
        {
            "code": "tmpl-s10",
            "name": "Plantilla S10",
            "storage_type_id": r_type.data["id"],
            "defaults": {
                "max_capacity": 40,
                "capacity_mode": "relative_scale",
                "capacity_level": 2,
            },
        },
        format="json",
    )
    assert r_tmpl.status_code == status.HTTP_201_CREATED

    r_loc = authenticated_almacenista_client.post(
        reverse("inventory-locations"),
        {"name": "Loc Template S10", "storage_template_id": r_tmpl.data["id"]},
        format="json",
    )
    assert r_loc.status_code == status.HTTP_201_CREATED
    assert r_loc.data["max_capacity"] == 40
    assert r_loc.data["capacity_mode"] == "relative_scale"
    assert r_loc.data["capacity_level"] == 2


def impl_rf004_s11(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Transicion a mantenimiento bloquea despacho."""
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )

    r_trans = authenticated_almacenista_client.post(
        reverse("inventory-location-state-transitions", kwargs={"pk": loc.id}),
        {"operational_status": "maintenance"},
        format="json",
    )
    assert r_trans.status_code == status.HTTP_200_OK
    assert r_trans.data["operational_status"] == "maintenance"
    assert r_trans.data["is_active"] is True

    r_disp = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": "SALIDA_VENTA_MENOR",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r_disp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf004_s12(authenticated_almacenista_client: APIClient, sample_locations, db):
    """Archivar ubicacion fuerza is_active=False."""
    loc = sample_locations[0]
    r = authenticated_almacenista_client.post(
        reverse("inventory-location-state-transitions", kwargs={"pk": loc.id}),
        {"operational_status": "archived"},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["operational_status"] == "archived"
    assert r.data["is_active"] is False


def impl_rf004_s13(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Ubicacion archivada rechaza entrada de stock."""
    loc = sample_locations[0]
    loc.operational_status = "archived"
    loc.is_active = False
    loc.save(update_fields=["operational_status", "is_active", "updated_at"])

    r = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 2,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rf004_s14(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Ubicacion restringida bloquea despacho pero permite entrada."""
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    loc.operational_status = "restricted"
    loc.save(update_fields=["operational_status", "updated_at"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )

    r_disp = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": "SALIDA_VENTA_MENOR",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r_disp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    r_entry = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 3,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r_entry.status_code == status.HTTP_201_CREATED


def impl_rf004_s15(authenticated_almacenista_client: APIClient, db):
    """Capacidad relativa guardada y expuesta en reporte."""
    r_loc = authenticated_almacenista_client.post(
        reverse("inventory-locations"),
        {
            "name": "Loc Relativa S15",
            "capacity_mode": "relative_scale",
            "capacity_level": 3,
            "capacity_score": 30,
            "occupancy_estimate_pct": 50.0,
        },
        format="json",
    )
    assert r_loc.status_code == status.HTTP_201_CREATED
    assert r_loc.data["capacity_mode"] == "relative_scale"
    assert r_loc.data["capacity_level"] == 3
    assert r_loc.data["capacity_score"] == 30

    r_rep = authenticated_almacenista_client.get(
        reverse("reports-warehouse-utilization")
    )
    assert r_rep.status_code == status.HTTP_200_OK
    row = next(
        (
            item
            for item in r_rep.data["by_location"]
            if item["code"] == r_loc.data["code"]
        ),
        None,
    )
    assert row is not None
    assert row["capacity_level"] == 3


def impl_rf004_s16(authenticated_almacenista_client: APIClient, db):
    """Filtro de inventario por storage_type_id."""
    from apps.inventory.models import Location, StockByLocation, StorageType
    from tests.factories import ProductFactory

    type_a = StorageType.objects.create(
        code="tipo-a-s16", name="Tipo A S16", is_active=True
    )
    type_b = StorageType.objects.create(
        code="tipo-b-s16", name="Tipo B S16", is_active=True
    )

    loc_a = Location.objects.create(
        code="LOC-A-S16", name="Loc A S16", storage_type=type_a, is_active=True
    )
    loc_b = Location.objects.create(
        code="LOC-B-S16", name="Loc B S16", storage_type=type_b, is_active=True
    )

    prod_a = ProductFactory()
    prod_b = ProductFactory()
    StockByLocation.objects.create(product=prod_a, location=loc_a, current_stock=5)
    StockByLocation.objects.create(product=prod_b, location=loc_b, current_stock=3)

    r = authenticated_almacenista_client.get(
        reverse("inventory-full"), {"storage_type_id": str(type_a.id)}
    )
    assert r.status_code == status.HTTP_200_OK
    results = r.data.get("results", [])
    product_ids = [item["product_id"] for item in results]
    assert str(prod_a.id) in product_ids
    assert str(prod_b.id) not in product_ids


def impl_rf004_s17(authenticated_almacenista_client: APIClient, db):
    """Filtro de inventario por estado operativo."""
    from apps.inventory.models import Location, StockByLocation
    from tests.factories import ProductFactory

    loc_active = Location.objects.create(
        code="LOC-ACT-S17",
        name="Loc Active S17",
        operational_status="active",
        is_active=True,
    )
    loc_maint = Location.objects.create(
        code="LOC-MNT-S17",
        name="Loc Maintenance S17",
        operational_status="maintenance",
        is_active=True,
    )
    product = ProductFactory()
    StockByLocation.objects.create(
        product=product, location=loc_active, current_stock=4
    )
    StockByLocation.objects.create(product=product, location=loc_maint, current_stock=2)

    r = authenticated_almacenista_client.get(
        reverse("inventory-full"), {"operational_status": "maintenance"}
    )
    assert r.status_code == status.HTTP_200_OK
    results = r.data.get("results", [])
    assert any(item["product_id"] == str(product.id) for item in results)


def impl_rf004_s18(authenticated_almacenista_client: APIClient, db):
    """Reporte de utilizacion agrupa por tipo de almacenamiento."""
    from apps.inventory.models import Location, StockByLocation, StorageType
    from tests.factories import ProductFactory

    st = StorageType.objects.create(code="tipo-s18", name="Tipo S18", is_active=True)
    loc1 = Location.objects.create(
        code="LOC-S18-1", name="Loc S18 1", storage_type=st, is_active=True
    )
    loc2 = Location.objects.create(
        code="LOC-S18-2", name="Loc S18 2", storage_type=st, is_active=True
    )
    product = ProductFactory()
    StockByLocation.objects.create(product=product, location=loc1, current_stock=10)
    StockByLocation.objects.create(product=product, location=loc2, current_stock=7)

    r = authenticated_almacenista_client.get(reverse("reports-warehouse-utilization"))
    assert r.status_code == status.HTTP_200_OK

    bucket = next(
        (b for b in r.data["by_storage_type"] if b["storage_type_code"] == "tipo-s18"),
        None,
    )
    assert bucket is not None
    assert bucket["locations"] == 2
    assert bucket["occupied_units"] == 17


IMPLEMENTATIONS: dict[str, object] = {
    "RF004-S01": impl_rf004_s01,
    "RF004-S02": impl_rf004_s02,
    "RF004-S03": impl_rf004_s03,
    "RF004-S04": impl_rf004_s04,
    "RF004-S05": impl_rf004_s05,
    "RF004-S06": impl_rf004_s06,
    "RF004-S07": impl_rf004_s07,
    "RF004-S08": impl_rf004_s08,
    "RF004-S09": impl_rf004_s09,
    "RF004-S10": impl_rf004_s10,
    "RF004-S11": impl_rf004_s11,
    "RF004-S12": impl_rf004_s12,
    "RF004-S13": impl_rf004_s13,
    "RF004-S14": impl_rf004_s14,
    "RF004-S15": impl_rf004_s15,
    "RF004-S16": impl_rf004_s16,
    "RF004-S17": impl_rf004_s17,
    "RF004-S18": impl_rf004_s18,
}
