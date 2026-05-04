from apps.alerts.models import AlertType


def test_alert_type_low_stock():
    assert AlertType.LOW_STOCK == "LOW_STOCK"
