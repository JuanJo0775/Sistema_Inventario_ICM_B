"""Tests para umbrales de stock por ubicación (NEW-02)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.alerts.models import Alert, AlertType
from apps.alerts.services import check_and_create_minimum_stock_alert
from apps.audit.models import AuditEventType, AuditLog
from apps.inventory.models import StockByLocation
from apps.movements.services import register_entry
from tests.factories import LocationFactory, ProductFactory


@pytest.fixture
def threshold_setup(db, almacenista_user):
    product = ProductFactory(sku="THR-0001", reorder_point=10)
    location = LocationFactory(code="THR-LOC-01", name="Bodega Threshold")
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        7,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    stock = StockByLocation.objects.get(product=product, location=location)
    return {"product": product, "location": location, "stock": stock}


@pytest.mark.django_db
def test_effective_reorder_point_uses_global_when_no_override(threshold_setup):
    """Sin override local, effective_reorder_point devuelve el threshold global del producto."""
    stock = threshold_setup["stock"]
    assert stock.location_reorder_point is None
    assert stock.effective_reorder_point == 10  # global del producto


@pytest.mark.django_db
def test_effective_reorder_point_uses_local_override(threshold_setup):
    """Con override local, effective_reorder_point devuelve el valor local."""
    stock = threshold_setup["stock"]
    stock.location_reorder_point = 5
    stock.save(update_fields=["location_reorder_point", "updated_at"])
    stock.refresh_from_db()
    assert stock.effective_reorder_point == 5


@pytest.mark.django_db
def test_local_threshold_prevents_alert_when_stock_above_local(threshold_setup):
    """stock=7 > local_threshold=5 → NO debe generar alerta STOCK_CRITICO."""
    stock = threshold_setup["stock"]
    # stock=7, global_threshold=10 (generaría alerta), local_threshold=5 (no genera)
    stock.location_reorder_point = 5
    stock.save(update_fields=["location_reorder_point", "updated_at"])

    alert = check_and_create_minimum_stock_alert(
        threshold_setup["product"], threshold_setup["location"]
    )
    assert alert is None


@pytest.mark.django_db
def test_global_threshold_generates_alert_without_local_override(threshold_setup):
    """stock=7 <= global_threshold=10 y sin override → alerta LOW_STOCK debe existir."""
    # register_entry ya llamó check_and_create_minimum_stock_alert internamente
    assert Alert.objects.filter(
        product=threshold_setup["product"],
        location=threshold_setup["location"],
        alert_type=AlertType.LOW_STOCK,
        is_resolved=False,
    ).exists()


@pytest.mark.django_db
def test_patch_threshold_via_api(authenticated_almacenista_client, threshold_setup):
    """PATCH /api/v1/inventory/stock/{id}/threshold/ actualiza el umbral local."""
    stock = threshold_setup["stock"]
    url = reverse("inventory-stock-threshold", kwargs={"pk": str(stock.id)})

    response = authenticated_almacenista_client.patch(
        url,
        data={"location_reorder_point": 3},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["location_reorder_point"] == 3
    assert data["effective_reorder_point"] == 3

    stock.refresh_from_db()
    assert stock.location_reorder_point == 3
    assert AuditLog.objects.filter(
        event_type=AuditEventType.STOCK_THRESHOLD_UPDATED,
        metadata__stock_id=str(stock.id),
    ).exists()


@pytest.mark.django_db
def test_patch_threshold_null_removes_override(
    authenticated_almacenista_client, threshold_setup
):
    """PATCH con null elimina el override; effective_reorder_point vuelve al global."""
    stock = threshold_setup["stock"]
    stock.location_reorder_point = 3
    stock.save(update_fields=["location_reorder_point", "updated_at"])

    url = reverse("inventory-stock-threshold", kwargs={"pk": str(stock.id)})
    response = authenticated_almacenista_client.patch(
        url,
        data={"location_reorder_point": None},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["location_reorder_point"] is None
    assert data["effective_reorder_point"] == 10  # vuelve al global
