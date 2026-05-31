from apps.alerts.models import (
    ALERT_TYPE_DEFAULTS,
    AlertCategory,
    AlertSeverity,
    AlertType,
)


def test_alert_type_low_stock():
    assert AlertType.LOW_STOCK == "LOW_STOCK"


def test_all_alert_types_have_defaults():
    for alert_type in AlertType.values:
        assert (
            alert_type in ALERT_TYPE_DEFAULTS
        ), f"{alert_type} no tiene entrada en ALERT_TYPE_DEFAULTS"


def test_expiration_30_is_critical():
    severity, category = ALERT_TYPE_DEFAULTS[AlertType.EXPIRATION_30]
    assert severity == AlertSeverity.CRITICAL
    assert category == AlertCategory.EXPIRATION


def test_stock_mismatch_is_critical_integrity():
    severity, category = ALERT_TYPE_DEFAULTS[AlertType.STOCK_MISMATCH]
    assert severity == AlertSeverity.CRITICAL
    assert category == AlertCategory.INTEGRITY


def test_low_stock_is_high_stock():
    severity, category = ALERT_TYPE_DEFAULTS[AlertType.LOW_STOCK]
    assert severity == AlertSeverity.HIGH
    assert category == AlertCategory.STOCK
