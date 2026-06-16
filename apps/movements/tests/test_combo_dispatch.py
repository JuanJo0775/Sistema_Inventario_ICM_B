"""Tests de integración para el endpoint POST /api/v1/movements/combo-dispatch/ (RF-003)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditEventType, AuditLog
from apps.catalog.models import ComboItem, ProductCombo, ProductSerial
from apps.inventory.models import StockByLocation
from apps.movements.models import Movement, MovementType
from shared.exceptions import InsufficientStockError
from tests.factories import (
    ElectroCategoryFactory,
    LocationFactory,
    ProductFactory,
    ProductSerialFactory,
)


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
def test_dispatch_combo_deleted_combo_returns_404(
    authenticated_almacenista_client, combo_setup
):
    """POST combo-dispatch con combo eliminado (soft delete) → 404."""
    combo = combo_setup["combo"]
    combo.deleted_at = timezone.now()
    combo.save(update_fields=["deleted_at", "updated_at"])

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


# ── BR-04: Serial en Combo Dispatch ───────────────────────────────────────────


@pytest.mark.django_db
def test_dispatch_combo_electro_without_serial_fails(almacenista_user):
    """Combo con producto Electroterapia sin serial → InsufficientStockError."""
    from apps.catalog.models import ComboItem, ProductCombo

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="CMB-ELEC-01")
    location = LocationFactory(code="BODEGA_CMB_ELEC")
    combo = ProductCombo.objects.create(name="Kit Electro", sku="KIT-ELEC")
    ComboItem.objects.create(combo=combo, product=product, quantity=1)
    StockByLocation.objects.create(product=product, location=location, current_stock=5)

    from apps.movements.services import dispatch_combo

    with pytest.raises(InsufficientStockError):
        dispatch_combo(
            almacenista_user,
            combo.id,
            location.id,
            serial_id=None,
        )


@pytest.mark.django_db
def test_dispatch_combo_electro_with_serial_succeeds(almacenista_user):
    """Combo con producto Electroterapia con serial → success."""
    from apps.catalog.models import ComboItem, ProductCombo

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="CMB-ELEC-02")
    location = LocationFactory(code="BODEGA_CMB_ELEC2")
    combo = ProductCombo.objects.create(name="Kit Electro 2", sku="KIT-ELEC2")
    ComboItem.objects.create(combo=combo, product=product, quantity=2)
    StockByLocation.objects.create(product=product, location=location, current_stock=10)

    serial = ProductSerialFactory(
        product=product,
        serial_number="SN-COMBO-01",
        current_location=location,
        status=ProductSerial.Status.AVAILABLE,
    )

    from apps.movements.services import dispatch_combo

    movements = dispatch_combo(
        almacenista_user,
        combo.id,
        location.id,
        serial_id=serial.id,
    )
    assert len(movements) == 1
    assert movements[0].serial_number == "SN-COMBO-01"


@pytest.mark.django_db
def test_dispatch_combo_with_mixed_products_serial_not_required(
    almacenista_user,
):
    """Combo con productos que NO requieren serial — debe funcionar sin serial."""
    from apps.catalog.models import ComboItem, ProductCombo

    product_a = ProductFactory(sku="CMB-MIX-A")
    product_b = ProductFactory(sku="CMB-MIX-B")
    location = LocationFactory(code="BODEGA_CMB_MIX")
    combo = ProductCombo.objects.create(name="Kit Mixto", sku="KIT-MIX")
    ComboItem.objects.create(combo=combo, product=product_a, quantity=1)
    ComboItem.objects.create(combo=combo, product=product_b, quantity=2)
    StockByLocation.objects.create(
        product=product_a, location=location, current_stock=5
    )
    StockByLocation.objects.create(
        product=product_b, location=location, current_stock=5
    )

    from apps.movements.services import dispatch_combo

    movements = dispatch_combo(
        almacenista_user,
        combo.id,
        location.id,
        serial_id=None,
    )
    assert len(movements) == 2
    assert all(m.serial_number is None for m in movements)


@pytest.mark.django_db
def test_dispatch_combo_with_external_invoice_number_skips_own_invoice(
    almacenista_user,
):
    """
    RF-003, BR-13 — Con external_invoice_number + skip_invoice_creation=True,
    el combo no genera su propio Invoice; el llamador (carrito multi-ítem) es
    responsable de consolidarlo con create_invoice_from_movements.
    """
    from apps.catalog.models import ComboItem, ProductCombo
    from apps.movements.models import Invoice
    from apps.movements.services import dispatch_combo

    product = ProductFactory(sku="CMB-EXT-01")
    location = LocationFactory(code="BODEGA_CMB_EXT")
    combo = ProductCombo.objects.create(name="Kit Externo", sku="KIT-EXT")
    ComboItem.objects.create(combo=combo, product=product, quantity=1)
    StockByLocation.objects.create(product=product, location=location, current_stock=5)

    movements = dispatch_combo(
        almacenista_user,
        combo.id,
        location.id,
        external_invoice_number="ICM-9999",
        skip_invoice_creation=True,
    )

    assert len(movements) == 1
    assert movements[0].invoice_number == "ICM-9999"
    assert not Invoice.objects.filter(number="ICM-9999").exists()
