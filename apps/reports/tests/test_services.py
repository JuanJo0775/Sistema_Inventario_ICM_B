from apps.reports.services import generate_kpis


def test_generate_kpis_returns_dashboard_keys(db):
    data = generate_kpis()
    assert "movements_today" in data
    assert "low_stock_products_count" in data
    assert "active_alerts_unresolved" in data
    assert "dispatches_this_month" in data
    assert "generated_at" in data
