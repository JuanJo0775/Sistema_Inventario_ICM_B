from apps.reports.views import (
    DiscardOperationalReportView,
    DispatchOperationalReportView,
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


def test_reports_dataset_view_is_available(authenticated_almacenista_client):
    response = authenticated_almacenista_client.get(
        "/api/v1/reports/data/", {"kind": "kpi"}
    )
    assert response.status_code == 200
    assert response.data["report"] == "kpi"
    assert "data" in response.data


def test_reports_warehouse_utilization_view_returns_summary(
    authenticated_almacenista_client, db
):
    from apps.inventory.models import Location, StockByLocation
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = Location.objects.create(
        code="BODEGA-KPI",
        name="Bodega KPI",
        max_capacity=20,
        is_active=True,
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=8)

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/warehouse-utilization/"
    )
    assert response.status_code == 200
    row = next(
        item for item in response.data["by_location"] if item["code"] == "BODEGA-KPI"
    )
    assert row["occupied_units"] == 8
    assert row["capacity_units"] == 20
    assert row["utilization_pct"] == 40.0


def test_reports_dataset_view_supports_warehouse_utilization(
    authenticated_almacenista_client, db
):
    from apps.inventory.models import Location, StockByLocation
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = Location.objects.create(
        code="BODEGA-KPI-2",
        name="Bodega KPI 2",
        max_capacity=10,
        is_active=True,
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=3)

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/data/", {"kind": "warehouse-utilization"}
    )
    assert response.status_code == 200
    assert response.data["report"] == "warehouse-utilization"
    row = next(
        item
        for item in response.data["data"]["by_location"]
        if item["code"] == "BODEGA-KPI-2"
    )
    assert row["capacity_units"] == 10


def test_reports_quality_operational_view_returns_summary(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_DANO,
        product=product,
        quantity=2,
        origin_location=location,
        executed_by=almacenista_user,
    )
    Movement.objects.create(
        movement_type=MovementType.DEVOLUCION,
        product=product,
        quantity=1,
        origin_location=location,
        destination_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/quality-operational/"
    )
    assert response.status_code == 200
    assert response.data["totals"]["units"] >= 3
    assert response.data["breakdown"]["incident_units"] >= 3
    assert any(
        item["movement_type"] == "SALIDA_DANO" for item in response.data["by_type"]
    )


def test_reports_dataset_view_supports_quality_operational(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENCIMIENTO,
        product=product,
        quantity=4,
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/data/", {"kind": "quality-operational", "period_days": 30}
    )
    assert response.status_code == 200
    assert response.data["report"] == "quality-operational"
    assert response.data["data"]["totals"]["units"] >= 4
    assert response.data["data"]["breakdown"]["discard_units"] >= 4


def test_reports_discard_operational_view_returns_summary(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENCIMIENTO,
        product=product,
        quantity=6,
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/discard-operational/"
    )
    assert response.status_code == 200
    assert response.data["totals"]["units"] == 6
    assert any(
        item["movement_type"] == "SALIDA_VENCIMIENTO"
        for item in response.data["by_type"]
    )


def test_reports_dispatch_operational_view_returns_summary(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENTA_MAYOR,
        product=product,
        quantity=5,
        quantity_invoiced=5,
        invoice_number="F-001",
        origin_location=location,
        executed_by=almacenista_user,
    )
    # add a second shipment without invoice to ensure shipments counts multiples
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENTA_MENOR,
        product=product,
        quantity=1,
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/dispatch-operational/"
    )
    assert response.status_code == 200
    assert response.data["sales"]["mayor"] == 5
    assert response.data["invoice_linked_dispatches"] == 1
    assert response.data["period"]["days"] == 30
    # nuevos campos contractuales y valores derivados
    assert "shipments" in response.data
    assert isinstance(response.data["shipments"], int)
    assert response.data["shipments"] >= 2
    assert "invoice_linked_ratio" in response.data
    assert isinstance(response.data["invoice_linked_ratio"], float)
    assert "order_proxy" in response.data
    assert isinstance(response.data["order_proxy"], list)
    assert "carriers" in response.data
    assert isinstance(response.data["carriers"], dict)
    assert "per_order_samples" in response.data
    assert isinstance(response.data["per_order_samples"], list)
    # should include the invoice sample we created
    assert any(
        p.get("invoice_number") == "F-001" for p in response.data["per_order_samples"]
    )
    assert "promised_date_example" in response.data


def test_reports_dataset_view_supports_dispatch_operational(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENTA_MENOR,
        product=product,
        quantity=2,
        quantity_invoiced=2,
        invoice_number="F-002",
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/data/", {"kind": "dispatch-operational", "period_days": 30}
    )
    assert response.status_code == 200
    assert response.data["report"] == "dispatch-operational"
    assert response.data["data"]["sales"]["menor"] == 2
    # dataset should include the new fields as well and example invoice
    assert "shipments" in response.data["data"]
    assert response.data["data"]["shipments"] >= 1
    assert "invoice_linked_ratio" in response.data["data"]
    assert "order_proxy" in response.data["data"]
    assert "carriers" in response.data["data"]
    assert "per_order_samples" in response.data["data"]
    assert any(
        p.get("invoice_number") == "F-002" or p.get("invoice_number") == "F-001"
        for p in response.data["data"]["per_order_samples"]
    )
    assert "promised_date_example" in response.data["data"]


def test_reports_dataset_view_supports_discard_operational(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_DANO,
        product=product,
        quantity=4,
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/data/", {"kind": "discard-operational", "period_days": 30}
    )
    assert response.status_code == 200
    assert response.data["report"] == "discard-operational"
    assert response.data["data"]["totals"]["units"] == 4


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
    assert WarehouseUtilizationReportView is not None
    assert QualityOperationalReportView is not None
    assert DiscardOperationalReportView is not None
    assert DispatchOperationalReportView is not None
    assert InvoiceHistoryReportView is not None
    assert KpiDashboardReportView is not None
    assert ExpiringProductsReportView is not None
    assert ReportDatasetView is not None


def test_dispatch_orders_endpoint_returns_samples(
    authenticated_almacenista_client, almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_VENTA_MAYOR,
        product=product,
        quantity=3,
        quantity_invoiced=3,
        invoice_number="ORD-100",
        origin_location=location,
        executed_by=almacenista_user,
    )

    response = authenticated_almacenista_client.get(
        "/api/v1/reports/dispatch-operational/orders/"
    )
    assert response.status_code == 200
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    assert any(
        item.get("invoice_number") == "ORD-100" for item in response.data["results"]
    )
