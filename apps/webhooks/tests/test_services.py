"""Tests del servicio de webhooks (NEW-03)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint
from apps.webhooks.services import (
    _sign_payload,
    deliver_pending_webhooks,
    queue_webhook_event,
)
from tests.factories import AdministradorFactory


@pytest.fixture
def admin_user(db):
    return AdministradorFactory()


@pytest.fixture
def endpoint(db, admin_user):
    return WebhookEndpoint.objects.create(
        url="https://example.com/hook",
        secret="supersecretkey",
        events=["STOCK_CRITICO", "PROXIMO_VENCIMIENTO"],
        is_active=True,
        max_retries=3,
        created_by=admin_user,
    )


@pytest.fixture
def inactive_endpoint(db, admin_user):
    return WebhookEndpoint.objects.create(
        url="https://inactive.example.com/hook",
        secret="key",
        events=["STOCK_CRITICO"],
        is_active=False,
        max_retries=3,
        created_by=admin_user,
    )


# ── queue_webhook_event ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_queue_creates_delivery_for_subscribed_endpoint(endpoint):
    count = queue_webhook_event("STOCK_CRITICO", {"product_id": "abc"})
    assert count == 1
    assert WebhookDelivery.objects.filter(
        endpoint=endpoint, event_type="STOCK_CRITICO", status=WebhookDelivery.Status.PENDING
    ).exists()


@pytest.mark.django_db
def test_queue_skips_inactive_endpoints(inactive_endpoint):
    count = queue_webhook_event("STOCK_CRITICO", {"product_id": "abc"})
    assert count == 0


@pytest.mark.django_db
def test_queue_skips_unsubscribed_event(endpoint):
    count = queue_webhook_event("EVENTO_DESCONOCIDO", {})
    assert count == 0


@pytest.mark.django_db
def test_queue_creates_multiple_deliveries_for_multiple_endpoints(db, admin_user):
    WebhookEndpoint.objects.create(
        url="https://a.example.com/hook", secret="k1", events=["STOCK_CRITICO"],
        is_active=True, max_retries=3, created_by=admin_user,
    )
    WebhookEndpoint.objects.create(
        url="https://b.example.com/hook", secret="k2", events=["STOCK_CRITICO"],
        is_active=True, max_retries=3, created_by=admin_user,
    )
    count = queue_webhook_event("STOCK_CRITICO", {})
    assert count == 2
    assert WebhookDelivery.objects.count() == 2


# ── deliver_pending_webhooks ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_deliver_success(endpoint):
    queue_webhook_event("STOCK_CRITICO", {"test": True})

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.status = 200
    mock_response.read.return_value = b"OK"

    with patch("urllib.request.urlopen", return_value=mock_response):
        delivered, failed = deliver_pending_webhooks()

    assert delivered == 1
    assert failed == 0
    delivery = WebhookDelivery.objects.get(endpoint=endpoint)
    assert delivery.status == WebhookDelivery.Status.DELIVERED
    assert delivery.response_code == 200


@pytest.mark.django_db
def test_deliver_connection_error_schedules_retry(endpoint):
    """Error de conexión en el primer intento → delivery sigue PENDING con next_retry_at."""
    queue_webhook_event("STOCK_CRITICO", {})

    with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
        delivered, failed = deliver_pending_webhooks()

    # 1 intento fallido, pero max_retries=3 → aún PENDING con próximo retry
    delivery = WebhookDelivery.objects.get(endpoint=endpoint)
    assert delivery.attempts == 1
    assert delivery.status == WebhookDelivery.Status.PENDING
    assert delivery.next_retry_at is not None


@pytest.mark.django_db
def test_deliver_max_retries_marks_as_failed(endpoint):
    """Tras max_retries intentos fallidos, el delivery queda en FAILED permanente."""
    queue_webhook_event("STOCK_CRITICO", {})
    delivery = WebhookDelivery.objects.get(endpoint=endpoint)
    # Simular que ya se ha intentado max_retries - 1 veces
    delivery.attempts = endpoint.max_retries - 1
    delivery.save(update_fields=["attempts", "updated_at"])

    with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
        deliver_pending_webhooks()

    delivery.refresh_from_db()
    assert delivery.status == WebhookDelivery.Status.FAILED
    assert delivery.next_retry_at is None


# ── HMAC signature ────────────────────────────────────────────────────────────


def test_sign_payload_format():
    sig = _sign_payload("mysecret", b'{"test": true}')
    assert sig.startswith("sha256=")
    assert len(sig) == 71  # "sha256=" + 64 hex chars


def test_sign_payload_is_deterministic():
    body = b'{"event": "STOCK_CRITICO"}'
    assert _sign_payload("key1", body) == _sign_payload("key1", body)


def test_sign_payload_differs_with_different_key():
    body = b'{"event": "STOCK_CRITICO"}'
    assert _sign_payload("key1", body) != _sign_payload("key2", body)
