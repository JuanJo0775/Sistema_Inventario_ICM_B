"""Tests para el modelo Invoice y PDF enriquecido (Fase 3)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.movements.models import Invoice, MovementType
from apps.movements.services import (
    create_invoice_from_movements,
    register_dispatch,
    register_entry,
)
from tests.factories import ProductFactory


def _seed_stock(user, product, location, qty):
    register_entry(user, product.id, location.id, qty)


# ---------------------------------------------------------------------------
# create_invoice_from_movements
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_invoice_created_on_dispatch(almacenista_user, sample_locations):
    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 5)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        2,
        MovementType.SALIDA_VENTA_MENOR,
    )
    invoice = Invoice.objects.filter(number=m.invoice_number).first()
    assert invoice is not None
    assert m in invoice.movements.all()


@pytest.mark.django_db
def test_invoice_totals_match_sum_of_movements(almacenista_user, sample_locations):
    product = ProductFactory(
        sale_price_retail=Decimal("5000.0000"),
        tax_rate_pct=Decimal("19.00"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 10)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        3,
        MovementType.SALIDA_VENTA_MENOR,
    )
    invoice = Invoice.objects.get(number=m.invoice_number)
    # subtotal = 5000 * 3 = 15000; tax = 15000 * 0.19 = 2850; total = 17850
    assert invoice.subtotal == Decimal("15000.0000")
    assert invoice.tax_total == Decimal("2850.0000")
    assert invoice.total_amount == Decimal("17850.0000")
    assert invoice.currency == "COP"


@pytest.mark.django_db
def test_invoice_has_customer_data_on_wholesale(almacenista_user, sample_locations):
    product = ProductFactory(
        sale_price_wholesale=Decimal("8000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 10)

    customer = {
        "customer_name": "Distribuidora ABC",
        "customer_email": "abc@dist.com",
        "customer_phone": "3001234567",
        "customer_address": "Calle 10 # 5-20",
        "privacy_notice_acknowledged": True,
    }
    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        4,
        MovementType.SALIDA_VENTA_MAYOR,
        customer_data=customer,
    )
    invoice = Invoice.objects.get(number=m.invoice_number)
    assert invoice.customer_name == "Distribuidora ABC"
    assert invoice.customer_email == "abc@dist.com"


@pytest.mark.django_db
def test_invoice_without_price_has_zero_totals(almacenista_user, sample_locations):
    product = ProductFactory()  # sin precios
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 5)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        1,
        MovementType.SALIDA_VENTA_MENOR,
    )
    invoice = Invoice.objects.get(number=m.invoice_number)
    assert invoice.subtotal == Decimal("0")
    assert invoice.total_amount == Decimal("0")


@pytest.mark.django_db
def test_create_invoice_from_movements_manually(almacenista_user, sample_locations):
    product = ProductFactory(
        sale_price_retail=Decimal("3000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 10)

    movements = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        2,
        MovementType.SALIDA_VENTA_MENOR,
    )
    inv_number = movements[0].invoice_number
    invoice = create_invoice_from_movements(
        movements,
        user=almacenista_user,
        invoice_number=inv_number + "-DUP",
    )
    assert invoice.subtotal == Decimal("6000.0000")
    assert invoice.movements.count() == len(movements)


# ---------------------------------------------------------------------------
# API endpoint: GET /movements/invoices/<number>/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_api_invoice_detail_returns_correct_data(
    almacenista_user, sample_locations, api_client
):
    api_client.force_authenticate(user=almacenista_user)
    product = ProductFactory(
        sale_price_retail=Decimal("7000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 10)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        2,
        MovementType.SALIDA_VENTA_MENOR,
    )
    url = reverse("movements-invoice-detail", kwargs={"number": m.invoice_number})
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["number"] == m.invoice_number
    assert data["subtotal"] == "14000.0000"
    assert data["total_amount"] == "14000.0000"
    assert str(m.id) in data["movement_ids"]


@pytest.mark.django_db
def test_api_invoice_detail_404_for_unknown_number(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("movements-invoice-detail", kwargs={"number": "ICM-9999"})
    resp = api_client.get(url)
    assert resp.status_code == 404
