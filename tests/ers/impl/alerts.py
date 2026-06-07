"""Implementaciones Gherkin — RF011 (Alertas proactivas)."""

from __future__ import annotations

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# --- RF-011 -----------------------------------------------------------------


def impl_rf011_s01(authenticated_almacenista_client: APIClient, sample_product, db):
    from apps.alerts.models import Alert, AlertType

    Alert.objects.create(
        product=sample_product,
        alert_type=AlertType.LOW_STOCK,
        message="bajo",
        is_resolved=False,
    )
    url = reverse("alerts-list")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf011_s02(authenticated_almacenista_client: APIClient, sample_product, db):
    from datetime import timedelta

    from django.utils import timezone

    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_expiry_alerts_for_product
    from tests.factories import LotFactory

    sample_product.requires_expiration = True
    sample_product.save(update_fields=["requires_expiration"])
    lot = LotFactory(
        product=sample_product,
        code="L-60",
        expiration_date=timezone.now().date() + timedelta(days=60),
    )
    sync_expiry_alerts_for_product(sample_product.id)
    assert Alert.objects.filter(
        product=sample_product,
        lot=lot,
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
    from tests.factories import LotFactory

    sample_product.requires_expiration = True
    sample_product.save(update_fields=["requires_expiration"])
    lot = LotFactory(
        product=sample_product,
        code="L-30",
        expiration_date=timezone.now().date() + timedelta(days=30),
    )
    sync_expiry_alerts_for_product(sample_product.id)
    assert Alert.objects.filter(
        product=sample_product,
        lot=lot,
        alert_type=AlertType.EXPIRATION_30,
        is_resolved=False,
    ).exists()


def impl_rf011_s04(
    authenticated_almacenista_client: APIClient,
    sample_product,
    sample_locations,
    db,
):
    from apps.inventory.models import StockByLocation

    sample_product.requires_cold_chain = True
    sample_product.save(update_fields=["requires_cold_chain"])
    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=0
    )
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


def impl_rf011_s06(
    authenticated_almacenista_client: APIClient,
    authenticated_administrador_client: APIClient,
    sample_product,
    sample_locations,
    db,
):
    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_stock_alerts_for_product
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    sample_product.reorder_point = 10
    sample_product.save(update_fields=["reorder_point"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=8
    )
    sync_stock_alerts_for_product(sample_product.id)
    active = Alert.objects.filter(
        product=sample_product, alert_type=AlertType.LOW_STOCK, is_resolved=False
    )
    assert active.exists()
    kpi = authenticated_administrador_client.get(reverse("reports-kpi"))
    assert kpi.status_code == status.HTTP_200_OK
    assert kpi.data["active_alerts_unresolved"] >= 1
    alerts = authenticated_almacenista_client.get(reverse("alerts-list"))
    assert alerts.status_code == status.HTTP_200_OK
    results = alerts.data.get("results", alerts.data)
    assert any(str(item["id"]) == str(active.first().id) for item in results)


def impl_rf011_s07(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    from apps.alerts.models import Alert, AlertType
    from apps.alerts.services import sync_stock_alerts_for_product
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    sample_product.reorder_point = 10
    sample_product.save(update_fields=["reorder_point"])
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=8
    )
    sync_stock_alerts_for_product(sample_product.id)
    alert = Alert.objects.get(
        product=sample_product, alert_type=AlertType.LOW_STOCK, is_resolved=False
    )
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


IMPLEMENTATIONS: dict[str, object] = {
    "RF011-S01": impl_rf011_s01,
    "RF011-S02": impl_rf011_s02,
    "RF011-S03": impl_rf011_s03,
    "RF011-S04": impl_rf011_s04,
    "RF011-S05": impl_rf011_s05,
    "RF011-S06": impl_rf011_s06,
    "RF011-S07": impl_rf011_s07,
}
