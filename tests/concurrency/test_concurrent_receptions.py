"""Tests de concurrencia para el módulo de compras.

Verifica que el mecanismo select_for_update en confirm_reception impide
que la misma recepción sea confirmada dos veces simultáneamente, lo que
duplicaría el stock de entrada.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connections

from apps.purchasing.exceptions import ReceptionNotInBorradorError
from apps.purchasing.models import PurchaseOrderStatus, ReceptionStatus
from apps.purchasing.services import (
    confirm_purchase_order,
    confirm_reception,
    create_purchase_order,
    create_reception,
    create_supplier,
)


@pytest.mark.skipif(
    os.environ.get("RUN_CONCURRENCY_TESTS") != "1",
    reason="Requires Postgres and RUN_CONCURRENCY_TESTS=1",
)
@pytest.mark.django_db(transaction=True)
def test_concurrent_reception_confirmation_does_not_duplicate_stock(
    almacenista_user, sample_product, sample_locations
):
    """Dos hilos intentan confirmar la misma recepción simultáneamente.

    Solo uno debe tener éxito; el segundo debe recibir ReceptionNotInBorradorError
    porque la recepción ya transicionó a CONFIRMADA. El stock resultante debe
    reflejar solo una confirmación (no duplicado).
    """
    from django.db import connection

    if connection.vendor == "sqlite":
        pytest.skip("SQLite no garantiza semántica de bloqueo; ejecutar en Postgres")

    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    product = sample_product

    # Setup: crear y confirmar OC con 10 unidades
    supplier = create_supplier(
        almacenista_user,
        {
            "nombre_comercial": "Proveedor Concurrencia",
            "nit": "999000000-9",
        },
    )
    po = create_purchase_order(
        almacenista_user,
        {
            "supplier_id": supplier.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity_ordered": 10,
                    "unit_cost": "5000.00",
                }
            ],
        },
    )
    po = confirm_purchase_order(almacenista_user, po.id)
    assert po.status == PurchaseOrderStatus.PENDIENTE

    # Crear recepción BORRADOR para 10 unidades
    poi = po.items.first()
    reception = create_reception(
        almacenista_user,
        po.id,
        {
            "destination_location_id": loc.id,
            "items": [
                {
                    "purchase_order_item_id": poi.id,
                    "quantity_received": 10,
                }
            ],
        },
    )
    assert reception.status == ReceptionStatus.BORRADOR

    results = []

    def worker():
        connections.close_all()
        try:
            confirm_reception(almacenista_user, reception.id)
            results.append(("ok", None))
        except ReceptionNotInBorradorError as exc:
            results.append(("not_borrador", exc))
        except Exception as exc:
            results.append(("error", exc))

    # Dos hilos intentan confirmar la misma recepción
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(worker), ex.submit(worker)]
        for fut in futures:
            fut.result()

    successes = [r for r in results if r[0] == "ok"]
    not_borrador = [r for r in results if r[0] == "not_borrador"]
    errors = [r for r in results if r[0] == "error"]

    assert not errors, f"Errores inesperados: {errors}"
    assert len(successes) == 1, f"Solo una confirmación debe tener éxito; resultados: {results}"
    assert len(not_borrador) == 1, "El segundo hilo debe recibir ReceptionNotInBorradorError"

    # Stock final debe reflejar solo una confirmación
    stock_row = StockByLocation.objects.get(product=product, location=loc)
    assert stock_row.current_stock == 10
