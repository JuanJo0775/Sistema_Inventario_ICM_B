"""Tests para el endpoint de polling de alertas (NEW-04)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.alerts.models import Alert, AlertSeverity, AlertType
from tests.factories import LocationFactory, ProductFactory


@pytest.fixture
def product_location(db):
    product = ProductFactory(sku="POLL-0001")
    location = LocationFactory(code="POLL-LOC-01", name="Bodega Poll")
    return product, location


def _create_alert(product, location, created_offset_seconds=0):
    alert = Alert.objects.create(
        product=product,
        location=location,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        message="Test alert",
    )
    if created_offset_seconds:
        Alert.objects.filter(pk=alert.pk).update(
            created_at=timezone.now() + timedelta(seconds=created_offset_seconds)
        )
        alert.refresh_from_db()
    return alert


@pytest.mark.django_db
def test_poll_returns_alerts_after_since(authenticated_almacenista_client, product_location):
    """Solo se retornan alertas creadas DESPUÉS de `since`."""
    product, location = product_location
    past_alert = _create_alert(product, location, created_offset_seconds=-120)
    since = timezone.now() - timedelta(seconds=60)
    new_alert = _create_alert(product, location, created_offset_seconds=0)

    # Usar request.get() con params para que el cliente DRF codifique correctamente el +
    response = authenticated_almacenista_client.get(
        reverse("alerts-poll"), {"since": since.isoformat()}
    )

    assert response.status_code == 200
    data = response.json()
    assert "server_timestamp" in data
    assert "results" in data
    result_ids = [r["id"] for r in data["results"]]
    assert new_alert.id in result_ids
    assert past_alert.id not in result_ids


@pytest.mark.django_db
def test_poll_without_since_defaults_24h(authenticated_almacenista_client, product_location):
    """Sin `since`, retorna las últimas 24 horas."""
    product, location = product_location
    recent_alert = _create_alert(product, location)

    url = reverse("alerts-poll")
    response = authenticated_almacenista_client.get(url)

    assert response.status_code == 200
    data = response.json()
    result_ids = [r["id"] for r in data["results"]]
    assert recent_alert.id in result_ids


@pytest.mark.django_db
def test_poll_includes_server_timestamp(authenticated_almacenista_client, db):
    """La respuesta siempre incluye `server_timestamp`."""
    url = reverse("alerts-poll")
    response = authenticated_almacenista_client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "server_timestamp" in data
    assert data["server_timestamp"]  # no vacío


@pytest.mark.django_db
def test_poll_severity_filter(authenticated_almacenista_client, product_location):
    """El filtro `?severity=CRITICAL` solo retorna alertas de esa severidad."""
    product, location = product_location
    high_alert = Alert.objects.create(
        product=product, location=location,
        alert_type=AlertType.LOW_STOCK, severity=AlertSeverity.HIGH,
        message="Alto",
    )
    critical_alert = Alert.objects.create(
        product=product, location=location,
        alert_type=AlertType.STOCK_ZERO, severity=AlertSeverity.CRITICAL,
        message="Crítico",
    )

    response = authenticated_almacenista_client.get(
        reverse("alerts-poll"), {"severity": "CRITICAL"}
    )

    assert response.status_code == 200
    result_ids = [r["id"] for r in response.json()["results"]]
    assert critical_alert.id in result_ids
    assert high_alert.id not in result_ids


@pytest.mark.django_db
def test_poll_invalid_since_returns_400(authenticated_almacenista_client, db):
    """?since con formato inválido → 400."""
    url = reverse("alerts-poll") + "?since=not-a-date"
    response = authenticated_almacenista_client.get(url)
    assert response.status_code == 400
