"""Tests para reportes financieros (Fase 5)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.movements.models import MovementType
from apps.movements.services import register_dispatch, register_entry
from apps.reports.selectors import (
    gross_margin_by_product,
    sales_by_customer,
    sales_revenue_summary,
)
from tests.factories import ProductFactory


def _seed_and_dispatch_retail(user, product, location, qty):
    register_entry(user, product.id, location.id, qty)
    return register_dispatch(
        user, product.id, location.id, qty, MovementType.SALIDA_VENTA_MENOR
    )


def _seed_and_dispatch_wholesale(user, product, location, qty, customer):
    register_entry(user, product.id, location.id, qty)
    return register_dispatch(
        user,
        product.id,
        location.id,
        qty,
        MovementType.SALIDA_VENTA_MAYOR,
        customer_data=customer,
    )


# ---------------------------------------------------------------------------
# sales_revenue_summary
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_revenue_summary_returns_correct_totals(almacenista_user, sample_locations):
    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_and_dispatch_retail(almacenista_user, product, loc, 3)

    now = timezone.now()
    result = sales_revenue_summary(start=now - timedelta(hours=1), end=now)

    assert result["retail"]["units"] == 3
    assert result["retail"]["total"] == Decimal("30000.0000")
    assert result["combined"]["total"] == Decimal("30000.0000")


@pytest.mark.django_db
def test_revenue_summary_separates_wholesale_and_retail(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        sale_price_retail=Decimal("5000.0000"),
        sale_price_wholesale=Decimal("4000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    customer = {
        "customer_name": "Empresa ABC",
        "customer_email": "abc@emp.com",
        "customer_phone": "3001234567",
        "customer_address": "Calle 1",
        "privacy_notice_acknowledged": True,
    }
    _seed_and_dispatch_retail(almacenista_user, product, loc, 2)
    _seed_and_dispatch_wholesale(almacenista_user, product, loc, 5, customer)

    now = timezone.now()
    result = sales_revenue_summary(start=now - timedelta(hours=1), end=now)
    assert result["retail"]["units"] == 2
    assert result["wholesale"]["units"] == 5
    assert result["combined"]["units"] == 7


@pytest.mark.django_db
def test_revenue_summary_products_without_price_contribute_zero(
    almacenista_user, sample_locations
):
    product = ProductFactory()  # sin precio
    loc = sample_locations[1]
    _seed_and_dispatch_retail(almacenista_user, product, loc, 10)

    now = timezone.now()
    result = sales_revenue_summary(start=now - timedelta(hours=1), end=now)
    assert result["retail"]["total"] == Decimal("0")


# ---------------------------------------------------------------------------
# gross_margin_by_product
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_gross_margin_correct_when_cost_and_price_set(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        unit_cost=Decimal("4000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_and_dispatch_retail(almacenista_user, product, loc, 2)

    now = timezone.now()
    result = gross_margin_by_product(start=now - timedelta(hours=1), end=now)

    assert len(result) >= 1
    row = next(r for r in result if r["sku"] == product.sku)
    assert row["revenue"] == Decimal("20000.0000")
    assert row["cogs"] == Decimal("8000.0000")
    assert row["gross_margin"] == Decimal("12000.0000")
    assert row["gross_margin_pct"] == Decimal("60.00")


@pytest.mark.django_db
def test_gross_margin_excludes_movements_without_price(
    almacenista_user, sample_locations
):
    product = ProductFactory()  # sin precio
    loc = sample_locations[1]
    _seed_and_dispatch_retail(almacenista_user, product, loc, 5)

    now = timezone.now()
    result = gross_margin_by_product(start=now - timedelta(hours=1), end=now)
    skus = [r["sku"] for r in result]
    assert product.sku not in skus


# ---------------------------------------------------------------------------
# sales_by_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sales_by_customer_aggregates_correctly(almacenista_user, sample_locations):
    product = ProductFactory(
        sale_price_wholesale=Decimal("5000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    customer = {
        "customer_name": "Cliente Nuevo",
        "customer_email": "nuevo@test.com",
        "customer_phone": "3009876543",
        "customer_address": "Av 2",
        "privacy_notice_acknowledged": True,
    }
    _seed_and_dispatch_wholesale(almacenista_user, product, loc, 3, customer)

    now = timezone.now()
    result = sales_by_customer(start=now - timedelta(hours=1), end=now)
    assert len(result) >= 1
    row = next(r for r in result if r["customer_name"] == "Cliente Nuevo")
    assert row["units"] == 3
    assert row["revenue"] == Decimal("15000.0000")


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_api_revenue_summary_returns_200(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("reports-revenue-summary")
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert "retail" in data
    assert "wholesale" in data
    assert "combined" in data


@pytest.mark.django_db
def test_api_margin_by_product_returns_200(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("reports-margin-by-product")
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db
def test_api_sales_by_customer_returns_200(almacenista_user, api_client):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("reports-sales-by-customer")
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db
def test_api_revenue_summary_requires_auth(api_client):
    url = reverse("reports-revenue-summary")
    resp = api_client.get(url)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Webhook dispatch.completed
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_webhook_emitted_on_dispatch_with_price(almacenista_user, sample_locations, db):
    from apps.webhooks.models import WebhookDelivery, WebhookEndpoint

    # Crear endpoint suscrito a dispatch.completed
    endpoint = WebhookEndpoint.objects.create(
        url="http://localhost:9999/webhook",
        secret="test-secret",
        events=["dispatch.completed"],
        is_active=True,
    )

    product = ProductFactory(
        sale_price_retail=Decimal("8000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 5)
    register_dispatch(
        almacenista_user, product.id, loc.id, 1, MovementType.SALIDA_VENTA_MENOR
    )

    deliveries = WebhookDelivery.objects.filter(endpoint=endpoint)
    assert deliveries.count() >= 1
    delivery = deliveries.first()
    assert delivery.event_type == "dispatch.completed"
    assert delivery.payload["product_sku"] == product.sku
