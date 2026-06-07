"""Implementaciones Gherkin — RF013 (Precios y facturación comercial)."""

from __future__ import annotations


# --- RF-013 (Precios y Facturación Comercial — BR-16, BR-17) -----------------


def impl_rf013_s01(almacenista_user, sample_locations, db):
    """S01: Despacho captura precio congelado al momento de la salida."""
    from decimal import Decimal

    from apps.movements.models import Invoice, MovementType
    from apps.movements.services import register_dispatch, register_entry
    from tests.factories import ProductFactory

    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("19.00"),
        currency="COP",
    )
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 10)

    movements = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        3,
        MovementType.SALIDA_VENTA_MENOR,
    )
    m = movements[0]
    assert m.unit_price == Decimal("10000.0000")
    assert m.subtotal == Decimal("30000.0000")
    assert m.tax_amount == Decimal("5700.0000")
    assert m.total_amount == Decimal("35700.0000")
    assert m.price_type == "retail"
    assert m.currency == "COP"

    invoice = Invoice.objects.filter(number=m.invoice_number).first()
    assert invoice is not None
    assert invoice.total_amount == Decimal("35700.0000")


def impl_rf013_s02(almacenista_user, sample_locations, db):
    """S02: Precio permanece inmutable tras modificar el precio del producto."""
    from decimal import Decimal

    from apps.catalog.services import update_product_prices
    from apps.movements.models import MovementType
    from apps.movements.services import register_dispatch, register_entry
    from tests.factories import ProductFactory

    product = ProductFactory(
        sale_price_retail=Decimal("10000.0000"),
        tax_rate_pct=Decimal("0.00"),
    )
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 5)
    movements = register_dispatch(
        almacenista_user, product.id, loc.id, 1, MovementType.SALIDA_VENTA_MENOR
    )
    m = movements[0]
    original_price = m.unit_price

    update_product_prices(
        almacenista_user, product.id, sale_price_retail=Decimal("20000.0000")
    )

    m.refresh_from_db()
    assert m.unit_price == original_price
    assert m.unit_price == Decimal("10000.0000")


def impl_rf013_s03(almacenista_user, auxiliar_user, db):
    """S03: Actualización de precio genera historial auditado."""
    from decimal import Decimal

    import pytest
    from apps.catalog.models import ProductPriceHistory
    from apps.catalog.services import update_product_prices
    from shared.exceptions import UnauthorizedCredentialManagementError
    from tests.factories import ProductFactory

    product = ProductFactory(sale_price_retail=Decimal("10000.0000"))

    update_product_prices(
        almacenista_user, product.id, sale_price_retail=Decimal("12000.0000")
    )
    entry = ProductPriceHistory.objects.get(
        product=product, field_changed="sale_price_retail"
    )
    assert entry.old_value == Decimal("10000.0000")
    assert entry.new_value == Decimal("12000.0000")
    assert entry.changed_by == almacenista_user

    update_product_prices(
        almacenista_user, product.id, sale_price_retail=Decimal("12000.0000")
    )
    assert ProductPriceHistory.objects.filter(product=product).count() == 1

    with pytest.raises(UnauthorizedCredentialManagementError):
        update_product_prices(
            auxiliar_user, product.id, sale_price_retail=Decimal("5000.0000")
        )


def impl_rf013_s04(almacenista_user, sample_locations, db):
    """S04: Factura reconstruible sin consultar el catálogo actual."""
    from decimal import Decimal

    from apps.movements.models import Invoice, MovementType
    from apps.movements.services import register_dispatch, register_entry
    from tests.factories import ProductFactory

    product = ProductFactory(
        sale_price_wholesale=Decimal("9000.0000"),
        tax_rate_pct=Decimal("19.00"),
    )
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 10)

    customer = {
        "customer_name": "Distribuidora RF013",
        "customer_email": "rf013@dist.com",
        "customer_phone": "3001234567",
        "customer_address": "Calle 10 # 5-20",
        "privacy_notice_acknowledged": True,
    }
    movements = register_dispatch(
        almacenista_user,
        product.id,
        loc.id,
        2,
        MovementType.SALIDA_VENTA_MAYOR,
        customer_data=customer,
    )
    m = movements[0]
    assert m.customer_snapshot["customer_name"] == "Distribuidora RF013"
    assert m.total_amount is not None

    invoice = Invoice.objects.get(number=m.invoice_number)
    assert invoice.customer_name == "Distribuidora RF013"
    assert invoice.total_amount == m.total_amount

    product.is_active = False
    product.save(update_fields=["is_active"])

    invoice.refresh_from_db()
    assert invoice.total_amount is not None
    assert invoice.customer_name == "Distribuidora RF013"


IMPLEMENTATIONS: dict[str, object] = {
    "RF013-S01": impl_rf013_s01,
    "RF013-S02": impl_rf013_s02,
    "RF013-S03": impl_rf013_s03,
    "RF013-S04": impl_rf013_s04,
}
