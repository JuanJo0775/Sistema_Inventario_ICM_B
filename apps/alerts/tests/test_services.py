from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.audit.models import AuditEventType, AuditLog
from apps.alerts.models import (
    ALERT_TYPE_DEFAULTS,
    Alert,
    AlertCategory,
    AlertSeverity,
    AlertType,
)
from apps.alerts.services import (
    _severity_and_category,
    resolve_alert,
    scan_all_location_alerts,
    sync_expiry_alerts_for_product,
    sync_location_blocked_alerts_for_location,
    sync_stock_alerts_for_product,
)
from apps.inventory.models import Location, StockByLocation
from shared.exceptions import UnauthorizedDomainActionError
from tests.factories import LocationFactory, LotFactory, ProductFactory


@pytest.mark.django_db
def test_resolve_alert_almacenista(almacenista_user):
    p = ProductFactory()
    alert = Alert.objects.create(
        product=p,
        alert_type=AlertType.LOW_STOCK,
        message="test",
    )
    out = resolve_alert(almacenista_user, alert.id)
    assert out.is_resolved
    assert out.resolved_by_id == almacenista_user.id
    assert AuditLog.objects.filter(
        event_type=AuditEventType.ALERT_RESOLVED,
        metadata__alert_id=str(alert.id),
    ).exists()


@pytest.mark.django_db
def test_resolve_alert_rejects_auxiliar(auxiliar_user):
    p = ProductFactory()
    alert = Alert.objects.create(
        product=p,
        alert_type=AlertType.LOW_STOCK,
        message="test",
    )
    with pytest.raises(UnauthorizedDomainActionError):
        resolve_alert(auxiliar_user, alert.id)


@pytest.mark.django_db
def test_sync_expiry_alerts_for_product_creates_lot_alert(db):
    from datetime import timedelta

    from django.utils import timezone

    from apps.alerts.services import sync_expiry_alerts_for_product

    product = ProductFactory(requires_expiration=True)
    lot = LotFactory(
        product=product,
        expiration_date=timezone.now().date() + timedelta(days=60),
        code="L-ALERT",
    )
    sync_expiry_alerts_for_product(product.id)
    alert = Alert.objects.get(
        product=product, lot=lot, alert_type=AlertType.EXPIRATION_60
    )
    assert alert.message.startswith("El lote L-ALERT")
    assert alert.severity == AlertSeverity.HIGH
    assert alert.category == AlertCategory.EXPIRATION


@pytest.mark.django_db
def test_sync_stock_alerts_sets_severity_and_category():
    product = ProductFactory(reorder_point=10)
    sync_stock_alerts_for_product(product.id)
    alert = Alert.objects.filter(
        product=product, alert_type=AlertType.LOW_STOCK, is_resolved=False
    ).first()
    assert alert is not None
    assert alert.severity == AlertSeverity.HIGH
    assert alert.category == AlertCategory.STOCK


@pytest.mark.django_db
def test_sync_expiry_30_days_sets_critical(db):
    from datetime import timedelta

    from django.utils import timezone

    from apps.alerts.services import sync_expiry_alerts_for_product

    product = ProductFactory(requires_expiration=True)
    LotFactory(
        product=product,
        expiration_date=timezone.now().date() + timedelta(days=15),
        code="L-30",
    )
    sync_expiry_alerts_for_product(product.id)
    alert = Alert.objects.get(product=product, alert_type=AlertType.EXPIRATION_30)
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.category == AlertCategory.EXPIRATION


@pytest.mark.django_db
def test_expiry_60_resolved_when_crossing_30_days():
    """Fix #3: al cruzar de ventana 60 días a 30 días, la alerta EXPIRATION_60 debe resolverse."""
    today = timezone.now().date()
    product = ProductFactory(
        requires_expiration=False,
        expiration_date=today + timedelta(days=45),
    )

    # Primer sync: debe crear EXPIRATION_60
    sync_expiry_alerts_for_product(product.id)
    assert Alert.objects.filter(
        product=product, alert_type=AlertType.EXPIRATION_60, is_resolved=False
    ).exists()

    # Simular que pasó el tiempo: producto ahora vence en 15 días
    product.expiration_date = today + timedelta(days=15)
    product.save(update_fields=["expiration_date"])

    # Segundo sync: debe resolver EXPIRATION_60 y crear EXPIRATION_30
    sync_expiry_alerts_for_product(product.id)

    assert not Alert.objects.filter(
        product=product, alert_type=AlertType.EXPIRATION_60, is_resolved=False
    ).exists(), "EXPIRATION_60 debe quedar resuelta al cruzar la ventana de 30 días"
    assert Alert.objects.filter(
        product=product, alert_type=AlertType.EXPIRATION_30, is_resolved=False
    ).exists(), "EXPIRATION_30 debe existir y estar activa"


