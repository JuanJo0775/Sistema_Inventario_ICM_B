from django.urls import path

from apps.reports.views import (
    DiscardOperationalReportView,
    DispatchOperationalReportView,
    DispatchOrdersReportView,
    ExpiringProductsReportView,
    InventorySummaryReportView,
    InvoiceHistoryReportView,
    KpiDashboardReportView,
    MovementHistoryReportView,
    MovementReportView,
    MovementSummaryReportView,
    QualityOperationalReportView,
    ReportDatasetView,
    SalesSummaryReportView,
    TopDispatchedProductsReportView,
    WarehouseUtilizationReportView,
)

# Routes grouped by functional area for clarity:
# - Inventory: inventario y vencimientos
# - Movements: resúmenes, reportes y historial
# - Operational summaries: warehouse, quality, discard, dispatch
# - Exports / datasets: unified dataset endpoint
# - KPI: legacy panel (delegates to apps.dashboard services)

urlpatterns = [
    # Inventory
    path(
        "inventory/summary/",
        InventorySummaryReportView.as_view(),
        name="reports-inventory-summary",
    ),
    path("expiring/", ExpiringProductsReportView.as_view(), name="reports-expiring"),
    # Movements
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
    # Operational summaries
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
    # Exports / dataset
    path("data/", ReportDatasetView.as_view(), name="reports-data"),
    # Sales / top products / invoices
    path(
        "sales/summary/", SalesSummaryReportView.as_view(), name="reports-sales-summary"
    ),
    path(
        "top-products/",
        TopDispatchedProductsReportView.as_view(),
        name="reports-top-products",
    ),
    path("invoices/", InvoiceHistoryReportView.as_view(), name="reports-invoices"),
    # KPI (legacy panel) - delegated to dashboard service for ownership
    path("kpi/", KpiDashboardReportView.as_view(), name="reports-kpi"),
]
