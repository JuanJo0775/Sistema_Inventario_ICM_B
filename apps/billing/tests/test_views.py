"""Tests de API endpoints de billing."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.billing.services import create_multi_dispatch_invoice, void_invoice
from apps.movements.models import Invoice
from apps.movements.services import register_entry
from tests.factories import ProductFactory


def _seed(user, product, location, qty):
    register_entry(user, product.id, location.id, qty)


# ---------------------------------------------------------------------------
# GET /billing/invoices/ — listado
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_invoice_list_requires_auth(api_client):
    url = reverse("billing-invoice-list")
    resp = api_client.get(url)
    assert resp.status_code == 401


@pytest.mark.django_db
def test_invoice_list_invalid_date_does_not_raise_500(almacenista_user, api_client):
    """Fechas inválidas en ?start_date o ?end_date son ignoradas, no provocan 500."""
    api_client.force_authenticate(user=almacenista_user)
    resp = api_client.get(
        reverse("billing-invoice-list") + "?start_date=not-a-date&end_date=bad"
    )
    assert resp.status_code == 200


@pytest.mark.django_db
def test_invoice_list_returns_invoices(almacenista_user, sample_locations, api_client):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)
    create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Cliente"},
        items=[{"product_id": p.id, "quantity": 1}],
    )

    resp = api_client.get(reverse("billing-invoice-list"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1


@pytest.mark.django_db
def test_invoice_list_excludes_voided_by_default(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )
    void_invoice(invoice.pk, user=almacenista_user, reason="Test")

    resp = api_client.get(reverse("billing-invoice-list"))
    assert resp.status_code == 200
    numbers = [inv["number"] for inv in resp.json()["results"]]
    assert invoice.number not in numbers


@pytest.mark.django_db
def test_invoice_list_includes_voided_with_param(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )
    void_invoice(invoice.pk, user=almacenista_user, reason="Test")

    resp = api_client.get(reverse("billing-invoice-list") + "?include_voided=true")
    numbers = [inv["number"] for inv in resp.json()["results"]]
    assert invoice.number in numbers


# ---------------------------------------------------------------------------
# POST /billing/invoices/ — crear factura multi-producto
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_invoice_success(almacenista_user, sample_locations, api_client):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p1 = ProductFactory(sale_price_retail=Decimal("10000"), tax_rate_pct=Decimal("0"))
    p2 = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p1, loc, 5)
    _seed(almacenista_user, p2, loc, 5)

    payload = {
        "invoice_type": "retail",
        "location_id": str(loc.id),
        "customer": {"name": "Juan García", "id_number": "12345678"},
        "items": [
            {"product_id": str(p1.id), "quantity": 2},
            {"product_id": str(p2.id), "quantity": 3},
        ],
    }
    resp = api_client.post(reverse("billing-invoice-list"), payload, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["number"].startswith("ICM-")
    assert data["invoice_type"] == "retail"
    assert data["customer_id_number"] == "12345678"
    assert Decimal(data["subtotal"]) == Decimal("35000.0000")


@pytest.mark.django_db
def test_create_invoice_insufficient_stock_returns_409(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("100"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 1)

    payload = {
        "invoice_type": "retail",
        "location_id": str(loc.id),
        "customer": {"name": "Test"},
        "items": [{"product_id": str(p.id), "quantity": 999}],
    }
    resp = api_client.post(reverse("billing-invoice-list"), payload, format="json")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_create_invoice_empty_items_returns_400(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    payload = {
        "invoice_type": "retail",
        "location_id": str(sample_locations[1].id),
        "customer": {"name": "Test"},
        "items": [],
    }
    resp = api_client.post(reverse("billing-invoice-list"), payload, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_invoice_atomicity_on_second_item_fail(
    almacenista_user, sample_locations, api_client
):
    """Si el segundo ítem falla, el primero tampoco debe haberse persistido."""
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p1 = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    p2 = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p1, loc, 5)
    # p2 sin stock

    invoice_count_before = Invoice.objects.count()

    payload = {
        "invoice_type": "retail",
        "location_id": str(loc.id),
        "customer": {"name": "Test"},
        "items": [
            {"product_id": str(p1.id), "quantity": 1},
            {"product_id": str(p2.id), "quantity": 1},  # falla: sin stock
        ],
    }
    resp = api_client.post(reverse("billing-invoice-list"), payload, format="json")
    assert resp.status_code == 409
    # La transacción completa debe haberse revertido
    assert Invoice.objects.count() == invoice_count_before


# ---------------------------------------------------------------------------
# GET /billing/invoices/{id}/ — detalle
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_invoice_detail_returns_movements(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("7000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 2}],
    )

    resp = api_client.get(reverse("billing-invoice-detail", kwargs={"pk": invoice.pk}))
    assert resp.status_code == 200
    data = resp.json()
    assert data["number"] == invoice.number
    assert len(data["movements_detail"]) >= 1


@pytest.mark.django_db
def test_invoice_detail_404(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    resp = api_client.get(reverse("billing-invoice-detail", kwargs={"pk": 99999}))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /billing/invoices/{id}/void/ — anular
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_void_invoice_endpoint(almacenista_user, sample_locations, api_client):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )

    resp = api_client.post(
        reverse("billing-invoice-void", kwargs={"pk": invoice.pk}),
        {"reason": "Cliente cambió de opinión"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["is_voided"] is True


@pytest.mark.django_db
def test_void_invoice_already_voided_returns_409(
    almacenista_user, sample_locations, api_client
):
    """Segunda anulación sobre la misma factura devuelve 409."""
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )
    api_client.post(
        reverse("billing-invoice-void", kwargs={"pk": invoice.pk}),
        {"reason": "Primera vez, correcto"},
        format="json",
    )
    resp = api_client.post(
        reverse("billing-invoice-void", kwargs={"pk": invoice.pk}),
        {"reason": "Segunda vez, debe fallar"},
        format="json",
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "INVOICE_ALREADY_VOIDED"


@pytest.mark.django_db
def test_void_invoice_nonexistent_returns_404(almacenista_user, api_client):
    """Anular factura inexistente devuelve 404."""
    api_client.force_authenticate(user=almacenista_user)
    resp = api_client.post(
        reverse("billing-invoice-void", kwargs={"pk": 99999}),
        {"reason": "Motivo de prueba valido"},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_void_invoice_without_reason_returns_400(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )

    resp = api_client.post(
        reverse("billing-invoice-void", kwargs={"pk": invoice.pk}),
        {"reason": "no"},  # menos de 5 chars
        format="json",
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /billing/invoices/stats/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_invoice_stats_endpoint(almacenista_user, sample_locations, api_client):
    api_client.force_authenticate(user=almacenista_user)
    resp = api_client.get(reverse("billing-invoice-stats"))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_sales_today" in data
    assert "invoice_count_month" in data


# ---------------------------------------------------------------------------
# GET/PUT /billing/config/company/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_auxiliar_cannot_void_invoice(
    auxiliar_user, almacenista_user, sample_locations, api_client
):
    """Auxiliar de despacho no puede anular facturas (solo almacenista)."""
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    from apps.movements.services import register_entry

    register_entry(almacenista_user, p.id, loc.id, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )

    api_client.force_authenticate(user=auxiliar_user)
    resp = api_client.post(
        reverse("billing-invoice-void", kwargs={"pk": invoice.pk}),
        {"reason": "Auxiliar intenta anular"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_administrador_cannot_create_invoice(
    administrador_user, sample_locations, api_client
):
    """Administrador no puede crear facturas (solo operativos)."""
    api_client.force_authenticate(user=administrador_user)
    payload = {
        "invoice_type": "retail",
        "location_id": str(sample_locations[1].id),
        "customer": {"name": "Test"},
        "items": [
            {"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}
        ],
    }
    resp = api_client.post(reverse("billing-invoice-list"), payload, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_company_config_get(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    resp = api_client.get(reverse("billing-company-config"))
    assert resp.status_code == 200
    assert "company_name" in resp.json()


@pytest.mark.django_db
def test_company_config_put(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    payload = {
        "company_name": "ICM Test",
        "nit": "900-1",
        "address": "Cra 1 #2-3",
        "invoice_series": "ICM",
    }
    resp = api_client.put(reverse("billing-company-config"), payload, format="json")
    assert resp.status_code == 200
    assert resp.json()["nit"] == "900-1"


@pytest.mark.django_db
def test_company_config_put_requires_almacenista(administrador_user, api_client):
    """Administrador solo puede leer, no puede editar datos de empresa."""
    api_client.force_authenticate(user=administrador_user)
    resp = api_client.put(
        reverse("billing-company-config"),
        {"company_name": "Hack"},
        format="json",
    )
    assert resp.status_code == 403
