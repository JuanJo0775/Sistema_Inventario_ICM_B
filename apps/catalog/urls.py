from django.urls import path

from apps.catalog.views import (
    CategoryListCreateView,
    ComboListCreateView,
    ProductDetailView,
    ProductListCreateView,
    ResolveIdentifierView,
    SubcategoryListView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="catalog-categories"),
    path("subcategories/", SubcategoryListView.as_view(), name="catalog-subcategories"),
    path("products/", ProductListCreateView.as_view(), name="catalog-products"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="catalog-product-detail"),
    path("products/resolve/", ResolveIdentifierView.as_view(), name="catalog-products-resolve"),
    path("resolve/", ResolveIdentifierView.as_view(), name="catalog-resolve"),
    path("combos/", ComboListCreateView.as_view(), name="catalog-combos"),
]