@pytest.mark.django_db
def test_scan_resolves_stale_alerts_on_unblocked_location():
    """Fix #4: scan_all_location_alerts debe resolver alertas de ubicaciones ya desbloqueadas."""
    product = ProductFactory()
    location = LocationFactory(
        name="Bodega Scan Test",
        code="scan-test",
        operational_status=Location.OperationalStatus.BLOCKED,
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=10)

    # Generar la alerta mientras la ubicación está bloqueada
    sync_location_blocked_alerts_for_location(location)
    assert Alert.objects.filter(
        product=product,
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exists()

    # Desbloquear la ubicación
    location.operational_status = Location.OperationalStatus.ACTIVE
    location.save(update_fields=["operational_status"])

    # El cron debe encontrar y resolver la alerta stale
    scan_all_location_alerts(dry_run=False)

    assert not Alert.objects.filter(
        product=product,
        location=location,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exists(), "La alerta debe quedar resuelta tras el scan con la ubicación activa"


# ─── Tests parametrizados de severidad y categoría canónicas ────────────────


@pytest.mark.parametrize(
    "alert_type, per_location, expected_severity, expected_category",
    [
        (AlertType.LOW_STOCK, False, AlertSeverity.HIGH, AlertCategory.STOCK),
        (AlertType.LOW_STOCK, True, AlertSeverity.MEDIUM, AlertCategory.STOCK),
        (
            AlertType.EXPIRATION_30,
            False,
            AlertSeverity.CRITICAL,
            AlertCategory.EXPIRATION,
        ),
        (AlertType.EXPIRATION_60, False, AlertSeverity.HIGH, AlertCategory.EXPIRATION),
        (
            AlertType.LOT_EXPIRED,
            False,
            AlertSeverity.CRITICAL,
            AlertCategory.EXPIRATION,
        ),
        (
            AlertType.COLD_CHAIN_MISSING,
            False,
            AlertSeverity.HIGH,
            AlertCategory.LOCATION,
        ),
        (
            AlertType.LOCATION_BLOCKED_WITH_STOCK,
            False,
            AlertSeverity.HIGH,
            AlertCategory.LOCATION,
        ),
        (
            AlertType.STOCK_MISMATCH,
            False,
            AlertSeverity.CRITICAL,
            AlertCategory.INTEGRITY,
        ),
        (AlertType.STOCK_ZERO, False, AlertSeverity.MEDIUM, AlertCategory.STOCK),
    ],
)
def test_severity_and_category_canonical(
    alert_type, per_location, expected_severity, expected_category
):
    """Verifica que _severity_and_category devuelve los valores canónicos del mapa."""
    severity, category = _severity_and_category(alert_type, per_location=per_location)
    assert (
        severity == expected_severity
    ), f"{alert_type}(per_location={per_location}): esperaba severity={expected_severity}, obtuvo={severity}"
    assert (
        category == expected_category
    ), f"{alert_type}(per_location={per_location}): esperaba category={expected_category}, obtuvo={category}"


def test_severity_unknown_type_returns_defaults():
    """Tipos desconocidos devuelven MEDIUM/STOCK como fallback."""
    severity, category = _severity_and_category("TIPO_INEXISTENTE")
    assert severity == AlertSeverity.MEDIUM
    assert category == AlertCategory.STOCK


def test_alert_type_defaults_map_covers_all_alert_types():
    """Todos los AlertType deben estar cubiertos en ALERT_TYPE_DEFAULTS."""
    all_types = {t.value for t in AlertType}
    covered = set(ALERT_TYPE_DEFAULTS.keys())
    missing = all_types - covered
    assert not missing, f"AlertTypes sin mapeo en ALERT_TYPE_DEFAULTS: {missing}"
