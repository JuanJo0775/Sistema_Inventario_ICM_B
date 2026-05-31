"""Tests para los nuevos tipos de alerta (Fase 2): LOT_EXPIRED, STOCK_ZERO,
COLD_CHAIN_MISSING, LOCATION_BLOCKED_WITH_STOCK."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.alerts.models import Alert, AlertCategory, AlertSeverity, AlertType
from apps.alerts.services import (
    sync_cold_chain_alerts,
    sync_location_blocked_alerts_for_location,
    sync_lot_expired_alerts,
    sync_stock_zero_alerts,
)
from apps.inventory.models import Location, StockByLocation
from tests.factories import LocationFactory, LotFactory, ProductFactory

# ---------------------------------------------------------------------------
# LOT_EXPIRED
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_lot_expired_creates_critical_alert():
    product = ProductFactory(requires_expiration=True)
    yesterday = timezone.now().date() - timedelta(days=1)
    lot = LotFactory(product=product, expiration_date=yesterday, code="EXPIRED-LOT")

    sync_lot_expired_alerts(product.id)

    alert = Alert.objects.get(
        product=product, lot=lot, alert_type=AlertType.LOT_EXPIRED
    )
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.category == AlertCategory.EXPIRATION
    assert not alert.is_resolved


@pytest.mark.django_db
def test_sync_lot_expired_no_duplicate():
    product = ProductFactory(requires_expiration=True)
    yesterday = timezone.now().date() - timedelta(days=1)
    lot = LotFactory(product=product, expiration_date=yesterday, code="EXP-DUP")

    sync_lot_expired_alerts(product.id)
    sync_lot_expired_alerts(product.id)

    assert (
        Alert.objects.filter(product=product, alert_type=AlertType.LOT_EXPIRED).count()
        == 1
    )


@pytest.mark.django_db
def test_sync_lot_expired_ignores_future_lot():
    product = ProductFactory(requires_expiration=True)
    future = timezone.now().date() + timedelta(days=90)
    LotFactory(product=product, expiration_date=future, code="FUTURE")

    sync_lot_expired_alerts(product.id)

    assert not Alert.objects.filter(
        product=product, alert_type=AlertType.LOT_EXPIRED
    ).exists()


# ---------------------------------------------------------------------------
# STOCK_ZERO
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_stock_zero_creates_alert_when_no_stock():
    product = ProductFactory()
    sync_stock_zero_alerts(product.id)

    alert = Alert.objects.filter(
        product=product, alert_type=AlertType.STOCK_ZERO
    ).first()
    assert alert is not None
    assert alert.severity == AlertSeverity.MEDIUM
    assert alert.category == AlertCategory.STOCK


@pytest.mark.django_db
def test_sync_stock_zero_resolves_when_stock_added():
    product = ProductFactory()
    sync_stock_zero_alerts(product.id)
    assert Alert.objects.filter(
        product=product, alert_type=AlertType.STOCK_ZERO, is_resolved=False
    ).exists()

    location = LocationFactory()
    StockByLocation.objects.create(product=product, location=location, current_stock=5)
    sync_stock_zero_alerts(product.id)

    assert not Alert.objects.filter(
        product=product, alert_type=AlertType.STOCK_ZERO, is_resolved=False
    ).exists()


@pytest.mark.django_db
def test_sync_stock_zero_no_alert_for_inactive_product():
    product = ProductFactory(is_active=False)
    sync_stock_zero_alerts(product.id)
    assert not Alert.objects.filter(
        product=product, alert_type=AlertType.STOCK_ZERO
    ).exists()


# ---------------------------------------------------------------------------
# COLD_CHAIN_MISSING
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_cold_chain_alert_created_for_non_cold_location():
    from apps.inventory.models import StorageType

    storage_type = StorageType.objects.create(
        code="bodega-normal", name="Bodega normal", category="warehouse"
    )
    product = ProductFactory(requires_cold_chain=True)
    location = LocationFactory(name="Bodega Normal CC", storage_type=storage_type)

    sync_cold_chain_alerts(product, location)

    alert = Alert.objects.filter(
        product=product, location=location, alert_type=AlertType.COLD_CHAIN_MISSING
    ).first()
    assert alert is not None
    assert alert.severity == AlertSeverity.HIGH
    assert alert.category == AlertCategory.LOCATION


@pytest.mark.django_db
def test_sync_cold_chain_no_alert_for_cold_location():
    from apps.inventory.models import StorageType

    cold_type = StorageType.objects.create(
        code="cuarto-frio-t", name="Cuarto frío test", category="cold_chain"
    )
    product = ProductFactory(requires_cold_chain=True)
    location = LocationFactory(name="Cuarto Frio T", storage_type=cold_type)

    sync_cold_chain_alerts(product, location)

    assert not Alert.objects.filter(
        product=product, location=location, alert_type=AlertType.COLD_CHAIN_MISSING
    ).exists()


@pytest.mark.django_db
def test_sync_cold_chain_no_alert_for_non_cold_chain_product():
    product = ProductFactory(requires_cold_chain=False)
    location = LocationFactory(name="Bodega No CC")

    sync_cold_chain_alerts(product, location)

    assert not Alert.objects.filter(
        product=product, alert_type=AlertType.COLD_CHAIN_MISSING
    ).exists()


@pytest.mark.django_db
def test_sync_cold_chain_resolves_when_moved_to_cold_location():
    from apps.inventory.models import StorageType

    warm_type = StorageType.objects.create(
        code="bodega-caliente", name="Bodega caliente", category="warehouse"
    )
    cold_type = StorageType.objects.create(
        code="cuarto-frio-r", name="Cuarto frío resolve", category="cold_chain"
    )
    product = ProductFactory(requires_cold_chain=True)
    warm_loc = LocationFactory(name="Bodega Caliente Test", storage_type=warm_type)
    cold_loc = LocationFactory(name="Cuarto Frio Resolve", storage_type=cold_type)

    sync_cold_chain_alerts(product, warm_loc)
    assert Alert.objects.filter(
        product=product,
        location=warm_loc,
        alert_type=AlertType.COLD_CHAIN_MISSING,
        is_resolved=False,
    ).exists()

    sync_cold_chain_alerts(product, cold_loc)
    # La ubicación fría nunca genera alerta
    assert not Alert.objects.filter(
        product=product,
        location=cold_loc,
        alert_type=AlertType.COLD_CHAIN_MISSING,
        is_resolved=False,
    ).exists()


# ---------------------------------------------------------------------------
# LOCATION_BLOCKED_WITH_STOCK
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_location_blocked_creates_alert_when_blocked_with_stock():
    product = ProductFactory()
    location = LocationFactory(
        name="Bloqueada Stock", operational_status=Location.OperationalStatus.BLOCKED
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=10)

    sync_location_blocked_alerts_for_location(location)

    alert = Alert.objects.filter(
        product=product,
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).first()
    assert alert is not None
    assert alert.severity == AlertSeverity.HIGH
    assert alert.category == AlertCategory.LOCATION


@pytest.mark.django_db
def test_sync_location_blocked_resolves_when_activated():
    product = ProductFactory()
    location = LocationFactory(
        name="Bloqueada Resolver", operational_status=Location.OperationalStatus.BLOCKED
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=10)

    sync_location_blocked_alerts_for_location(location)
    assert Alert.objects.filter(
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exists()

    location.operational_status = Location.OperationalStatus.ACTIVE
    location.save()
    sync_location_blocked_alerts_for_location(location)

    assert not Alert.objects.filter(
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exists()


@pytest.mark.django_db
def test_sync_location_blocked_no_alert_when_no_stock():
    location = LocationFactory(
        name="Bloqueada Sin Stock",
        operational_status=Location.OperationalStatus.BLOCKED,
    )

    sync_location_blocked_alerts_for_location(location)

    assert not Alert.objects.filter(
        location=location, alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK
    ).exists()


@pytest.mark.django_db
def test_sync_location_archived_with_stock_creates_alert():
    product = ProductFactory()
    location = LocationFactory(
        name="Archivada Con Stock",
        operational_status=Location.OperationalStatus.ARCHIVED,
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=3)

    sync_location_blocked_alerts_for_location(location)

    assert Alert.objects.filter(
        product=product,
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exists()
