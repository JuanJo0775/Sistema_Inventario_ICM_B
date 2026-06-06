"""Tests de endpoints REST del módulo de compras."""

from __future__ import annotations

import pytest

from apps.purchasing.models import PurchaseOrderStatus, ReceptionStatus
from tests.factories import LocationFactory, ProductFactory

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
def test_deactivate_supplier(authenticated_almacenista_client):
    supplier = SupplierFactory(is_active=True)
    response = authenticated_almacenista_client.post(
        f"/api/v1/purchasing/suppliers/{supplier.id}/deactivate/"
    )
    assert response.status_code == 200
    assert response.data["is_active"] is False


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
def test_confirm_reception_endpoint(authenticated_almacenista_client, almacenista_user):
    po = PurchaseOrderFactory(status=PurchaseOrderStatus.PENDIENTE)
    product = ProductFactory()
    poi = PurchaseOrderItemFactory(
        purchase_order=po, product=product, quantity_ordered=5
    )
    location = LocationFactory(name="Bodega Endpoint", code="bodega-endpoint")
    reception = ReceptionFactory(
        purchase_order=po, destination_location=location, received_by=almacenista_user
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
