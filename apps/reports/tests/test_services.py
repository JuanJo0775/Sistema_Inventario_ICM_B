from apps.reports.selectors import get_expiring_products
from apps.reports.services import generate_kpis


def test_get_expiring_products_returns_lot_rows(almacenista_user, sample_locations, db):
    from datetime import timedelta

    from django.utils import timezone

    from apps.movements.services import register_entry
    from tests.factories import LotFactory, ProductFactory

    product = ProductFactory(requires_expiration=True)
    location = sample_locations[0]
    lot = LotFactory(
        product=product,
        code="L-SEL",
        expiration_date=timezone.now().date() + timedelta(days=45),
    )
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        5,
        lot_code=lot.code,
        lot_expiration_date=lot.expiration_date,
        serial_number="SN-SEL",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    rows = get_expiring_products(days=60)
    assert any(row["lot_code"] == "L-SEL" for row in rows)


def test_generate_kpis_returns_dashboard_keys(db):
    data = generate_kpis()
    assert "movements_today" in data
    assert "low_stock_products_count" in data
    assert "active_alerts_unresolved" in data
    assert "dispatches_this_month" in data
    assert "generated_at" in data
