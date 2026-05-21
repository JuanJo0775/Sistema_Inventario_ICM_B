from apps.reports.views import (ExpiringProductsReportView,
                                InventorySummaryReportView,
                                InvoiceHistoryReportView,
                                KpiDashboardReportView,
                                MovementHistoryReportView, MovementReportView,
                                MovementSummaryReportView,
                                SalesSummaryReportView,
                                TopDispatchedProductsReportView,
                                ReportDatasetView)


def test_reports_dataset_view_is_available(authenticated_almacenista_client):
    response = authenticated_almacenista_client.get(
        "/api/v1/reports/data/", {"kind": "kpi"}
    )
    assert response.status_code == 200
    assert response.data["report"] == "kpi"
    assert "data" in response.data


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
    assert ReportDatasetView is not None
