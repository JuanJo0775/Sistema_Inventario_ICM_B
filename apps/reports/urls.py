from django.urls import path

from apps.reports.views import (
    ExpiringProductsReportView,
    InventorySummaryReportView,
    InvoiceHistoryReportView,
    KpiDashboardReportView,
    MovementHistoryReportView,
    MovementReportView,
    MovementSummaryReportView,
    SalesSummaryReportView,
    TopDispatchedProductsReportView,
)

urlpatterns = [
    path("inventory/summary/", InventorySummaryReportView.as_view(), name="reports-inventory-summary"),
    path("movements/summary/", MovementSummaryReportView.as_view(), name="reports-movements-summary"),
    path("movements/report/", MovementReportView.as_view(), name="reports-movements-report"),
    path("movements/history/", MovementHistoryReportView.as_view(), name="reports-movements-history"),
    path("sales/summary/", SalesSummaryReportView.as_view(), name="reports-sales-summary"),
    path("top-products/", TopDispatchedProductsReportView.as_view(), name="reports-top-products"),
    path("invoices/", InvoiceHistoryReportView.as_view(), name="reports-invoices"),
    path("kpi/", KpiDashboardReportView.as_view(), name="reports-kpi"),
    path("expiring/", ExpiringProductsReportView.as_view(), name="reports-expiring"),
]
