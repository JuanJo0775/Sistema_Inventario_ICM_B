"""Tests reales para inventory/services.py — reemplaza el test trivial callable."""

from __future__ import annotations

import pytest

from apps.inventory.models import StockByLocation
from apps.inventory.services import get_current_stock, trigger_stock_reconstruction
from tests.factories import LocationFactory, ProductFactory


@pytest.mark.django_db
def test_get_current_stock_returns_zero_when_no_row(db):
    product = ProductFactory()
    location = LocationFactory(name="Bodega Test A", code="bodega-test-a")
    assert get_current_stock(product.id, location.id) == 0


@pytest.mark.django_db
def test_get_current_stock_returns_existing_stock(db):
    product = ProductFactory()
    location = LocationFactory(name="Bodega Test B", code="bodega-test-b")
    StockByLocation.objects.create(product=product, location=location, current_stock=10)
    assert get_current_stock(product.id, location.id) == 10


@pytest.mark.django_db
def test_get_current_stock_does_not_leak_other_locations(db):
    product = ProductFactory()
    loc1 = LocationFactory(name="Bodega Test C1", code="bodega-test-c1")
    loc2 = LocationFactory(name="Bodega Test C2", code="bodega-test-c2")
    StockByLocation.objects.create(product=product, location=loc1, current_stock=10)
    StockByLocation.objects.create(product=product, location=loc2, current_stock=5)
    assert get_current_stock(product.id, loc1.id) == 10
    assert get_current_stock(product.id, loc2.id) == 5


@pytest.mark.django_db
def test_get_current_stock_does_not_leak_other_products(db):
    product_a = ProductFactory(sku="TST-0001", barcode="BAR00000001")
    product_b = ProductFactory(sku="TST-0002", barcode="BAR00000002")
    location = LocationFactory(name="Bodega Test D", code="bodega-test-d")
    StockByLocation.objects.create(
        product=product_a, location=location, current_stock=7
    )
    StockByLocation.objects.create(
        product=product_b, location=location, current_stock=3
    )
    assert get_current_stock(product_a.id, location.id) == 7
    assert get_current_stock(product_b.id, location.id) == 3


@pytest.mark.django_db
def test_trigger_stock_reconstruction_detects_discrepancy(db, almacenista_user):
    """
    trigger_stock_reconstruction detecta divergencias y crea alerta STOCK_MISMATCH.
    No modifica el caché directamente — eso es responsabilidad de verify_stock_integrity --fix.
    """
    from apps.alerts.models import Alert, AlertType

    product = ProductFactory()
    location = LocationFactory(name="Bodega Test E", code="bodega-test-e")
    StockByLocation.objects.create(
        product=product, location=location, current_stock=999
    )
    result = trigger_stock_reconstruction(
        almacenista_user, product_id=product.id, location_id=location.id
    )
    assert result["status"] == "DISCREPANCY"
    assert result["reconstructed"] == 0
    assert result["actual"] == 999
    assert Alert.objects.filter(
        product=product, location=location, alert_type=AlertType.STOCK_MISMATCH
    ).exists()
