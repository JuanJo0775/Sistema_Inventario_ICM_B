from apps.inventory.services import get_current_stock


def test_inventory_service_exports_current_stock_reader():
    assert callable(get_current_stock)
