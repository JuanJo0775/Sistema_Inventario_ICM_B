from apps.reports.views import MovementHistoryReportView, MovementSummaryReportView, SalesSummaryReportView


def test_reports_views_are_available():
    assert MovementSummaryReportView is not None
    assert SalesSummaryReportView is not None
    assert MovementHistoryReportView is not None
