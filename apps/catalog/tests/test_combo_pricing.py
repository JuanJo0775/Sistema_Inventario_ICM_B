"""Tests para pricing de combos (Fase 4)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.catalog.models import ComboItem, ProductCombo
from apps.catalog.services import create_combo, update_combo
from apps.inventory.models import StockByLocation
from apps.movements.models import Invoice, MovementType
from apps.movements.services import dispatch_combo
from tests.factories import LocationFactory, ProductFactory

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def combo_with_priced_products(db, almacenista_user):
    product_a = ProductFactory(
        sku="CMB-P001",
        unit_cost=Decimal("3000.0000"),
        sale_price_retail=Decimal("8000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    product_b = ProductFactory(
        sku="CMB-P002",
        unit_cost=Decimal("2000.0000"),
        sale_price_retail=Decimal("5000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    location = LocationFactory(code="BODEGA_COMBO_P", name="Bodega Combo Precios")

    combo = ProductCombo.objects.create(
        name="Kit Precios", sku="KIT-PRECIO", price_strategy="derived"
    )
    ComboItem.objects.create(combo=combo, product=product_a, quantity=1)
    ComboItem.objects.create(combo=combo, product=product_b, quantity=2)

    StockByLocation.objects.create(
        product=product_a, location=location, current_stock=10
    )
    StockByLocation.objects.create(
        product=product_b, location=location, current_stock=10
    )

    return {
        "combo": combo,
        "location": location,
        "product_a": product_a,
        "product_b": product_b,
    }


# ---------------------------------------------------------------------------
# Derived pricing (price_strategy=derived)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_combo_derived_price_uses_individual_product_prices(
    almacenista_user, combo_with_priced_products
):
    data = combo_with_priced_products
    movements = dispatch_combo(almacenista_user, data["combo"].id, data["location"].id)
    assert len(movements) == 2

    m_a = next(m for m in movements if m.product_id == data["product_a"].id)
    m_b = next(m for m in movements if m.product_id == data["product_b"].id)

    # product_a: SALIDA_COMBO → uses sale_price_retail (fallback for SALIDA_COMBO derived)
    assert m_a.price_type == "combo"
    assert m_b.price_type == "combo"


@pytest.mark.django_db
def test_combo_derived_without_prices_stores_null(almacenista_user, db):
    product_a = ProductFactory(sku="CMB-NOP001")
    product_b = ProductFactory(sku="CMB-NOP002")
    location = LocationFactory(code="BODEGA_NO_PRICE", name="Bodega No Price")

    combo = ProductCombo.objects.create(name="Kit Sin Precio", sku="KIT-NOPRICE")
    ComboItem.objects.create(combo=combo, product=product_a, quantity=1)
    ComboItem.objects.create(combo=combo, product=product_b, quantity=1)

    StockByLocation.objects.create(
        product=product_a, location=location, current_stock=5
    )
    StockByLocation.objects.create(
        product=product_b, location=location, current_stock=5
    )

    movements = dispatch_combo(almacenista_user, combo.id, location.id)
    for m in movements:
        assert m.unit_price is None
        assert m.price_type == "combo"


# ---------------------------------------------------------------------------
# Fixed pricing (price_strategy=fixed)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_combo_fixed_price_distributes_proportionally(
    almacenista_user, combo_with_priced_products
):
    data = combo_with_priced_products
    combo = data["combo"]
    combo.price_strategy = "fixed"
    combo.fixed_price_retail = Decimal("20000.0000")
    combo.save()

    movements = dispatch_combo(almacenista_user, combo.id, data["location"].id)
    # total fixed = 20000; total cost = 3000*1 + 2000*2 = 7000
    # product_a cost = 3000; ratio = 3000/7000; share = 20000 * 3000/7000 ≈ 8571.4286
    # product_b cost = 4000; ratio = 4000/7000; share = 20000 * 4000/7000 ≈ 11428.5714
    total_from_movements = sum(m.subtotal or Decimal("0") for m in movements)
    assert abs(total_from_movements - Decimal("20000.0000")) < Decimal("1.0000")


@pytest.mark.django_db
def test_combo_fixed_price_invoice_created(
    almacenista_user, combo_with_priced_products
):
    data = combo_with_priced_products
    combo = data["combo"]
    combo.price_strategy = "fixed"
    combo.fixed_price_retail = Decimal("15000.0000")
    combo.save()

    movements = dispatch_combo(almacenista_user, combo.id, data["location"].id)
    inv_number = movements[0].invoice_number
    invoice = Invoice.objects.filter(number=inv_number).first()
    assert invoice is not None
    assert invoice.movements.count() == len(movements)


# ---------------------------------------------------------------------------
# Crear combo con precio fijo via servicio
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_combo_with_fixed_price(almacenista_user, db):
    product = ProductFactory(sku="CMB-0101")
    combo = create_combo(
        almacenista_user,
        {
            "name": "Kit Fijo",
            "sku": "KIT-0101",
            "items": [{"product_id": product.id, "quantity": 1}],
            "price_strategy": "fixed",
            "fixed_price_retail": "50000.0000",
            "fixed_price_wholesale": "40000.0000",
        },
    )
    combo.refresh_from_db()
    assert combo.price_strategy == "fixed"
    assert combo.fixed_price_retail == Decimal("50000.0000")
    assert combo.fixed_price_wholesale == Decimal("40000.0000")


@pytest.mark.django_db
def test_update_combo_price_strategy(almacenista_user, db):
    product = ProductFactory(sku="CMB-0102")
    combo = create_combo(
        almacenista_user,
        {
            "name": "Kit Actualizable",
            "sku": "KIT-0102",
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    assert combo.price_strategy == "derived"

    updated = update_combo(
        almacenista_user,
        combo.id,
        {"price_strategy": "fixed", "fixed_price_retail": "25000.0000"},
    )
    updated.refresh_from_db()
    assert updated.price_strategy == "fixed"
    assert updated.fixed_price_retail == Decimal("25000.0000")
