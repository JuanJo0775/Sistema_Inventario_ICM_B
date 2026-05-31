"""Tests para los nuevos endpoints de inventario: PUT en storage-templates y filtro include_inactive en locations."""

from __future__ import annotations

import pytest

from apps.inventory.models import Location, StorageTemplate, StorageType

# ===========================================================================
# Storage Templates — PUT (reemplazo completo)
# ===========================================================================


class TestStorageTemplatePut:
    @pytest.fixture
    def storage_type_id(self, authenticated_almacenista_client):
        resp = authenticated_almacenista_client.post(
            "/api/v1/inventory/storage-types/",
            {"code": "tipo-base", "name": "Tipo Base"},
            format="json",
        )
        assert resp.status_code == 201
        return resp.data["id"]

    @pytest.fixture
    def template_id(self, authenticated_almacenista_client):
        resp = authenticated_almacenista_client.post(
            "/api/v1/inventory/storage-templates/",
            {"code": "tpl-test", "name": "Plantilla Test", "sort_order": 1},
            format="json",
        )
        assert resp.status_code == 201
        return resp.data["id"]

    @pytest.mark.django_db
    def test_put_replaces_template(self, authenticated_almacenista_client, template_id):
        resp = authenticated_almacenista_client.put(
            f"/api/v1/inventory/storage-templates/{template_id}/",
            {
                "code": "tpl-test",
                "name": "Plantilla Reemplazada",
                "description": "Nueva descripción",
                "sort_order": 2,
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Plantilla Reemplazada"
        assert resp.data["description"] == "Nueva descripción"
        assert resp.data["sort_order"] == 2

    @pytest.mark.django_db
    def test_put_requires_almacenista(self, administrador_user):
        import uuid

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=administrador_user)
        resp = client.put(
            f"/api/v1/inventory/storage-templates/{uuid.uuid4()}/",
            {"code": "tpl-test", "name": "X"},
            format="json",
        )
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_put_404_on_nonexistent(self, almacenista_user):
        import uuid

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=almacenista_user)
        resp = client.put(
            f"/api/v1/inventory/storage-templates/{uuid.uuid4()}/",
            {"code": "tpl-nonexistent", "name": "No existe"},
            format="json",
        )
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_patch_still_works_after_put_added(
        self, authenticated_almacenista_client, template_id
    ):
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/inventory/storage-templates/{template_id}/",
            {"description": "Solo descripción"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["description"] == "Solo descripción"


# ===========================================================================
# Locations list — filtro include_inactive
# ===========================================================================


class TestLocationListIncludeInactive:
    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(
        self, authenticated_almacenista_client, sample_locations
    ):
        active_loc = sample_locations[0]
        # Desactivar una ubicación
        resp_del = authenticated_almacenista_client.delete(
            f"/api/v1/inventory/locations/{sample_locations[1].id}/"
        )
        assert resp_del.status_code == 204

        resp = authenticated_almacenista_client.get("/api/v1/inventory/locations/")
        assert resp.status_code == 200
        ids = [loc["id"] for loc in resp.data]
        assert str(active_loc.id) in ids
        assert str(sample_locations[1].id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(
        self, authenticated_almacenista_client, sample_locations
    ):
        inactive_loc = sample_locations[2]
        authenticated_almacenista_client.delete(
            f"/api/v1/inventory/locations/{inactive_loc.id}/"
        )

        resp = authenticated_almacenista_client.get(
            "/api/v1/inventory/locations/?include_inactive=true"
        )
        assert resp.status_code == 200
        ids = [loc["id"] for loc in resp.data]
        assert str(inactive_loc.id) in ids

    @pytest.mark.django_db
    def test_active_locations_always_visible(
        self, authenticated_almacenista_client, sample_locations
    ):
        resp = authenticated_almacenista_client.get("/api/v1/inventory/locations/")
        assert resp.status_code == 200
        ids = [loc["id"] for loc in resp.data]
        for loc in sample_locations:
            assert str(loc.id) in ids
