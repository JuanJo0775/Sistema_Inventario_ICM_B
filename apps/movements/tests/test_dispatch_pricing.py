"""Tests para el snapshot de precio en despachos (Fase 2)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.movements.models import Movement, MovementType
from apps.movements.services import register_dispatch, register_entry
from tests.factories import ProductFactory

# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------


def _seed_stock(user, product, location, qty):
    register_entry(user, product.id, location.id, qty)


# ---------------------------------------------------------------------------
# Snapshot de precio: retail
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dispatch_retail_captures_sale_price_retail_as_unit_price(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        sale_price_retail=Decimal("12000.0000"),
        tax_rate_pct=Decimal("0.00"),
        currency="COP",
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
    assert m.unit_price == Decimal("12000.0000")
    assert m.price_type == "retail"
    assert m.currency == "COP"


@pytest.mark.django_db
def test_dispatch_wholesale_captures_sale_price_wholesale(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        sale_price_wholesale=Decimal("9000.0000"),
        tax_rate_pct=Decimal("0.00"),
        currency="COP",
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 20)

    customer = {
        "customer_name": "Test SA",
        "customer_email": "test@test.com",
        "customer_phone": "3001234567",
        "customer_address": "Calle 1 # 2-3",
        "privacy_notice_acknowledged": True,
    }
    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        5,
        MovementType.SALIDA_VENTA_MAYOR,
        customer_data=customer,
    )
    assert m.unit_price == Decimal("9000.0000")
    assert m.price_type == "wholesale"
    assert m.subtotal == Decimal("9000.0000") * 5


@pytest.mark.django_db
def test_dispatch_calculates_subtotal_tax_total_correctly(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("19.00"),
        currency="COP",
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 5)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        3,
        MovementType.SALIDA_VENTA_MENOR,
    )
    # subtotal = 10000 * 3 = 30000
    # tax = 30000 * 0.19 = 5700
    # total = 35700
    assert m.subtotal == Decimal("30000.0000")
    assert m.tax_amount == Decimal("5700.0000")
    assert m.total_amount == Decimal("35700.0000")
    assert m.tax_rate_pct == Decimal("19.00")


@pytest.mark.django_db
def test_dispatch_with_discount_calculates_correctly(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("0.00"),
        currency="COP",
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 5)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        2,
        MovementType.SALIDA_VENTA_MENOR,
        discount_pct=Decimal("10"),
    )
    # subtotal = 20000, discount = 2000, total = 18000
    assert m.subtotal == Decimal("20000.0000")
    assert m.discount_pct == Decimal("10")
    assert m.discount_amount == Decimal("2000.0000")
    assert m.total_amount == Decimal("18000.0000")


@pytest.mark.django_db
def test_dispatch_without_product_price_stores_null_gracefully(
    almacenista_user, sample_locations
):
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
    assert m.unit_price is None
    assert m.subtotal is None
    assert m.total_amount is None
    assert m.currency == "COP"  # siempre se captura la moneda del producto


@pytest.mark.django_db
def test_customer_snapshot_persisted_on_wholesale_dispatch(
    almacenista_user, sample_locations
):
    product = ProductFactory(sale_price_wholesale=Decimal("5000.0000"))
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 10)

    customer = {
        "customer_name": "Empresa XYZ",
        "customer_email": "xyz@empresa.com",
        "customer_phone": "3109876543",
        "customer_address": "Av Siempre Viva 123",
        "privacy_notice_acknowledged": True,
    }
    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        2,
        MovementType.SALIDA_VENTA_MAYOR,
        customer_data=customer,
    )
    assert m.customer_snapshot is not None
    assert m.customer_snapshot["customer_name"] == "Empresa XYZ"
    assert m.customer_snapshot["customer_email"] == "xyz@empresa.com"


@pytest.mark.django_db
def test_retail_dispatch_has_no_customer_snapshot(almacenista_user, sample_locations):
    product = ProductFactory(sale_price_retail=Decimal("8000.0000"))
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 5)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        1,
        MovementType.SALIDA_VENTA_MENOR,
    )
    assert m.customer_snapshot is None


@pytest.mark.django_db
def test_price_snapshot_immutable_after_product_price_change(
    almacenista_user, sample_locations
):
    """El precio congelado en el Movement no cambia si se modifica el producto."""
    from apps.catalog.services import update_product_prices

    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 10)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        1,
        MovementType.SALIDA_VENTA_MENOR,
    )
    original_price = m.unit_price

    # Cambiar el precio del producto
    update_product_prices(
        almacenista_user, product.id, sale_price_retail=Decimal("20000.0000")
    )

    m.refresh_from_db()
    assert m.unit_price == original_price  # sigue siendo el precio histórico


@pytest.mark.django_db
def test_damage_dispatch_uses_unit_cost_as_price_type(
    almacenista_user, sample_locations
):
    product = ProductFactory(
        unit_cost=Decimal("4000.0000"),
        sale_price_retail=Decimal("10000.0000"),
    )
    loc = sample_locations[1]
    _seed_stock(almacenista_user, product, loc, 5)

    [m] = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        1,
        MovementType.SALIDA_DANO,
    )
    assert m.price_type == "cost"
    assert m.unit_price == Decimal("4000.0000")


@pytest.mark.django_db
def test_movement_serializer_exposes_price_fields(
    almacenista_user, sample_locations, api_client
):
    from django.urls import reverse

    api_client.force_authenticate(user=almacenista_user)
    product = ProductFactory(
        sale_price_retail=Decimal("7500.0000"),
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
    url = reverse("movements-dispatch-detail", kwargs={"pk": m.id})
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert "unit_price" in data
    assert data["unit_price"] == "7500.0000"
    assert data["subtotal"] == "15000.0000"
    assert data["currency"] == "COP"
    assert data["price_type"] == "retail"
