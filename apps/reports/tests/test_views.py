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


def test_reports_expiring_view_returns_lots(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from datetime import timedelta

    from django.utils import timezone

    from apps.movements.services import register_entry
    from tests.factories import LotFactory, ProductFactory

    product = ProductFactory(requires_expiration=True)
    location = sample_locations[0]
    LotFactory(
        product=product,
        code="L-REP",
        expiration_date=timezone.now().date() + timedelta(days=45),
    )
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        6,
        lot_code="L-REP",
        lot_expiration_date=timezone.now().date() + timedelta(days=45),
        serial_number="SN-REP",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    response = authenticated_almacenista_client.get("/api/v1/reports/expiring/")
    assert response.status_code == 200


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
