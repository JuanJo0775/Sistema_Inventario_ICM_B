"""URLs del módulo de compras."""

from django.urls import path

from .views import (
    PurchaseOrderCancelView,
    PurchaseOrderConfirmView,
    PurchaseOrderDetailView,
    PurchaseOrderListCreateView,
    ReceptionCancelView,
    ReceptionConfirmView,
    ReceptionDetailView,
    ReceptionListCreateView,
    SupplierActivateView,
    SupplierDeactivateView,
    SupplierDetailView,
    SupplierDisableView,
    SupplierEnableView,
    SupplierListCreateView,
    SupplierRestoreView,
)

urlpatterns = [
    # Suppliers
    path("suppliers/", SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("suppliers/<uuid:pk>/", SupplierDetailView.as_view(), name="supplier-detail"),
    path(
        "suppliers/<uuid:pk>/restore/",
        SupplierRestoreView.as_view(),
        name="supplier-restore",
    ),
    path(
        "suppliers/<uuid:pk>/disable/",
        SupplierDisableView.as_view(),
        name="supplier-disable",
    ),
    path(
        "suppliers/<uuid:pk>/enable/",
        SupplierEnableView.as_view(),
        name="supplier-enable",
    ),
    # legacy aliases — mantenidos para compatibilidad
    path(
        "suppliers/<uuid:pk>/deactivate/",
        SupplierDeactivateView.as_view(),
        name="supplier-deactivate",
    ),
    path(
        "suppliers/<uuid:pk>/activate/",
        SupplierActivateView.as_view(),
        name="supplier-activate",
    ),
    # Purchase Orders
    path(
        "purchase-orders/", PurchaseOrderListCreateView.as_view(), name="po-list-create"
    ),
    path(
        "purchase-orders/<uuid:pk>/",
        PurchaseOrderDetailView.as_view(),
        name="po-detail",
    ),
    path(
        "purchase-orders/<uuid:pk>/confirm/",
        PurchaseOrderConfirmView.as_view(),
        name="po-confirm",
    ),
    path(
        "purchase-orders/<uuid:pk>/cancel/",
        PurchaseOrderCancelView.as_view(),
        name="po-cancel",
    ),
    # Receptions
    path(
        "receptions/", ReceptionListCreateView.as_view(), name="reception-list-create"
    ),
    path(
        "receptions/<uuid:pk>/", ReceptionDetailView.as_view(), name="reception-detail"
    ),
    path(
        "receptions/<uuid:pk>/confirm/",
        ReceptionConfirmView.as_view(),
        name="reception-confirm",
    ),
    path(
        "receptions/<uuid:pk>/cancel/",
        ReceptionCancelView.as_view(),
        name="reception-cancel",
    ),
]
