from __future__ import annotations

import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.alerts.models import Alert, AlertType
from apps.dashboard.services import (
    build_dashboard_alerts,
    build_dashboard_kpis,
    build_dashboard_metrics,
    build_dashboard_movements,
    build_dashboard_overview,
)


@pytest.fixture(autouse=True)
def _clear_dashboard_cache():
    """Limpia la caché del dashboard antes de cada test para evitar contaminación."""
    cache.clear()
    yield
    cache.clear()


# ── Servicio: estructura del payload ──────────────────────────────────────────


@pytest.mark.django_db
def test_dashboard_service_overview_stays_structured(db):
    payload = build_dashboard_overview()
    assert set(payload.keys()) == {
        "metrics",
        "alerts",
        "kpis",
        "movements",
        "generated_at",
    }


@pytest.mark.django_db
def test_dashboard_metrics_empty_db_returns_zeros(db):
    m = build_dashboard_metrics()
    assert m["stock_total"] == 0
    assert m["dispatches_today"] == 0
    assert m["reorder_count"] == 0
    assert m["invoices_issued"] == 0
    assert m["invoice_range"] is None


@pytest.mark.django_db
def test_dashboard_alerts_empty_db_returns_zeros(db):
    a = build_dashboard_alerts()
    assert a["active"] == 0
    assert a["reorder"] == 0
    assert a["expiring"] == 0
    assert a["returns"] == 0


@pytest.mark.django_db
def test_dashboard_kpis_no_data_returns_zero_or_null_values(db):
    """Sin stock ni movimientos, la utilización debe ser None (sin capacidad) o 0.0 (sin stock)."""
    kpis = build_dashboard_kpis()
    assert kpis["warehouse_utilization"]["value"] in (None, 0.0)
    assert kpis["damaged_rate"]["value"] == 0.0
    assert kpis["dispatch_invoice_ratio"]["value"] == 0.0


@pytest.mark.django_db
def test_dashboard_movements_empty_db_returns_empty_list(db):
    mvs = build_dashboard_movements()
    assert mvs == []


@pytest.mark.django_db
def test_dashboard_metrics_stock_total_reflects_stock_by_location(
    almacenista_user, sample_locations, db
):
    from apps.inventory.models import StockByLocation
    from tests.factories import ProductFactory

    p1 = ProductFactory()
    p2 = ProductFactory()
    loc = sample_locations[0]
    StockByLocation.objects.create(product=p1, location=loc, current_stock=10)
    StockByLocation.objects.create(product=p2, location=loc, current_stock=5)

    m = build_dashboard_metrics()
    assert m["stock_total"] == 15


@pytest.mark.django_db
def test_dashboard_metrics_reorder_count_uses_reorder_point(sample_locations, db):
    from apps.inventory.models import StockByLocation
    from tests.factories import ProductFactory

    below = ProductFactory(reorder_point=10)
    above = ProductFactory(reorder_point=2)
    loc = sample_locations[0]
    StockByLocation.objects.create(product=below, location=loc, current_stock=3)
    StockByLocation.objects.create(product=above, location=loc, current_stock=5)

    m = build_dashboard_metrics()
    assert m["reorder_count"] >= 1


@pytest.mark.django_db
def test_dashboard_alerts_counts_only_unresolved(sample_product, sample_locations, db):
    loc = sample_locations[0]
    Alert.objects.create(
        alert_type=AlertType.LOW_STOCK,
        product=sample_product,
        location=loc,
        message="bajo",
        is_resolved=False,
    )
    Alert.objects.create(
        alert_type=AlertType.LOW_STOCK,
        product=sample_product,
        location=loc,
        message="resuelto",
        is_resolved=True,
    )
    a = build_dashboard_alerts()
    assert a["active"] == 1
    assert a["reorder"] == 1


@pytest.mark.django_db
def test_dashboard_movements_list_returns_expected_shape(
    almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    loc = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.ENTRADA,
        product=product,
        quantity=3,
        destination_location=loc,
        executed_by=almacenista_user,
    )
    mvs = build_dashboard_movements()
    assert len(mvs) >= 1
    mv = mvs[0]
    assert "id" in mv
    assert mv["type"] == "in"
    assert mv["quantity"] == 3
    assert "sku" in mv
    assert "user" in mv
    assert "time" in mv
    assert "status" in mv


# ── API: autenticación y control de acceso ────────────────────────────────────


@pytest.mark.django_db
def test_dashboard_overview_requires_authentication(api_client):
    r = api_client.get(reverse("dashboard-overview"))
    assert r.status_code == 401


@pytest.mark.django_db
def test_dashboard_overview_blocked_for_administrador(
    authenticated_administrador_client,
):
    r = authenticated_administrador_client.get(reverse("dashboard-overview"))
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_metrics_endpoint_returns_200(authenticated_almacenista_client):
    r = authenticated_almacenista_client.get(reverse("dashboard-metrics"))
    assert r.status_code == 200
    assert "stock_total" in r.data
    assert "reorder_count" in r.data


@pytest.mark.django_db
def test_dashboard_alerts_endpoint_returns_200(authenticated_almacenista_client):
    r = authenticated_almacenista_client.get(reverse("dashboard-alerts"))
    assert r.status_code == 200
    assert "active" in r.data
    assert "reorder" in r.data


@pytest.mark.django_db
def test_dashboard_kpis_endpoint_returns_200(authenticated_almacenista_client):
    r = authenticated_almacenista_client.get(reverse("dashboard-kpis"))
    assert r.status_code == 200
    assert "warehouse_utilization" in r.data
    assert "damaged_rate" in r.data
    assert "dispatch_invoice_ratio" in r.data


@pytest.mark.django_db
def test_dashboard_movements_endpoint_returns_list(authenticated_almacenista_client):
    r = authenticated_almacenista_client.get(reverse("dashboard-movements"))
    assert r.status_code == 200
    assert isinstance(r.data, list)


@pytest.mark.django_db
def test_dashboard_overview_returns_composable_payload(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory(reorder_point=3)
    location = sample_locations[0]
    StockByLocation.objects.create(product=product, location=location, current_stock=2)
    Movement.objects.create(
        movement_type=MovementType.ENTRADA,
        product=product,
        quantity=2,
        destination_location=location,
        executed_by=almacenista_user,
    )
    Alert.objects.create(
        alert_type=AlertType.LOW_STOCK,
        product=product,
        location=location,
        message="Stock bajo",
    )

    response = authenticated_almacenista_client.get("/api/v1/dashboard/overview/")
    assert response.status_code == 200
    assert "metrics" in response.data
    assert "alerts" in response.data
    assert "kpis" in response.data
    assert "movements" in response.data
    assert isinstance(response.data["movements"], list)
    assert response.data["alerts"]["active"] >= 1
    assert response.data["metrics"]["reorder_count"] >= 1


@pytest.mark.django_db
def test_dashboard_kpis_expose_precision_metadata(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.inventory.models import Location, StockByLocation
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory(reorder_point=1, requires_cold_chain=True)
    location = Location.objects.create(
        code="BODEGA-DASH",
        name="Bodega Dash",
        max_capacity=10,
        is_active=True,
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=4)
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENTA_MENOR,
        product=product,
        quantity=2,
        quantity_invoiced=2,
        invoice_number="D-001",
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get("/api/v1/dashboard/kpis/")
    assert response.status_code == 200
    assert response.data["warehouse_utilization"]["precision"] == "real"
    assert response.data["dispatch_invoice_ratio"]["precision"] == "partial"
    assert response.data["cold_chain_alerts"]["precision"] in {"future", "partial"}
    assert "value" in response.data["damaged_rate"]
