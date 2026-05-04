from apps.inventory.views import LocationListView, ProductSearchView, StockByLocationView, StockByProductView


def test_inventory_views_are_available():
    assert LocationListView is not None
    assert ProductSearchView is not None
    assert StockByLocationView is not None
    assert StockByProductView is not None
