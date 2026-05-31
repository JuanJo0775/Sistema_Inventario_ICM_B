"""Tests de integración para el endpoint POST /api/v1/movements/combo-dispatch/ (RF-003)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.audit.models import AuditEventType, AuditLog
from apps.catalog.models import ComboItem, ProductCombo
from apps.inventory.models import StockByLocation
from apps.movements.models import Movement, MovementType
from shared.exceptions import InsufficientStockError
from tests.factories import LocationFactory, ProductFactory


@pytest.fixture
def combo_setup(db, almacenista_user):
    """Crea combo de 2 productos con stock suficiente en una ubicación."""
    product_a = ProductFactory(sku="CMB-0001")
    product_b = ProductFactory(sku="CMB-0002")
    location = LocationFactory(code="BODEGA_COMBO", name="Bodega Combo")

    combo = ProductCombo.objects.create(name="Kit de prueba", sku="KIT-001")
    ComboItem.objects.create(combo=combo, product=product_a, quantity=2)
    ComboItem.objects.create(combo=combo, product=product_b, quantity=3)

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


@pytest.mark.django_db
def test_dispatch_combo_success(authenticated_almacenista_client, combo_setup):
    """POST combo-dispatch con stock suficiente → 201 + stock reducido en ambos productos."""
    combo = combo_setup["combo"]
    location = combo_setup["location"]

    url = reverse("movements-combo-dispatch")
    response = authenticated_almacenista_client.post(
        url,
        data={"combo_id": str(combo.id), "location_id": str(location.id)},
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    # Se generan 2 movimientos (uno por cada ítem del combo)
    assert len(data) == 2
    assert all(m["movement_type"] == MovementType.SALIDA_COMBO for m in data)

    # Stock reducido correctamente
    stock_a = StockByLocation.objects.get(
        product=combo_setup["product_a"], location=location
    ).current_stock
    stock_b = StockByLocation.objects.get(
        product=combo_setup["product_b"], location=location
    ).current_stock
    assert stock_a == 8  # 10 - 2
    assert stock_b == 7  # 10 - 3


@pytest.mark.django_db
def test_dispatch_combo_insufficient_stock(
    authenticated_almacenista_client, combo_setup
):
    """POST combo-dispatch sin stock suficiente → 409."""
    combo = combo_setup["combo"]
    location = combo_setup["location"]

    # Vaciar stock del primer producto
    StockByLocation.objects.filter(
        product=combo_setup["product_a"], location=location
    ).update(current_stock=0)

    url = reverse("movements-combo-dispatch")
    response = authenticated_almacenista_client.post(
        url,
        data={"combo_id": str(combo.id), "location_id": str(location.id)},
        format="json",
    )

    assert response.status_code == 409


@pytest.mark.django_db
def test_dispatch_combo_creates_audit_log(
    authenticated_almacenista_client, combo_setup
):
    """POST combo-dispatch exitoso → AuditLog con tipo MOVEMENT_CREATED."""
    combo = combo_setup["combo"]
    location = combo_setup["location"]

    before_count = AuditLog.objects.filter(
        event_type=AuditEventType.MOVEMENT_CREATED
    ).count()

    url = reverse("movements-combo-dispatch")
    authenticated_almacenista_client.post(
        url,
        data={"combo_id": str(combo.id), "location_id": str(location.id)},
        format="json",
    )

    after_count = AuditLog.objects.filter(
        event_type=AuditEventType.MOVEMENT_CREATED
    ).count()
    assert after_count > before_count


@pytest.mark.django_db
def test_dispatch_combo_inactive_combo_returns_404(
    authenticated_almacenista_client, combo_setup
):
    """POST combo-dispatch con combo inactivo → 404."""
    combo = combo_setup["combo"]
    combo.is_active = False
    combo.save(update_fields=["is_active", "updated_at"])

    url = reverse("movements-combo-dispatch")
    response = authenticated_almacenista_client.post(
        url,
        data={
            "combo_id": str(combo.id),
            "location_id": str(combo_setup["location"].id),
        },
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_dispatch_combo_requires_authentication(api_client, combo_setup):
    """POST combo-dispatch sin autenticación → 401."""
    combo = combo_setup["combo"]
    url = reverse("movements-combo-dispatch")
    response = api_client.post(
        url,
        data={
            "combo_id": str(combo.id),
            "location_id": str(combo_setup["location"].id),
        },
        format="json",
    )
    assert response.status_code == 401
