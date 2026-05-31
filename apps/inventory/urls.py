from django.urls import path

from apps.inventory.views import (
    InventoryFullListView,
    LocationDetailView,
    LocationListCreateView,
    LocationStateTransitionView,
    ProductSearchView,
    ReconstructStockView,
    StorageTemplateDetailView,
    StorageTemplateListCreateView,
    StorageTypeDetailView,
    StorageTypeListCreateView,
    StockByLocationView,
    StockByProductView,
)

urlpatterns = [
    path("", InventoryFullListView.as_view(), name="inventory-full"),
    path(
        "storage-types/",
        StorageTypeListCreateView.as_view(),
        name="inventory-storage-types",
    ),
    path(
        "storage-types/<uuid:pk>/",
        StorageTypeDetailView.as_view(),
        name="inventory-storage-type-detail",
    ),
    path(
        "storage-templates/",
        StorageTemplateListCreateView.as_view(),
        name="inventory-storage-templates",
    ),
    path(
        "storage-templates/<uuid:pk>/",
        StorageTemplateDetailView.as_view(),
        name="inventory-storage-template-detail",
    ),
    path("locations/", LocationListCreateView.as_view(), name="inventory-locations"),
    path(
        "locations/<uuid:pk>/",
        LocationDetailView.as_view(),
        name="inventory-location-detail",
    ),
    path(
        "locations/<uuid:pk>/state-transitions/",
        LocationStateTransitionView.as_view(),
        name="inventory-location-state-transitions",
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
