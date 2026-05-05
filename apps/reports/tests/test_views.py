from apps.reports.views import (ExpiringProductsReportView,
                                InventorySummaryReportView,
                                InvoiceHistoryReportView,
                                KpiDashboardReportView,
                                MovementHistoryReportView, MovementReportView,
                                MovementSummaryReportView,
                                SalesSummaryReportView,
                                TopDispatchedProductsReportView)


def test_reports_views_are_available():
    assert MovementSummaryReportView is not None
    assert SalesSummaryReportView is not None
    assert MovementHistoryReportView is not None
    assert InventorySummaryReportView is not None
    assert MovementReportView is not None
    assert TopDispatchedProductsReportView is not None
    assert InvoiceHistoryReportView is not None
    assert KpiDashboardReportView is not None
    assert ExpiringProductsReportView is not None
