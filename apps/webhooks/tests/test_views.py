"""Tests de la API de webhooks (NEW-03)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint
from tests.factories import AdministradorFactory


@pytest.fixture
def admin_client(api_client, db):
    user = AdministradorFactory()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def endpoint(db):
    admin = AdministradorFactory()
    return WebhookEndpoint.objects.create(
        url="https://example.com/hook",
        secret="supersecretkey12345",
        events=["STOCK_CRITICO"],
        is_active=True,
        max_retries=3,
        created_by=admin,
    )


# ── CRUD endpoints ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_create_endpoint(admin_client):
    url = reverse("webhooks-endpoints")
    response = admin_client.post(
        url,
        data={
            "url": "https://hook.example.com/events",
            "secret": "mysecret123",
            "events": ["STOCK_CRITICO", "PROXIMO_VENCIMIENTO"],
        },
        format="json",
    )
    assert response.status_code == 201
    assert WebhookEndpoint.objects.filter(url="https://hook.example.com/events").exists()


@pytest.mark.django_db
def test_list_endpoints(admin_client, endpoint):
    url = reverse("webhooks-endpoints")
    response = admin_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_delete_endpoint_deactivates_it(admin_client, endpoint):
    url = reverse("webhooks-endpoint-detail", kwargs={"pk": str(endpoint.id)})
    response = admin_client.delete(url)
    assert response.status_code == 204
    endpoint.refresh_from_db()
    assert not endpoint.is_active


@pytest.mark.django_db
def test_create_endpoint_requires_admin(authenticated_almacenista_client):
    url = reverse("webhooks-endpoints")
    response = authenticated_almacenista_client.post(
        url,
        data={"url": "https://example.com", "secret": "key", "events": ["STOCK_CRITICO"]},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_stats_view(admin_client, endpoint):
    url = reverse("webhooks-stats")
    response = admin_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "delivered" in data
    assert "failed" in data
    assert "active_endpoints" in data


@pytest.mark.django_db
def test_deliveries_list(admin_client, endpoint):
    WebhookDelivery.objects.create(
        endpoint=endpoint,
        event_type="STOCK_CRITICO",
        payload={"test": True},
        status=WebhookDelivery.Status.DELIVERED,
    )
    url = reverse("webhooks-deliveries")
    response = admin_client.get(url)
    assert response.status_code == 200
