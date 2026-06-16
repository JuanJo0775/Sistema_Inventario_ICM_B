"""Tests de servicios de billing: create_multi_dispatch_invoice, void_invoice, stats."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.audit.models import AuditEventType, AuditLog
from apps.billing.services import (
    create_multi_dispatch_invoice,
    get_company_info,
    get_invoice_stats,
    update_company_info,
    void_invoice,
)
from apps.movements.models import Invoice, Movement, MovementType
from apps.movements.services import register_entry
from shared.exceptions import DomainValidationError
from tests.factories import ProductFactory


def _seed(user, product, location, qty):
    register_entry(user, product.id, location.id, qty)


# ---------------------------------------------------------------------------
# create_multi_dispatch_invoice
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_multi_dispatch_creates_single_invoice(almacenista_user, sample_locations):
    """Un solo número de factura agrupa todos los movements del carrito."""
    loc = sample_locations[1]
    p1 = ProductFactory(sale_price_retail=Decimal("10000"), tax_rate_pct=Decimal("0"))
    p2 = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p1, loc, 5)
    _seed(almacenista_user, p2, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Cliente Test"},
        items=[
            {"product_id": p1.id, "quantity": 2},
            {"product_id": p2.id, "quantity": 3},
        ],
    )

    assert invoice.pk is not None
    assert invoice.number.startswith("ICM-")
    assert invoice.invoice_type == "retail"
    assert invoice.movements.count() == 2  # un movement por producto


@pytest.mark.django_db
def test_multi_dispatch_totals_are_sum_of_all_items(almacenista_user, sample_locations):
    """Los totales del Invoice reflejan la suma de todos los items."""
    loc = sample_locations[1]
    p1 = ProductFactory(sale_price_retail=Decimal("10000"), tax_rate_pct=Decimal("0"))
    p2 = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("19"))
    _seed(almacenista_user, p1, loc, 5)
    _seed(almacenista_user, p2, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[
            {"product_id": p1.id, "quantity": 2},  # 20000
            {"product_id": p2.id, "quantity": 1},  # 5000 + 950 IVA = 5950
        ],
    )

    # subtotal = 20000 + 5000 = 25000; tax = 950; total = 25950
    assert invoice.subtotal == Decimal("25000.0000")
    assert invoice.tax_total == Decimal("950.0000")
    assert invoice.total_amount == Decimal("25950.0000")


@pytest.mark.django_db
def test_multi_dispatch_wholesale_requires_customer_data(
    almacenista_user, sample_locations
):
    """Wholesale exige datos completos del cliente y consentimiento de privacidad."""
    loc = sample_locations[1]
    p = ProductFactory(sale_price_wholesale=Decimal("8000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 10)

    from shared.exceptions import CrossValidationFailedError

    with pytest.raises(CrossValidationFailedError):
        create_multi_dispatch_invoice(
            almacenista_user,
            invoice_type="wholesale",
            location_id=loc.id,
            customer_data={"name": ""},  # datos incompletos
            items=[{"product_id": p.id, "quantity": 2}],
            privacy_notice_acknowledged=True,
        )


@pytest.mark.django_db
def test_multi_dispatch_invalid_type_raises(almacenista_user, sample_locations):
    with pytest.raises(DomainValidationError):
        create_multi_dispatch_invoice(
            almacenista_user,
            invoice_type="invalid",
            location_id=sample_locations[1].id,
            customer_data={"name": "Test"},
            items=[],
        )


@pytest.mark.django_db
def test_multi_dispatch_insufficient_stock_raises(almacenista_user, sample_locations):
    from shared.exceptions import InsufficientStockError

    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("100"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 1)

    with pytest.raises(InsufficientStockError):
        create_multi_dispatch_invoice(
            almacenista_user,
            invoice_type="retail",
            location_id=loc.id,
            customer_data={"name": "Test"},
            items=[{"product_id": p.id, "quantity": 999}],
        )


def _make_combo(product, quantity=1, sku="KIT-BILL-01"):
    """Crea un ProductCombo de un solo ítem para los tests del carrito mixto."""
    from apps.catalog.models import ComboItem, ProductCombo

    combo = ProductCombo.objects.create(name=f"Combo {sku}", sku=sku)
    ComboItem.objects.create(combo=combo, product=product, quantity=quantity)
    return combo


@pytest.mark.django_db
def test_multi_dispatch_mixes_combo_and_individual_product_in_one_invoice(
    almacenista_user, sample_locations
):
    """RF-006, RF-003 — Un combo y un producto individual caben en la misma factura."""
    loc = sample_locations[1]
    combo_component = ProductFactory(
        sale_price_retail=Decimal("3000"), tax_rate_pct=Decimal("0")
    )
    individual_product = ProductFactory(
        sale_price_retail=Decimal("7000"), tax_rate_pct=Decimal("0")
    )
    combo = _make_combo(combo_component, quantity=2)
    _seed(almacenista_user, combo_component, loc, 10)
    _seed(almacenista_user, individual_product, loc, 10)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Cliente Mixto"},
        items=[
            {"combo_id": combo.id, "quantity": 1},
            {"product_id": individual_product.id, "quantity": 1},
        ],
    )

    # 1 movement por el componente del combo + 1 movement del producto individual
    assert invoice.movements.count() == 2
    assert (
        invoice.movements.filter(movement_type=MovementType.SALIDA_COMBO).count() == 1
    )
    numbers = set(invoice.movements.values_list("invoice_number", flat=True))
    assert len(numbers) == 1
    assert numbers.pop() == invoice.number


@pytest.mark.django_db
def test_multi_dispatch_combo_quantity_dispatches_combo_multiple_times(
    almacenista_user, sample_locations
):
    """quantity=2 en un ítem combo despacha el combo completo dos veces."""
    loc = sample_locations[1]
    component = ProductFactory(sale_price_retail=Decimal("1000"))
    combo = _make_combo(component, quantity=1, sku="KIT-BILL-02")
    _seed(almacenista_user, component, loc, 10)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"combo_id": combo.id, "quantity": 2}],
    )

    assert invoice.movements.count() == 2  # 2 despachos del combo (1 ítem cada uno)


@pytest.mark.django_db
def test_multi_dispatch_unknown_combo_raises_does_not_exist(
    almacenista_user, sample_locations
):
    from uuid import uuid4

    from apps.catalog.models import ProductCombo

    with pytest.raises(ProductCombo.DoesNotExist):
        create_multi_dispatch_invoice(
            almacenista_user,
            invoice_type="retail",
            location_id=sample_locations[1].id,
            customer_data={"name": "Test"},
            items=[{"combo_id": uuid4(), "quantity": 1}],
        )


@pytest.mark.django_db
def test_void_invoice_with_mixed_combo_and_product_restores_all_stock(
    almacenista_user, sample_locations
):
    """Anular una factura mixta revierte el stock tanto del combo como del producto suelto."""
    from apps.inventory.models import StockByLocation

    loc = sample_locations[1]
    combo_component = ProductFactory(sale_price_retail=Decimal("3000"))
    individual_product = ProductFactory(sale_price_retail=Decimal("7000"))
    combo = _make_combo(combo_component, quantity=2, sku="KIT-BILL-03")
    _seed(almacenista_user, combo_component, loc, 10)
    _seed(almacenista_user, individual_product, loc, 10)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[
            {"combo_id": combo.id, "quantity": 1},
            {"product_id": individual_product.id, "quantity": 3},
        ],
    )

    void_invoice(invoice.pk, user=almacenista_user, reason="Anulación mixta")

    assert (
        StockByLocation.objects.get(product=combo_component, location=loc).current_stock
        == 10
    )
    assert (
        StockByLocation.objects.get(
            product=individual_product, location=loc
        ).current_stock
        == 10
    )


@pytest.mark.django_db
def test_multi_dispatch_each_item_shares_same_invoice_number(
    almacenista_user, sample_locations
):
    loc = sample_locations[1]
    p1 = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    p2 = ProductFactory(sale_price_retail=Decimal("2000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p1, loc, 5)
    _seed(almacenista_user, p2, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[
            {"product_id": p1.id, "quantity": 1},
            {"product_id": p2.id, "quantity": 1},
        ],
    )

    # Todos los movements tienen el mismo invoice_number
    numbers = set(invoice.movements.values_list("invoice_number", flat=True))
    assert len(numbers) == 1
    assert numbers.pop() == invoice.number


# ---------------------------------------------------------------------------
# void_invoice
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_void_invoice_marks_as_voided(almacenista_user, sample_locations):
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 10)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 3}],
    )

    result = void_invoice(invoice.pk, user=almacenista_user, reason="Error de despacho")

    result.refresh_from_db()
    assert result.is_voided is True
    assert result.void_reason == "Error de despacho"
    assert result.voided_by == almacenista_user
    assert result.voided_at is not None


@pytest.mark.django_db
def test_void_invoice_restores_stock(almacenista_user, sample_locations):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 10)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 4}],
    )

    stock_before_void = StockByLocation.objects.get(
        product=p, location=loc
    ).current_stock
    assert stock_before_void == 6  # 10 - 4

    void_invoice(invoice.pk, user=almacenista_user, reason="Prueba")

    stock_after_void = StockByLocation.objects.get(
        product=p, location=loc
    ).current_stock
    assert stock_after_void == 10  # restaurado


@pytest.mark.django_db
def test_void_invoice_creates_anulacion_movements(almacenista_user, sample_locations):
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("1000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 5)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 2}],
    )

    void_invoice(invoice.pk, user=almacenista_user, reason="Test void")

    anulacion_movements = Movement.objects.filter(
        movement_type=MovementType.ANULACION,
        invoice_number=invoice.number,
    )
    assert anulacion_movements.count() == 1


@pytest.mark.django_db
def test_void_invoice_twice_raises_409_conflict(almacenista_user, sample_locations):
    """Anular una factura ya anulada lanza InvoiceAlreadyVoidedError (409)."""
    from shared.exceptions import InvoiceAlreadyVoidedError

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
    void_invoice(invoice.pk, user=almacenista_user, reason="Primera vez")

    with pytest.raises(InvoiceAlreadyVoidedError):
        void_invoice(invoice.pk, user=almacenista_user, reason="Segunda vez")


@pytest.mark.django_db
def test_void_invoice_logs_audit(almacenista_user, sample_locations):
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
    void_invoice(invoice.pk, user=almacenista_user, reason="Audit test")

    assert AuditLog.objects.filter(
        event_type=AuditEventType.INVOICE_VOIDED,
        metadata__invoice_number=invoice.number,
    ).exists()


# ---------------------------------------------------------------------------
# get_invoice_stats
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_invoice_stats_today(almacenista_user, sample_locations):
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("10000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 10)

    create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 2}],
    )

    stats = get_invoice_stats()
    assert stats["invoice_count_today"] >= 1
    assert stats["total_sales_today"] >= Decimal("20000")


@pytest.mark.django_db
def test_invoice_stats_excludes_voided(almacenista_user, sample_locations):
    loc = sample_locations[1]
    p = ProductFactory(sale_price_retail=Decimal("5000"), tax_rate_pct=Decimal("0"))
    _seed(almacenista_user, p, loc, 10)

    invoice = create_multi_dispatch_invoice(
        almacenista_user,
        invoice_type="retail",
        location_id=loc.id,
        customer_data={"name": "Test"},
        items=[{"product_id": p.id, "quantity": 1}],
    )
    void_invoice(invoice.pk, user=almacenista_user, reason="Test")

    stats = get_invoice_stats()
    # La factura anulada no suma al total
    assert stats["invoice_count_today"] == 0


# ---------------------------------------------------------------------------
# CompanyInfo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_company_info_creates_default():
    info = get_company_info()
    assert info.pk == 1
    assert info.invoice_series == "ICM"


@pytest.mark.django_db
def test_update_company_info(almacenista_user):
    info = update_company_info(
        almacenista_user, {"nit": "900123456-1", "company_name": "ICM S.A.S"}
    )
    assert info.nit == "900123456-1"
    assert info.company_name == "ICM S.A.S"
    assert AuditLog.objects.filter(
        event_type=AuditEventType.COMPANY_INFO_UPDATED
    ).exists()
