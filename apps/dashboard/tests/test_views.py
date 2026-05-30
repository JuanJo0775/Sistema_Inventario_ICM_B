from apps.alerts.models import Alert, AlertType
from apps.dashboard.services import build_dashboard_overview


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


def test_dashboard_service_overview_stays_structured(db):
    payload = build_dashboard_overview()
    assert set(payload.keys()) == {
        "metrics",
        "alerts",
        "kpis",
        "movements",
        "generated_at",
    }
