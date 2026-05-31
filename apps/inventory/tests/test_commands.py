"""Tests para management commands de inventory."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from apps.inventory.models import StockByLocation
from apps.movements.services import register_entry
from tests.factories import LocationFactory, ProductFactory


@pytest.fixture
def stock_setup(db, almacenista_user):
    product = ProductFactory(sku="INT-0001")
    location = LocationFactory(code="INT-LOC-01", name="Bodega Integridad")
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    stock = StockByLocation.objects.get(product=product, location=location)
    return {"product": product, "location": location, "stock": stock}


@pytest.mark.django_db
def test_verify_integrity_no_divergence(stock_setup):
    """Sin divergencias: ledger y caché alineados → command reporta OK."""
    out = StringIO()
    call_command("verify_stock_integrity", stdout=out)
    output = out.getvalue()
    assert "OK" in output


@pytest.mark.django_db
def test_verify_integrity_detects_divergence(stock_setup):
    """Con divergencia: command la detecta y reporta correctamente."""
    stock = stock_setup["stock"]
    # Corromper la caché directamente (bypass ORM-safe)
    StockByLocation.objects.filter(pk=stock.pk).update(current_stock=9999)

    err = StringIO()
    out = StringIO()
    call_command("verify_stock_integrity", stdout=out, stderr=err)
    error_output = err.getvalue()
    assert "DIVERGENCIA" in error_output or "divergencia" in error_output.lower()


@pytest.mark.django_db
def test_verify_integrity_fix_flag(stock_setup):
    """Con --fix: command corrige la divergencia y el caché queda en el valor del ledger."""
    stock = stock_setup["stock"]
    StockByLocation.objects.filter(pk=stock.pk).update(current_stock=9999)

    out = StringIO()
    call_command("verify_stock_integrity", "--fix", stdout=out)

    stock.refresh_from_db()
    assert stock.current_stock == 10  # valor correcto según ledger


@pytest.mark.django_db
def test_verify_integrity_empty_stock(db):
    """Sin movimientos ni caché → 0 divergencias."""
    out = StringIO()
    call_command("verify_stock_integrity", stdout=out)
    assert "OK" in out.getvalue()


@pytest.mark.django_db
def test_verify_integrity_no_fix_without_flag(stock_setup):
    """Sin --fix: divergencias detectadas pero caché NO se modifica."""
    stock = stock_setup["stock"]
    StockByLocation.objects.filter(pk=stock.pk).update(current_stock=9999)

    out = StringIO()
    call_command("verify_stock_integrity", stdout=out)

    stock.refresh_from_db()
    assert stock.current_stock == 9999  # sin --fix, la caché no se toca
