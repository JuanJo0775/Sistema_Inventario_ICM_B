"""Tests de endpoints REST del módulo de inventario."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditEventType, AuditLog


@pytest.mark.django_db
def test_inventory_full_list_returns_200(authenticated_almacenista_client):
    response = authenticated_almacenista_client.get("/api/v1/inventory/")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data


@pytest.mark.django_db
def test_inventory_search_returns_200(authenticated_almacenista_client, sample_product):
    response = authenticated_almacenista_client.get(
        "/api/v1/inventory/search/", {"q": sample_product.sku}
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_product_stock_returns_200(authenticated_almacenista_client, sample_product):
    response = authenticated_almacenista_client.get(
        f"/api/v1/inventory/products/{sample_product.id}/stock/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert "total" in response.data


@pytest.mark.django_db
def test_location_create_returns_201(authenticated_almacenista_client):
    response = authenticated_almacenista_client.post(
        "/api/v1/inventory/locations/",
        {"name": "Bodega Test Nueva"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Bodega Test Nueva"
    assert AuditLog.objects.filter(
        event_type=AuditEventType.LOCATION_CREATED,
    ).exists()


@pytest.mark.django_db
def test_location_state_transition_returns_200(
    authenticated_almacenista_client, sample_locations
):
    loc = sample_locations[0]
    response = authenticated_almacenista_client.post(
        f"/api/v1/inventory/locations/{loc.id}/state-transitions/",
        {"operational_status": "maintenance"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["operational_status"] == "maintenance"
    assert AuditLog.objects.filter(
        event_type=AuditEventType.LOCATION_MODIFIED,
        metadata___action="state_changed",
    ).exists()


@pytest.mark.django_db
def test_storage_type_create_returns_201(authenticated_almacenista_client):
    response = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {"code": "st-test-01", "name": "Tipo Test"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["code"] == "st-test-01"
    assert AuditLog.objects.filter(
        event_type=AuditEventType.STORAGE_TYPE_CREATED,
    ).exists()


@pytest.mark.django_db
def test_storage_type_update_logs_audit(authenticated_almacenista_client):
    create = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {"code": "st-test-02", "name": "Tipo Test 2"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    response = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/storage-types/{create.data['id']}/",
        {"name": "Tipo Test 2 actualizado"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert AuditLog.objects.filter(
        event_type=AuditEventType.STORAGE_TYPE_UPDATED,
    ).exists()


@pytest.mark.django_db
def test_storage_template_create_logs_audit(authenticated_almacenista_client):
    response = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-templates/",
        {"code": "tpl-test-01", "name": "Plantilla Test"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert AuditLog.objects.filter(
        event_type=AuditEventType.STORAGE_TEMPLATE_CREATED,
    ).exists()


@pytest.mark.django_db
def test_storage_template_update_logs_audit(authenticated_almacenista_client):
    create = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-templates/",
        {"code": "tpl-test-02", "name": "Plantilla Test 2"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    response = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/storage-templates/{create.data['id']}/",
        {"name": "Plantilla Test 2 actualizada"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert AuditLog.objects.filter(
        event_type=AuditEventType.STORAGE_TEMPLATE_UPDATED,
    ).exists()


@pytest.mark.django_db
def test_auxiliar_cannot_manage_locations(auxiliar_user):
    client = APIClient()
    client.force_authenticate(user=auxiliar_user)
    response = client.post(
        "/api/v1/inventory/locations/",
        {"name": "No permitida"},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
