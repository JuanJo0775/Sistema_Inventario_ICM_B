from apps.alerts.services import sync_stock_alerts_for_product


def test_alerts_service_exports_stock_sync():
    assert callable(sync_stock_alerts_for_product)
