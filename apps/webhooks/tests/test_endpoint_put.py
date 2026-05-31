"""Tests para el nuevo método PUT en webhook endpoints."""

from __future__ import annotations

import pytest


VALID_EVENTS = ["movement.created", "alert.triggered"]
VALID_SECRET = "s3cr3t-seguro"  # mínimo 8 caracteres


def _create_endpoint(client, url="https://example.com/hook", events=None):
    return client.post(
        "/api/v1/webhooks/endpoints/",
        {
            "url": url,
            "secret": VALID_SECRET,
            "events": events or VALID_EVENTS,
            "max_retries": 3,
        },
        format="json",
    )


class TestWebhookEndpointPut:
    @pytest.mark.django_db
    def test_put_replaces_endpoint(self, authenticated_almacenista_client):
        create_resp = _create_endpoint(authenticated_almacenista_client)
        assert create_resp.status_code == 201
        endpoint_id = create_resp.data["id"]

        put_resp = authenticated_almacenista_client.put(
            f"/api/v1/webhooks/endpoints/{endpoint_id}/",
            {
                "url": "https://nuevo.example.com/hook",
                "secret": "nuevo-secreto",
                "events": ["alert.triggered"],
                "max_retries": 5,
            },
            format="json",
        )
        assert put_resp.status_code == 200
        assert put_resp.data["url"] == "https://nuevo.example.com/hook"
        assert put_resp.data["events"] == ["alert.triggered"]
        assert put_resp.data["max_retries"] == 5

    @pytest.mark.django_db
    def test_put_requires_all_fields(self, authenticated_almacenista_client):
        create_resp = _create_endpoint(authenticated_almacenista_client)
        assert create_resp.status_code == 201
        endpoint_id = create_resp.data["id"]

        # PUT sin url ni events (campos requeridos ausentes)
        put_resp = authenticated_almacenista_client.put(
            f"/api/v1/webhooks/endpoints/{endpoint_id}/",
            {"secret": VALID_SECRET},
            format="json",
        )
        assert put_resp.status_code == 400

    @pytest.mark.django_db
    def test_put_requires_almacenista(self, authenticated_administrador_client):
        import uuid
        put_resp = authenticated_administrador_client.put(
            f"/api/v1/webhooks/endpoints/{uuid.uuid4()}/",
            {"url": "https://x.com", "secret": VALID_SECRET, "events": VALID_EVENTS},
            format="json",
        )
        assert put_resp.status_code == 403

    @pytest.mark.django_db
    def test_put_404_on_nonexistent(self, authenticated_almacenista_client):
        import uuid
        put_resp = authenticated_almacenista_client.put(
            f"/api/v1/webhooks/endpoints/{uuid.uuid4()}/",
            {
                "url": "https://example.com/hook",
                "secret": VALID_SECRET,
                "events": VALID_EVENTS,
            },
            format="json",
        )
        assert put_resp.status_code == 404

    @pytest.mark.django_db
    def test_patch_still_works_independently(self, authenticated_almacenista_client):
        create_resp = _create_endpoint(authenticated_almacenista_client)
        assert create_resp.status_code == 201
        endpoint_id = create_resp.data["id"]

        patch_resp = authenticated_almacenista_client.patch(
            f"/api/v1/webhooks/endpoints/{endpoint_id}/",
            {"max_retries": 10},
            format="json",
        )
        assert patch_resp.status_code == 200
        assert patch_resp.data["max_retries"] == 10
        # URL original no se alteró
        assert patch_resp.data["url"] == "https://example.com/hook"
