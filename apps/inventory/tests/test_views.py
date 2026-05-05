from apps.inventory.views import (InventoryFullListView, LocationDetailView,
                                  LocationListCreateView, ProductSearchView,
                                  StockByLocationView, StockByProductView)


def test_inventory_views_are_available():
    assert InventoryFullListView is not None
    assert LocationListCreateView is not None
    assert LocationDetailView is not None
    assert ProductSearchView is not None
    assert StockByLocationView is not None
    assert StockByProductView is not None
