from django.urls import path

from apps.catalog.views import (
    CategoryListCreateView,
    ComboListCreateView,
    ProductBarcodeView,
    ProductDetailView,
    ProductListCreateView,
    ResolveIdentifierView,
    SubcategoryListCreateView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="catalog-categories"),
    path(
        "subcategories/",
        SubcategoryListCreateView.as_view(),
        name="catalog-subcategories",
    ),
    path("products/", ProductListCreateView.as_view(), name="catalog-products"),
    path(
        "products/<uuid:pk>/",
        ProductDetailView.as_view(),
        name="catalog-product-detail",
    ),
    path(
        "products/<uuid:pk>/barcode/",
        ProductBarcodeView.as_view(),
        name="catalog-product-barcode",
    ),
    path(
        "products/resolve/",
        ResolveIdentifierView.as_view(),
        name="catalog-products-resolve",
    ),
    path("resolve/", ResolveIdentifierView.as_view(), name="catalog-resolve"),
    path("combos/", ComboListCreateView.as_view(), name="catalog-combos"),
]
