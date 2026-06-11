"""Tests de SLA a nivel de servicio.

Verifican que las operaciones críticas de dominio completan dentro de umbrales
de latencia aceptables usando SQLite en memoria.

Los umbrales son deliberadamente generosos (500 ms–2 s) para evitar falsos
negativos en entornos CI de distinto hardware; su valor es detectar
regresiones graves (N+1, full-table scans sin índice, blocking I/O accidental)
más que medir latencia de producción.

Para benchmarks de producción usar el locustfile con PostgreSQL.
"""

from __future__ import annotations

import time

import pytest

from apps.movements.services import register_entry
from tests.factories import LocationFactory, ProductFactory


SLA_SINGLE_ENTRY_MS = 500
SLA_LEDGER_NET_QTY_MS = 100
SLA_DASHBOARD_KPI_MS = 500
SLA_INVENTORY_SELECTOR_MS = 300


@pytest.mark.django_db
def test_register_entry_completes_within_sla(almacenista_user):
    """RF-005: registrar entrada de inventario debe completar en <500 ms."""
    product = ProductFactory()
    location = LocationFactory()

    start = time.perf_counter()
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        5,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < SLA_SINGLE_ENTRY_MS, (
        f"register_entry tardó {elapsed_ms:.1f}ms — supera SLA de {SLA_SINGLE_ENTRY_MS}ms"
    )


@pytest.mark.django_db
def test_ledger_net_qty_completes_within_sla(almacenista_user):
    """El cálculo del stock ledger (sin caché) debe completar en <100 ms."""
    from apps.movements.services import _ledger_net_qty

    product = ProductFactory()
    location = LocationFactory()
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    start = time.perf_counter()
    qty = _ledger_net_qty(product_id=product.id, location_id=location.id)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert qty == 10
    assert elapsed_ms < SLA_LEDGER_NET_QTY_MS, (
        f"_ledger_net_qty tardó {elapsed_ms:.1f}ms — supera SLA de {SLA_LEDGER_NET_QTY_MS}ms"
    )


@pytest.mark.django_db
def test_dashboard_kpis_completes_within_sla(db):
    """Dashboard KPI service debe completar en <500 ms sobre base vacía."""
    from django.core.cache import cache

    from apps.dashboard.services import build_dashboard_kpis

    cache.clear()

    start = time.perf_counter()
    build_dashboard_kpis()
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < SLA_DASHBOARD_KPI_MS, (
        f"build_dashboard_kpis tardó {elapsed_ms:.1f}ms — supera SLA de {SLA_DASHBOARD_KPI_MS}ms"
    )

    cache.clear()


@pytest.mark.django_db
def test_inventory_selector_completes_within_sla(sample_product, sample_locations):
    """El selector de inventario consolidado debe completar en <300 ms con datos mínimos."""
    from apps.inventory.selectors import get_full_inventory

    start = time.perf_counter()
    get_full_inventory()
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < SLA_INVENTORY_SELECTOR_MS, (
        f"get_full_inventory tardó {elapsed_ms:.1f}ms — supera SLA de {SLA_INVENTORY_SELECTOR_MS}ms"
    )
