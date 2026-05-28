from django.urls import path

from apps.reports.views import (
    ExpiringProductsReportView,
    InventorySummaryReportView,
    InvoiceHistoryReportView,
    KpiDashboardReportView,
    MovementHistoryReportView,
    MovementReportView,
    ReportDatasetView,
    MovementSummaryReportView,
    DiscardOperationalReportView,
    SalesSummaryReportView,
    WarehouseUtilizationReportView,
    QualityOperationalReportView,
    DispatchOperationalReportView,
    DispatchOrdersReportView,
    TopDispatchedProductsReportView,
)

urlpatterns = [
    path(
        "inventory/summary/",
        InventorySummaryReportView.as_view(),
        name="reports-inventory-summary",
    ),
    path(
        "movements/summary/",
        MovementSummaryReportView.as_view(),
        name="reports-movements-summary",
    ),
    path(
        "movements/report/",
        MovementReportView.as_view(),
        name="reports-movements-report",
    ),
    path(
        "movements/history/",
        MovementHistoryReportView.as_view(),
        name="reports-movements-history",
    ),
    path("data/", ReportDatasetView.as_view(), name="reports-data"),
    path(
        "sales/summary/", SalesSummaryReportView.as_view(), name="reports-sales-summary"
    ),
    path(
        "top-products/",
        TopDispatchedProductsReportView.as_view(),
        name="reports-top-products",
    ),
    path(
        "warehouse-utilization/",
        WarehouseUtilizationReportView.as_view(),
        name="reports-warehouse-utilization",
    ),
    path(
        "quality-operational/",
        QualityOperationalReportView.as_view(),
        name="reports-quality-operational",
    ),
    path(
        "discard-operational/",
        DiscardOperationalReportView.as_view(),
        name="reports-discard-operational",
    ),
    path(
        "dispatch-operational/",
        DispatchOperationalReportView.as_view(),
        name="reports-dispatch-operational",
    ),
    path(
        "dispatch-operational/orders/",
        DispatchOrdersReportView.as_view(),
        name="reports-dispatch-operational-orders",
    ),
    path("invoices/", InvoiceHistoryReportView.as_view(), name="reports-invoices"),
    path("kpi/", KpiDashboardReportView.as_view(), name="reports-kpi"),
    path("expiring/", ExpiringProductsReportView.as_view(), name="reports-expiring"),
]
