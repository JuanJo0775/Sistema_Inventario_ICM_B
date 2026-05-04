from django.urls import path

from apps.inventory.views import LocationListView, ProductSearchView, StockByLocationView, StockByProductView

urlpatterns = [
    path("locations/", LocationListView.as_view(), name="inventory-locations"),
    path("stock/product/<uuid:product_id>/", StockByProductView.as_view(), name="inventory-stock-product"),
    path("stock/location/<uuid:location_id>/", StockByLocationView.as_view(), name="inventory-stock-location"),
    path("search/", ProductSearchView.as_view(), name="inventory-search"),
]
