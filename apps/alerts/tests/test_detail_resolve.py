"""Tests para detalle y resolución de alertas (RF-011)."""

from __future__ import annotations

import pytest
from rest_framework import status

from apps.alerts.models import Alert, AlertCategory, AlertSeverity, AlertType
from tests.factories import ProductFactory


@pytest.mark.django_db
def test_alert_detail_with_int_pk(authenticated_almacenista_client):
    product = ProductFactory()
    alert = Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="test",
    )
    assert isinstance(alert.id, int)
    resp = authenticated_almacenista_client.get(f"/api/v1/alerts/{alert.id}/")
    assert resp.status_code == status.HTTP_200_OK, (
        f"Alert detail returned {resp.status_code} for pk={alert.id}"
    )
    assert resp.data["id"] == alert.id


@pytest.mark.django_db
def test_alert_resolve_with_int_pk(authenticated_almacenista_client):
    product = ProductFactory()
    alert = Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="test",
    )
    resp = authenticated_almacenista_client.post(f"/api/v1/alerts/{alert.id}/resolve/")
    assert resp.status_code == status.HTTP_200_OK, (
        f"Alert resolve returned {resp.status_code} for pk={alert.id}"
    )
    assert resp.data["is_resolved"] is True


@pytest.mark.django_db
def test_alert_detail_404_for_nonexistent(authenticated_almacenista_client):
    resp = authenticated_almacenista_client.get("/api/v1/alerts/99999/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_alert_resolve_404_for_nonexistent(authenticated_almacenista_client):
    resp = authenticated_almacenista_client.post("/api/v1/alerts/99999/resolve/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
