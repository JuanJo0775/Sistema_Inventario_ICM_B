from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.inventory.models import StockByLocation
from apps.movements.models import MovementType
from apps.movements.services import register_dispatch, register_entry


@pytest.mark.django_db(transaction=True)
def test_integration_fefo_multi_lot(almacenista_user, sample_locations):
    """Prueba de integración transaccional: FEFO multi-lote.

    Crea dos lotes y entradas, luego realiza un despacho que debe consumir
    el lote con vencimiento más temprano primero y mantener las invariantes
    de stock (no negativo).
    """
    from tests.factories import ElectroCategoryFactory, LotFactory, ProductFactory

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, requires_expiration=True)
    loc = sample_locations[0]

    lot_early = LotFactory(
        product=product,
        code="INT-L-early",
        expiration_date=timezone.now().date() + timedelta(days=7),
    )
    lot_late = LotFactory(
        product=product,
        code="INT-L-late",
        expiration_date=timezone.now().date() + timedelta(days=60),
    )

    # entradas
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        6,
        lot_code=lot_late.code,
        lot_expiration_date=lot_late.expiration_date,
        serial_number="INT-SN-LATE",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        5,
        lot_code=lot_early.code,
        lot_expiration_date=lot_early.expiration_date,
        serial_number="INT-SN-EARLY",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    # dispatch que requiere consumir ambos lotes (total 9)
    with patch("apps.movements.services.generate_invoice_number", return_value=None):
        movements = register_dispatch(
            almacenista_user,
            product.id,
            loc.id,
            9,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=product.barcode,
            order_sku=product.sku,
            serial_number="INT-SN-DSP",
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )

    assert isinstance(movements, list)
    # primero debe consumir el lote con vencimiento más cercano
    assert movements[0].lot_id == lot_early.id

    # stock resultante no debe ser negativo
    row = StockByLocation.objects.get(product=product, location=loc)
    assert row.current_stock >= 0
