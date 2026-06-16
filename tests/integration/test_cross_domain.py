"""Tests de integración multi-dominio.

Verifican que los flujos que atraviesan varios módulos mantienen
consistencia end-to-end: movimientos → stock → alertas → auditoría → reportes.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.alerts.models import Alert, AlertType
from apps.alerts.services import sync_stock_alerts_for_product
from apps.audit.models import AuditEventType, AuditLog
from apps.inventory.models import StockByLocation
from apps.movements.models import MovementType
from apps.movements.services import register_entry


@pytest.mark.django_db(transaction=True)
def test_entry_creates_movement_and_audit_log(
    almacenista_user, sample_product, sample_locations
):
    """Una entrada crea ledger inmutable y evento de auditoría MOVEMENT_CREATED."""
    loc = sample_locations[0]
    movement = register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        5,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    log = AuditLog.objects.filter(
        event_type=AuditEventType.MOVEMENT_CREATED,
        movement=movement,
    ).first()
    assert log is not None, "Debe existir un AuditLog MOVEMENT_CREATED para la entrada"
    assert log.user == almacenista_user


@pytest.mark.django_db(transaction=True)
def test_entry_then_stock_alert_resolved_when_above_reorder_point(
    almacenista_user, sample_locations
):
    """Registrar una entrada suficiente resuelve la alerta de stock bajo."""
    from tests.factories import ProductFactory

    product = ProductFactory(reorder_point=5)
    loc = sample_locations[0]

    # Alerta global preexistente de stock bajo (sin location, como las crea el servicio)
    Alert.objects.create(
        alert_type=AlertType.LOW_STOCK,
        product=product,
        location=None,
        message="Stock bajo",
        is_resolved=False,
    )
    assert Alert.objects.filter(product=product, is_resolved=False).count() == 1

    # Entrada que lleva el stock por encima del reorder_point
    register_entry(
        almacenista_user,
        product.id,
        loc.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    sync_stock_alerts_for_product(product.id)

    assert (
        Alert.objects.filter(
            product=product, alert_type=AlertType.LOW_STOCK, is_resolved=False
        ).count()
        == 0
    ), "La alerta LOW_STOCK debe resolverse al superar el reorder_point"


@pytest.mark.django_db(transaction=True)
def test_dispatch_reflected_in_reports_kpi(
    authenticated_almacenista_client,
    almacenista_user,
    sample_product,
    sample_locations,
):
    """Un despacho registrado aparece en los KPI de reports el mismo día."""
    from apps.movements.services import register_dispatch

    loc = sample_locations[0]
    register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    with patch("apps.movements.services.generate_invoice_number", return_value="F-001"):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            3,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=sample_product.barcode,
            order_sku=sample_product.sku,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )

    r = authenticated_almacenista_client.get(reverse("reports-kpi"))
    assert r.status_code == 200
    assert r.data["movements_today"] >= 1


@pytest.mark.django_db(transaction=True)
def test_entry_stock_visible_in_inventory_api(
    authenticated_almacenista_client,
    almacenista_user,
    sample_product,
    sample_locations,
):
    """El stock de una entrada es inmediatamente consultable vía la API de inventario."""
    loc = sample_locations[0]
    register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        7,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    r = authenticated_almacenista_client.get(reverse("inventory-full"))
    assert r.status_code == 200
    skus = [item["sku"] for item in r.data.get("results", r.data)]
    assert sample_product.sku in skus


@pytest.mark.django_db(transaction=True)
def test_dispatch_reduces_stock_and_entry_audit_log_exists(
    almacenista_user, sample_product, sample_locations
):
    """Un despacho reduce StockByLocation; la entrada previa tiene AuditLog MOVEMENT_CREATED."""
    from apps.movements.services import register_dispatch

    loc = sample_locations[0]
    entry = register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    # La entrada debe haber generado un AuditLog inmutable
    entry_log = AuditLog.objects.filter(
        event_type=AuditEventType.MOVEMENT_CREATED,
        movement=entry,
    ).first()
    assert entry_log is not None, "La entrada debe tener AuditLog MOVEMENT_CREATED"

    with patch(
        "apps.movements.services.generate_invoice_number", return_value="F-INT-001"
    ):
        register_dispatch(
            almacenista_user,
            sample_product.id,
            loc.id,
            4,
            MovementType.SALIDA_VENTA_MENOR,
            scanned_code=sample_product.barcode,
            order_sku=sample_product.sku,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )

    row = StockByLocation.objects.get(product=sample_product, location=loc)
    assert row.current_stock == 6


@pytest.mark.django_db(transaction=True)
def test_internal_transfer_preserves_global_stock_and_updates_locations(
    almacenista_user, sample_product, sample_locations
):
    """Un traslado interno mueve stock entre ubicaciones sin cambiar el total global."""
    from apps.movements.services import register_internal_transfer

    origin = sample_locations[0]
    destination = sample_locations[1]

    register_entry(
        almacenista_user,
        sample_product.id,
        origin.id,
        10,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    register_internal_transfer(
        almacenista_user,
        sample_product.id,
        origin.id,
        destination.id,
        4,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    origin_stock = StockByLocation.objects.get(
        product=sample_product, location=origin
    ).current_stock
    dest_stock = StockByLocation.objects.get(
        product=sample_product, location=destination
    ).current_stock

    assert origin_stock == 6
    assert dest_stock == 4
    assert origin_stock + dest_stock == 10
