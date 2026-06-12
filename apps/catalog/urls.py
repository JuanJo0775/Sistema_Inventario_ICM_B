from django.urls import path

from apps.catalog.views import (
    BrandDetailView,
    BrandListCreateView,
    BrandRestoreView,
    CategoryDetailView,
    CategoryListCreateView,
    CategoryRestoreView,
    ComboDetailView,
    ComboListCreateView,
    ComboRestoreView,
    ProductBarcodeView,
    ProductDetailView,
    ProductListCreateView,
    ProductPricesView,
    ProductRestoreView,
    ResolveIdentifierView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="catalog-categories"),
    path(
        "categories/<uuid:pk>/",
        CategoryDetailView.as_view(),
        name="catalog-category-detail",
    ),
    path(
        "categories/<uuid:pk>/restore/",
        CategoryRestoreView.as_view(),
        name="catalog-category-restore",
    ),
    path(
        "brands/",
        BrandListCreateView.as_view(),
        name="catalog-brands",
    ),
    path(
        "brands/<uuid:pk>/",
        BrandDetailView.as_view(),
        name="catalog-brand-detail",
    ),
    path(
        "brands/<uuid:pk>/restore/",
        BrandRestoreView.as_view(),
        name="catalog-brand-restore",
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
        "products/<uuid:pk>/prices/",
        ProductPricesView.as_view(),
        name="catalog-product-prices",
    ),
    path(
        "products/<uuid:pk>/restore/",
        ProductRestoreView.as_view(),
        name="catalog-product-restore",
    ),
    path(
        "products/resolve/",
        ResolveIdentifierView.as_view(),
        name="catalog-products-resolve",
    ),
    path("resolve/", ResolveIdentifierView.as_view(), name="catalog-resolve"),
    path("combos/", ComboListCreateView.as_view(), name="catalog-combos"),
    path(
        "combos/<uuid:pk>/",
        ComboDetailView.as_view(),
        name="catalog-combo-detail",
    ),
    path(
        "combos/<uuid:pk>/restore/",
        ComboRestoreView.as_view(),
        name="catalog-combo-restore",
    ),
]
