"""Tests de concurrencia para traslados internos simultáneos.

Verifica que select_for_update en register_internal_transfer impide
stock negativo en origen cuando múltiples hilos trasladan de la misma ubicación.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connections

from apps.inventory.models import StockByLocation
from apps.movements.services import register_entry, register_internal_transfer
from shared.exceptions import InsufficientStockError


@pytest.mark.skipif(
    os.environ.get("RUN_CONCURRENCY_TESTS") != "1",
    reason="Requires Postgres and RUN_CONCURRENCY_TESTS=1",
)
@pytest.mark.django_db(transaction=True)
def test_concurrent_transfers_do_not_produce_negative_stock_at_origin(
    almacenista_user, sample_product, sample_locations
):
    """Dos hilos trasladan 7 unidades cada uno desde un origen con 10 unidades.

    Solo uno debe completarse; el otro debe recibir InsufficientStockError.
    El stock en el origen nunca debe ser negativo.
    """
    from django.db import connection

    if connection.vendor == "sqlite":
        pytest.skip("SQLite no garantiza semántica de bloqueo; ejecutar en Postgres")

    origin = sample_locations[0]
    destination = sample_locations[1]
    product = sample_product

    # Stock inicial: 10 unidades en origen
    register_entry(
        almacenista_user,
        product.id,
        origin.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    results = []

    def worker():
        connections.close_all()
        try:
            register_internal_transfer(
                almacenista_user,
                product.id,
                origin.id,
                destination.id,
                7,
                cold_chain_acknowledged=True,
                electrical_safety_acknowledged=True,
            )
            results.append(("ok", 7))
        except InsufficientStockError as exc:
            results.append(("insufficient", exc))
        except Exception as exc:
            results.append(("error", exc))

    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(worker), ex.submit(worker)]
        for fut in futures:
            fut.result()

    errors = [r for r in results if r[0] == "error"]
    assert not errors, f"Errores inesperados: {errors}"

    successes = [r for r in results if r[0] == "ok"]
    insufficient = [r for r in results if r[0] == "insufficient"]
    assert len(successes) == 1, "Solo un traslado debe completarse"
    assert len(insufficient) == 1, "El segundo debe recibir InsufficientStockError"

    # Stock en origen no debe ser negativo
    origin_row = StockByLocation.objects.get(product=product, location=origin)
    assert origin_row.current_stock >= 0

    # Stock total global se conserva (traslado no cambia el total)
    dest_row, _ = StockByLocation.objects.get_or_create(
        product=product, location=destination, defaults={"current_stock": 0}
    )
    assert origin_row.current_stock + dest_row.current_stock == 10
