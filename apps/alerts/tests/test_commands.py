"""Tests de integración para el management command scan_alerts (Fase 3)."""

from __future__ import annotations

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.alerts.models import Alert, AlertType
from apps.inventory.models import Location, StockByLocation
from tests.factories import LocationFactory, LotFactory, ProductFactory


@pytest.mark.django_db
def test_scan_alerts_dry_run_creates_no_alerts():
    product = ProductFactory(requires_expiration=True)
    yesterday = timezone.now().date() - timedelta(days=1)
    LotFactory(product=product, expiration_date=yesterday, code="CMD-EXP")

    out = StringIO()
    call_command("scan_alerts", "--dry-run", stdout=out)

    assert not Alert.objects.filter(
        product=product, alert_type=AlertType.LOT_EXPIRED
    ).exists()
    assert "[DRY RUN]" in out.getvalue()


@pytest.mark.django_db
def test_scan_alerts_expiry_type_creates_lot_expired_alert():
    product = ProductFactory(requires_expiration=True)
    yesterday = timezone.now().date() - timedelta(days=1)
    LotFactory(product=product, expiration_date=yesterday, code="CMD-LOT-EXP")

    out = StringIO()
    call_command("scan_alerts", "--types", "expiry", stdout=out)

    assert Alert.objects.filter(
        product=product, alert_type=AlertType.LOT_EXPIRED, is_resolved=False
    ).exists()
    assert "expiry" in out.getvalue()


@pytest.mark.django_db
def test_scan_alerts_stock_type_creates_low_stock_alert():
    product = ProductFactory(reorder_point=10)
    # Sin stock: reorder_point=10 y stock=0

    out = StringIO()
    call_command("scan_alerts", "--types", "stock", stdout=out)

    assert Alert.objects.filter(
        product=product, alert_type=AlertType.LOW_STOCK, is_resolved=False
    ).exists()


@pytest.mark.django_db
def test_scan_alerts_location_type_creates_blocked_alert():
    product = ProductFactory()
    location = LocationFactory(
        name="Bloqueada CMD", operational_status=Location.OperationalStatus.BLOCKED
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=5)

    out = StringIO()
    call_command("scan_alerts", "--types", "location", stdout=out)

    assert Alert.objects.filter(
        product=product,
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exists()


@pytest.mark.django_db
def test_scan_alerts_idempotent():
    product = ProductFactory(reorder_point=10)

    call_command("scan_alerts", "--types", "stock")
    call_command("scan_alerts", "--types", "stock")

    assert (
        Alert.objects.filter(product=product, alert_type=AlertType.LOW_STOCK).count()
        == 1
    )


@pytest.mark.django_db
def test_scan_alerts_unknown_type_is_ignored():
    out = StringIO()
    err = StringIO()
    call_command(
        "scan_alerts", "--types", "unknown_stuff", "--dry-run", stdout=out, stderr=err
    )

    assert "desconocidos" in err.getvalue() or "unknown" in err.getvalue().lower()


@pytest.mark.django_db
def test_scan_alerts_all_types_default():
    product = ProductFactory(requires_expiration=True, reorder_point=10)
    yesterday = timezone.now().date() - timedelta(days=1)
    LotFactory(product=product, expiration_date=yesterday, code="ALL-EXP")

    out = StringIO()
    call_command("scan_alerts", stdout=out)

    assert Alert.objects.filter(
        product=product, alert_type=AlertType.LOT_EXPIRED
    ).exists()
    assert Alert.objects.filter(
        product=product, alert_type=AlertType.LOW_STOCK
    ).exists()
