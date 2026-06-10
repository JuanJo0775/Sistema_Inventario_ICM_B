from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from django.db import connections

from apps.inventory.models import StockByLocation
from apps.movements.models import MovementType
from apps.movements.services import register_dispatch, register_entry


@pytest.mark.django_db(transaction=True)
def test_concurrent_dispatches_does_not_produce_negative_stock(
    almacenista_user, sample_product, sample_locations
):
    """Simula despachos concurrentes y valida que no haya stock negativo.

    Esta prueba se salta en SQLite (no soporta `select_for_update` real)
    porque la semántica de bloqueo difiere. Para ejecutarla en CI, use
    Postgres (el workflow de CI incluye un job para ello).
    """
    from django.db import connection

    if connection.vendor == "sqlite":
        pytest.skip("SQLite no garantiza semántica de bloqueo; ejecutar en Postgres")

    loc = sample_locations[0]
    product = sample_product

    # crear stock inicial 10
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    results = []

    def worker(qty):
        # cerrar conexiones para forzar nueva conexión por hilo/proceso
        connections.close_all()
        with patch(
            "apps.movements.services.generate_invoice_number", return_value=None
        ):
            try:
                movements = register_dispatch(
                    almacenista_user,
                    product.id,
                    loc.id,
                    qty,
                    MovementType.SALIDA_VENTA_MENOR,
                    scanned_code=product.barcode,
                    order_sku=product.sku,
                    cold_chain_acknowledged=True,
                    electrical_safety_acknowledged=True,
                )
                results.append((True, sum(m.quantity for m in movements)))
            except Exception as e:
                results.append((False, e))

    # dos hilos que intentan despachar 7 cada uno (total pedido 14 > stock 10)
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut1 = ex.submit(worker, 7)
        # pequeña pausa para aumentar probabilidad de colisión
        time.sleep(0.05)
        fut2 = ex.submit(worker, 7)
        fut1.result()
        fut2.result()

    # recargar stock
    row = StockByLocation.objects.get(product=product, location=loc)
    assert row.current_stock >= 0

    # sum of successful dispatched quantities cannot exceed initial stock (10)
    total_dispatched = sum(v for ok, v in results if ok and isinstance(v, int))
    assert total_dispatched <= 10


@pytest.mark.skipif(
    os.environ.get("RUN_CONCURRENCY_TESTS") != "1",
    reason="Requires Postgres and RUN_CONCURRENCY_TESTS=1",
)
@pytest.mark.django_db(transaction=True)
def test_concurrent_movements_do_not_create_negative_stock(
    almacenista_user, sample_product, sample_locations
):
    """Simula entries y dispatches concurrentes para verificar que el stock nunca sea negativo."""
    from django.db import connection

    if connection.vendor == "sqlite":
        pytest.skip("SQLite no garantiza semántica de bloqueo; ejecutar en Postgres")

    loc = sample_locations[0]
    product = sample_product

    register_entry(almacenista_user, product.id, loc.id, 5)

    results = []

    def entry_worker():
        connections.close_all()
        try:
            register_entry(almacenista_user, product.id, loc.id, 2)
            results.append(("entry", True, 2))
        except Exception as e:
            results.append(("entry", False, e))

    def dispatch_worker():
        connections.close_all()
        with patch(
            "apps.movements.services.generate_invoice_number", return_value=None
        ):
            try:
                register_dispatch(
                    almacenista_user,
                    product.id,
                    loc.id,
                    3,
                    MovementType.SALIDA_VENTA_MENOR,
                    scanned_code=product.barcode,
                    order_sku=product.sku,
                )
                results.append(("dispatch", True, 3))
            except Exception as e:
                results.append(("dispatch", False, e))

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(entry_worker) for _ in range(3)]
        futures += [ex.submit(dispatch_worker) for _ in range(5)]
        for fut in futures:
            fut.result()

    row = StockByLocation.objects.get(product=product, location=loc)
    assert row.current_stock >= 0
