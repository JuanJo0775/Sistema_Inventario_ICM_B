"""Tests de endpoints REST del módulo de compras."""

from __future__ import annotations

import pytest

from apps.purchasing.models import PurchaseOrderStatus, ReceptionStatus
from tests.factories import ElectroCategoryFactory, LocationFactory, ProductFactory

from .factories import (
    PurchaseOrderFactory,
    PurchaseOrderItemFactory,
    ReceptionFactory,
    ReceptionItemFactory,
    SupplierFactory,
)

# ---------------------------------------------------------------------------
# Supplier endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_suppliers_authenticated_almacenista(authenticated_almacenista_client):
    SupplierFactory.create_batch(3)
    response = authenticated_almacenista_client.get("/api/v1/purchasing/suppliers/")
    assert response.status_code == 200
    assert response.data["count"] >= 3


@pytest.mark.django_db
def test_create_supplier_almacenista(authenticated_almacenista_client):
    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/suppliers/",
        {
            "nombre_comercial": "Proveedor Test",
            "razon_social": "Proveedor Test S.A.S.",
            "nit": "800000001-1",
            "pais": "Colombia",
            "correo": "test@proveedor.com",
            "telefono": "3001234567",
            "ciudad": "Bogotá",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["nit"] == "800000001-1"


@pytest.mark.django_db
def test_create_supplier_forbidden_auxiliar(api_client, auxiliar_user):
    api_client.force_authenticate(user=auxiliar_user)
    response = api_client.post(
        "/api/v1/purchasing/suppliers/",
        {"nombre_comercial": "X", "nit": "1"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_supplier_forbidden_administrador(authenticated_administrador_client):
    response = authenticated_administrador_client.post(
        "/api/v1/purchasing/suppliers/",
        {"nombre_comercial": "X", "nit": "2"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_supplier_without_nit(authenticated_almacenista_client):
    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/suppliers/",
        {"nombre_comercial": "Importadora Internacional", "pais": "México"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["nit"] is None


@pytest.mark.django_db
def test_patch_supplier_without_nit_preserves_existing(
    authenticated_almacenista_client,
):
    supplier = SupplierFactory(nit="900000002-2")
    response = authenticated_almacenista_client.patch(
        f"/api/v1/purchasing/suppliers/{supplier.id}/",
        {"ciudad": "Medellín"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["nit"] == "900000002-2"


@pytest.mark.django_db
def test_patch_supplier_with_empty_nit_clears_value(authenticated_almacenista_client):
    supplier = SupplierFactory(nit="900000003-3")
    response = authenticated_almacenista_client.patch(
        f"/api/v1/purchasing/suppliers/{supplier.id}/",
        {"nit": ""},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["nit"] is None


@pytest.mark.django_db
def test_deactivate_supplier(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)
    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/suppliers/{supplier.id}/deactivate/"
    )
    assert response.status_code == 200
    assert response.data["is_active"] is False


@pytest.mark.django_db
def test_supplier_soft_delete_returns_204(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)
    response = authenticated_almacenista_client.delete(
        f"/api/v1/purchasing/suppliers/{supplier.id}/"
    )
    assert response.status_code == 204
    supplier.refresh_from_db()
    assert supplier.deleted_at is not None
    assert supplier.is_active is False


@pytest.mark.django_db
def test_supplier_restore_after_soft_delete(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)
    authenticated_almacenista_client.delete(
        f"/api/v1/purchasing/suppliers/{supplier.id}/"
    )
    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/suppliers/{supplier.id}/restore/"
    )
    assert response.status_code == 200
    assert response.data["is_active"] is True
    assert response.data["deleted_at"] is None


@pytest.mark.django_db
def test_supplier_disable_enable_cycle(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)

    # disable
    r_disable = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/suppliers/{supplier.id}/disable/"
    )
    assert r_disable.status_code == 200
    assert r_disable.data["is_active"] is False
    assert r_disable.data["deleted_at"] is None  # no archivado

    # enable
    r_enable = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/suppliers/{supplier.id}/enable/"
    )
    assert r_enable.status_code == 200
    assert r_enable.data["is_active"] is True
    assert r_enable.data["deleted_at"] is None


@pytest.mark.django_db
def test_supplier_response_includes_deleted_at(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)
    response = authenticated_almacenista_client.get(
        f"/api/v1/purchasing/suppliers/{supplier.id}/"
    )
    assert response.status_code == 200
    assert "deleted_at" in response.data
    assert response.data["deleted_at"] is None


@pytest.mark.django_db
def test_supplier_enable_blocked_when_archived(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)
    authenticated_almacenista_client.delete(
        f"/api/v1/purchasing/suppliers/{supplier.id}/"
    )
    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/suppliers/{supplier.id}/enable/"
    )
    # enable en proveedor archivado debe fallar (usar /restore/ en su lugar)
    assert response.status_code in (400, 409)


# ---------------------------------------------------------------------------
# PurchaseOrder endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_purchase_order(authenticated_almacenista_client, almacenista_user):
    supplier = SupplierFactory()
    product = ProductFactory()
    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/purchase-orders/",
        {
            "supplier_id": str(supplier.id),
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity_ordered": 10,
                    "unit_cost": "5000.00",
                }
            ],
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "borrador"
    assert response.data["number"].startswith("OC-")


@pytest.mark.django_db
def test_confirm_purchase_order(authenticated_almacenista_client, almacenista_user):
    po = PurchaseOrderFactory(created_by=almacenista_user)
    PurchaseOrderItemFactory(purchase_order=po)
    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/purchase-orders/{po.id}/confirm/"
    )
    assert response.status_code == 200
    assert response.data["status"] == "pendiente"


@pytest.mark.django_db
def test_cancel_purchase_order(authenticated_almacenista_client, almacenista_user):
    po = PurchaseOrderFactory(created_by=almacenista_user)
    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/purchase-orders/{po.id}/cancel/",
        {"reason": "No se requiere la mercancía"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == "cancelada"


# ---------------------------------------------------------------------------
# Reception endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_reception(authenticated_almacenista_client, almacenista_user):
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    location = LocationFactory(name="Bodega API", code="bodega-api")

    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/receptions/",
        {
            "po_id": str(po.id),
            "destination_location_id": str(location.id),
            "items": [
                {
                    "purchase_order_item_id": str(poi.id),
                    "quantity_received": 5,
                }
            ],
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "borrador"


@pytest.mark.django_db
def test_create_reception_with_allocations(
    authenticated_almacenista_client, almacenista_user
):
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    b1 = LocationFactory(name="Bodega 1", code="bodega-1-api")
    vit = LocationFactory(name="Vitrina", code="vitrina-api")

    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/receptions/",
        {
            "po_id": str(po.id),
            "destination_location_id": str(vit.id),
            "items": [
                {
                    "purchase_order_item_id": str(poi.id),
                    "quantity_received": 10,
                    "allocations": [
                        {
                            "location_id": str(b1.id),
                            "quantity_received": 4,
                        },
                        {
                            "location_id": str(vit.id),
                            "quantity_received": 6,
                        },
                    ],
                }
            ],
        },
        format="json",
    )
    assert response.status_code == 201
    assert len(response.data["items"][0]["allocations"]) == 2
    assert {
        str(allocation["location"])
        for allocation in response.data["items"][0]["allocations"]
    } == {str(b1.id), str(vit.id)}
    assert response.data["has_allocations"] is True


@pytest.mark.django_db
def test_confirm_reception_endpoint(authenticated_almacenista_client, almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=5
    )
    location = LocationFactory(name="Bodega Endpoint", code="bodega-endpoint")
    reception = ReceptionFactory(
        purchase_order=po,
        destination_location=location,
        received_by=almacenista_user,
    )
    ReceptionItemFactory(
        reception=reception, purchase_order_item=poi, quantity_received=5
    )

    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/receptions/{reception.id}/confirm/"
    )
    assert response.status_code == 200
    assert response.data["status"] == "confirmada"


@pytest.mark.django_db
def test_list_receptions_administrador_can_view(
    authenticated_administrador_client,
):
    ReceptionFactory.create_batch(2)
    response = authenticated_administrador_client.get("/api/v1/purchasing/receptions/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_confirm_reception_forbidden_administrador(
    authenticated_administrador_client,
):
    reception = ReceptionFactory()
    response = authenticated_administrador_client.post(
        f"/api/v1/purchasing/receptions/{reception.id}/confirm/"
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Reception + serial_number (BR-04) — view-layer integration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_reception_with_serial_number(
    authenticated_almacenista_client, almacenista_user
):
    """Crea recepción vía endpoint con serial_number y verifica que se persista."""
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat)
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    location = LocationFactory(name="Bodega Test", code="bodega-test")

    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/receptions/",
        {
            "po_id": str(po.id),
            "destination_location_id": str(location.id),
            "items": [
                {
                    "purchase_order_item_id": str(poi.id),
                    "quantity_received": 5,
                    "serial_number": "SN-TEST-001",
                }
            ],
        },
        format="json",
    )
    assert response.status_code == 201
    item = response.data["items"][0]
    assert item["serial_number"] == "SN-TEST-001"
    assert item["quantity_received"] == 5


@pytest.mark.django_db
def test_create_reception_with_allocations_and_serial(
    authenticated_almacenista_client, almacenista_user
):
    """Crea recepción con allocations y serial_number en item y allocation."""
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat)
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    b1 = LocationFactory(name="Bodega 1", code="bodega-1-test")
    v1 = LocationFactory(name="Vitrina", code="vitrina-test")

    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/receptions/",
        {
            "po_id": str(po.id),
            "destination_location_id": str(b1.id),
            "items": [
                {
                    "purchase_order_item_id": str(poi.id),
                    "quantity_received": 6,
                    "serial_number": "SN-TEST-ALLOC-001",
                    "allocations": [
                        {
                            "location_id": str(b1.id),
                            "quantity_received": 2,
                            "serial_number": "SN-ALLOC-001",
                        },
                        {
                            "location_id": str(v1.id),
                            "quantity_received": 4,
                            "serial_number": "SN-ALLOC-002",
                        },
                    ],
                }
            ],
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["has_allocations"] is True
    # Item-level serial
    assert response.data["items"][0]["serial_number"] == "SN-TEST-ALLOC-001"
    # Allocation-level serials
    allocs = response.data["items"][0]["allocations"]
    assert len(allocs) == 2
    serials = {a["serial_number"] for a in allocs}
    assert serials == {"SN-ALLOC-001", "SN-ALLOC-002"}


@pytest.mark.django_db
def test_create_and_confirm_reception_with_serial(
    authenticated_almacenista_client, almacenista_user
):
    """
    Flujo completo: crea recepción con serial vía endpoint,
    luego la confirma — debe crear el movimiento de entrada sin error.
    """
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat)
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=5
    )
    location = LocationFactory(
        name="Bodega Confirm", code="bodega-confirm", operational_status="active"
    )

    # Crear recepción
    create_resp = authenticated_almacenista_client.post(
        "/api/v1/purchasing/receptions/",
        {
            "po_id": str(po.id),
            "destination_location_id": str(location.id),
            "items": [
                {
                    "purchase_order_item_id": str(poi.id),
                    "quantity_received": 5,
                    "serial_number": "SN-CONFIRM-001",
                }
            ],
        },
        format="json",
    )
    assert create_resp.status_code == 201
    reception_id = create_resp.data["id"]

    # Confirmar recepción
    confirm_resp = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/receptions/{reception_id}/confirm/",
        {
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.data["status"] == "confirmada"


@pytest.mark.django_db
def test_create_reception_with_serial_ignored_when_not_required(
    authenticated_almacenista_client, almacenista_user
):
    """Serial opcional se ignora si la categoría no lo exige."""
    po = PurchaseOrderFactory(
        created_by=almacenista_user, status=PurchaseOrderStatus.PENDIENTE
    )
    product = ProductFactory()  # ManoCategoryFactory — requires_serial_number=False
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=10
    )
    location = LocationFactory(name="Bodega Normal", code="bodega-normal")

    response = authenticated_almacenista_client.post(
        "/api/v1/purchasing/receptions/",
        {
            "po_id": str(po.id),
            "destination_location_id": str(location.id),
            "items": [
                {
                    "purchase_order_item_id": str(poi.id),
                    "quantity_received": 3,
                    "serial_number": "SN-OPTIONAL-001",
                }
            ],
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["items"][0]["serial_number"] == "SN-OPTIONAL-001"
