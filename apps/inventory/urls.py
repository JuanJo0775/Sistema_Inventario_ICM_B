from django.urls import path

from apps.inventory.views import (InventoryFullListView, LocationDetailView,
                                  LocationListCreateView, ProductSearchView,
                                  ReconstructStockView, StockByLocationView,
                                  StockByProductView)

urlpatterns = [
    path("", InventoryFullListView.as_view(), name="inventory-full"),
    path("locations/", LocationListCreateView.as_view(), name="inventory-locations"),
    path(
        "locations/<uuid:pk>/",
        LocationDetailView.as_view(),
        name="inventory-location-detail",
    ),
    path("reconstruct/", ReconstructStockView.as_view(), name="inventory-reconstruct"),
    path(
        "products/<uuid:product_id>/stock/",
        StockByProductView.as_view(),
        name="inventory-product-stock",
    ),
    path(
        "stock/product/<uuid:product_id>/",
        StockByProductView.as_view(),
        name="inventory-stock-product",
    ),
    path(
        "stock/location/<uuid:location_id>/",
        StockByLocationView.as_view(),
        name="inventory-stock-location",
    ),
    path("search/", ProductSearchView.as_view(), name="inventory-search"),
]
