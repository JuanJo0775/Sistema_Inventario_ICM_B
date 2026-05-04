from apps.reports.services import generate_kpis


def test_reports_service_is_declared():
    assert callable(generate_kpis)
