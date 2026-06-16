from django.urls import path

from apps.billing.views import (
    CompanyConfigView,
    InvoiceDetailView,
    InvoiceListCreateView,
    InvoiceStatsView,
    InvoiceVoidView,
)

urlpatterns = [
    path("invoices/stats/", InvoiceStatsView.as_view(), name="billing-invoice-stats"),
    path("invoices/", InvoiceListCreateView.as_view(), name="billing-invoice-list"),
    path(
        "invoices/<int:pk>/", InvoiceDetailView.as_view(), name="billing-invoice-detail"
    ),
    path(
        "invoices/<int:pk>/void/",
        InvoiceVoidView.as_view(),
        name="billing-invoice-void",
    ),
    path("config/company/", CompanyConfigView.as_view(), name="billing-company-config"),
]
