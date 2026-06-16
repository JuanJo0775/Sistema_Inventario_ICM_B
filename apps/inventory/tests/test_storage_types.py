from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_storage_type_crud_and_location_binding(authenticated_almacenista_client):
    create_type = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {
            "code": "bodega-grande",
            "name": "Bodega grande",
            "category": "warehouse",
            "default_is_retail": False,
            "sort_order": 5,
        },
        format="json",
    )
    assert create_type.status_code == 201
    storage_type_id = create_type.data["id"]

    create_location = authenticated_almacenista_client.post(
        "/api/v1/inventory/locations/",
        {
            "name": "Bodega Norte",
            "description": "Espacio principal",
            "storage_type_id": storage_type_id,
        },
        format="json",
    )
    assert create_location.status_code == 201
    assert create_location.data["storage_type_id"] == storage_type_id
    assert create_location.data["storage_type_code"] == "bodega-grande"


@pytest.mark.django_db
def test_location_patch_can_assign_storage_type(
    authenticated_almacenista_client, sample_locations
):
    create_type = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {
            "code": "cuarto-frio-zona-a",
            "name": "Cuarto frío zona A",
            "category": "cold_chain",
            "default_is_retail": False,
        },
        format="json",
    )
    assert create_type.status_code == 201
    storage_type_id = create_type.data["id"]

    location = sample_locations[1]
    patch_resp = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/locations/{location.id}/",
        {"storage_type_id": storage_type_id},
        format="json",
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data["storage_type_id"] == storage_type_id
    assert patch_resp.data["storage_type_code"] == "cuarto-frio-zona-a"


@pytest.mark.django_db
def test_location_state_transition_endpoint(
    authenticated_almacenista_client, sample_locations
):
    location = sample_locations[0]

    response = authenticated_almacenista_client.post(
        f"/api/v1/inventory/locations/{location.id}/state-transitions/",
        {"operational_status": "maintenance"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["operational_status"] == "maintenance"
    assert response.data["is_active"] is True


@pytest.mark.django_db
def test_inactive_storage_type_rejected_on_create_location(
    authenticated_almacenista_client,
):
    """An inactive StorageType cannot be assigned to a new location."""
    create_type = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {"code": "tipo-inactivo", "name": "Tipo Inactivo"},
        format="json",
    )
    assert create_type.status_code == 201
    storage_type_id = create_type.data["id"]

    # deactivate it
    authenticated_almacenista_client.delete(
        f"/api/v1/inventory/storage-types/{storage_type_id}/"
    )

    create_location = authenticated_almacenista_client.post(
        "/api/v1/inventory/locations/",
        {"name": "Bodega Inactiva", "storage_type_id": storage_type_id},
        format="json",
    )
    assert create_location.status_code in (400, 422)


@pytest.mark.django_db
def test_inactive_storage_type_rejected_on_patch_location(
    authenticated_almacenista_client, sample_locations
):
    """An inactive StorageType cannot be assigned via PATCH."""
    create_type = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {"code": "tipo-inactivo-patch", "name": "Tipo Inactivo Patch"},
        format="json",
    )
    assert create_type.status_code == 201
    storage_type_id = create_type.data["id"]

    authenticated_almacenista_client.delete(
        f"/api/v1/inventory/storage-types/{storage_type_id}/"
    )

    location = sample_locations[0]
    patch_resp = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/locations/{location.id}/",
        {"storage_type_id": storage_type_id},
        format="json",
    )
    assert patch_resp.status_code in (400, 422)


@pytest.mark.django_db
def test_location_capacity_relative_fields_in_create_and_patch(
    authenticated_almacenista_client,
):
    create_location = authenticated_almacenista_client.post(
        "/api/v1/inventory/locations/",
        {
            "name": "Bodega Relativa",
            "capacity_mode": "relative_scale",
            "capacity_level": 3,
            "capacity_score": 30,
            "occupancy_estimate_pct": 45.5,
        },
        format="json",
    )
    assert create_location.status_code == 201
    assert create_location.data["capacity_mode"] == "relative_scale"
    assert create_location.data["capacity_level"] == 3
    assert create_location.data["capacity_score"] == 30

    patch_resp = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/locations/{create_location.data['id']}/",
        {"capacity_mode": "none", "capacity_level": None},
        format="json",
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data["capacity_mode"] == "none"
    assert patch_resp.data["capacity_level"] is None
