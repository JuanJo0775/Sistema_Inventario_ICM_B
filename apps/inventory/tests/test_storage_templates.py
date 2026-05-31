from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_storage_template_crud_and_location_defaults(
    authenticated_almacenista_client,
):
    create_type = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {
            "code": "zona-fria",
            "name": "Zona fría",
            "category": "cold_chain",
        },
        format="json",
    )
    assert create_type.status_code == 201

    create_template = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-templates/",
        {
            "code": "frio-base",
            "name": "Plantilla frío base",
            "storage_type_id": create_type.data["id"],
            "defaults": {
                "is_retail": False,
                "max_capacity": 40,
                "capacity_mode": "relative_scale",
                "capacity_level": 2,
                "capacity_score": 80,
            },
        },
        format="json",
    )
    assert create_template.status_code == 201
    template_id = create_template.data["id"]

    create_location = authenticated_almacenista_client.post(
        "/api/v1/inventory/locations/",
        {
            "name": "Frío Norte",
            "storage_template_id": template_id,
        },
        format="json",
    )
    assert create_location.status_code == 201
    assert create_location.data["storage_template_id"] == template_id
    assert create_location.data["storage_type_id"] == create_type.data["id"]
    assert create_location.data["max_capacity"] == 40
    assert create_location.data["capacity_mode"] == "relative_scale"
    assert create_location.data["capacity_level"] == 2
    assert create_location.data["capacity_score"] == 80

    patch_template = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/storage-templates/{template_id}/",
        {"name": "Plantilla frío base v2"},
        format="json",
    )
    assert patch_template.status_code == 200
    assert patch_template.data["name"] == "Plantilla frío base v2"

    delete_template = authenticated_almacenista_client.delete(
        f"/api/v1/inventory/storage-templates/{template_id}/"
    )
    assert delete_template.status_code == 204

    detail_after_delete = authenticated_almacenista_client.get(
        f"/api/v1/inventory/storage-templates/{template_id}/"
    )
    assert detail_after_delete.status_code == 200
    assert detail_after_delete.data["is_active"] is False


@pytest.mark.django_db
def test_location_patch_can_assign_storage_template(
    authenticated_almacenista_client, sample_locations
):
    create_type = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-types/",
        {
            "code": "bodega-plantilla",
            "name": "Bodega plantilla",
            "category": "warehouse",
        },
        format="json",
    )
    assert create_type.status_code == 201

    create_template = authenticated_almacenista_client.post(
        "/api/v1/inventory/storage-templates/",
        {
            "code": "template-bodega-1",
            "name": "Template Bodega 1",
            "storage_type_id": create_type.data["id"],
        },
        format="json",
    )
    assert create_template.status_code == 201

    location = sample_locations[0]
    patch_location = authenticated_almacenista_client.patch(
        f"/api/v1/inventory/locations/{location.id}/",
        {"storage_template_id": create_template.data["id"]},
        format="json",
    )
    assert patch_location.status_code == 200
    assert patch_location.data["storage_template_id"] == create_template.data["id"]
    assert patch_location.data["storage_type_id"] == create_type.data["id"]
