from __future__ import annotations

import pytest

from apps.alerts.models import Alert, AlertCategory, AlertSeverity, AlertType
from apps.alerts.views import (
    AlertDetailView,
    AlertHistoryView,
    AlertListView,
    AlertResolveView,
    AlertStatsView,
)
from tests.factories import ProductFactory


def test_alerts_views_are_available():
    assert AlertListView is not None
    assert AlertDetailView is not None
    assert AlertResolveView is not None
    assert AlertHistoryView is not None
    assert AlertStatsView is not None


@pytest.mark.django_db
def test_alert_list_returns_active_alerts(authenticated_almacenista_client):
    product = ProductFactory()
    Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="test",
    )
    resp = authenticated_almacenista_client.get("/api/v1/alerts/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    result = data["results"][0]
    assert "severity" in result
    assert "category" in result


@pytest.mark.django_db
def test_alert_list_filter_by_severity(authenticated_almacenista_client):
    product = ProductFactory()
    Alert.objects.create(
        product=product,
        alert_type=AlertType.EXPIRATION_30,
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.EXPIRATION,
        message="c",
    )
    Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.MEDIUM,
        category=AlertCategory.STOCK,
        message="m",
    )

    resp = authenticated_almacenista_client.get("/api/v1/alerts/?severity=CRITICAL")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert all(r["severity"] == "CRITICAL" for r in results)


@pytest.mark.django_db
def test_alert_list_filter_by_category(authenticated_almacenista_client):
    product = ProductFactory()
    Alert.objects.create(
        product=product,
        alert_type=AlertType.EXPIRATION_30,
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.EXPIRATION,
        message="e",
    )
    Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="s",
    )

    resp = authenticated_almacenista_client.get("/api/v1/alerts/?category=EXPIRATION")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert all(r["category"] == "EXPIRATION" for r in results)


@pytest.mark.django_db
def test_alert_stats_endpoint(authenticated_almacenista_client):
    product = ProductFactory()
    Alert.objects.create(
        product=product,
        alert_type=AlertType.EXPIRATION_30,
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.EXPIRATION,
        message="x",
    )
    Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="y",
    )

    resp = authenticated_almacenista_client.get("/api/v1/alerts/stats/")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_active" in data
    assert "by_severity" in data
    assert "by_category" in data
    assert data["total_active"] >= 2
    assert data["by_severity"].get("CRITICAL", 0) >= 1
    assert data["by_category"].get("EXPIRATION", 0) >= 1


@pytest.mark.django_db
def test_alert_history_endpoint(authenticated_almacenista_client, almacenista_user):
    from django.utils import timezone

    product = ProductFactory()
    alert = Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="resolved",
        is_resolved=True,
        resolved_at=timezone.now(),
        resolved_by=almacenista_user,
    )

    resp = authenticated_almacenista_client.get("/api/v1/alerts/history/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    ids = [r["id"] for r in data["results"]]
    assert alert.id in ids


@pytest.mark.django_db
def test_alert_history_not_in_active_list(
    authenticated_almacenista_client, almacenista_user
):
    from django.utils import timezone

    product = ProductFactory()
    Alert.objects.create(
        product=product,
        alert_type=AlertType.LOW_STOCK,
        severity=AlertSeverity.HIGH,
        category=AlertCategory.STOCK,
        message="resolved",
        is_resolved=True,
        resolved_at=timezone.now(),
        resolved_by=almacenista_user,
    )

    resp = authenticated_almacenista_client.get("/api/v1/alerts/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.django_db
def test_alert_stats_empty(authenticated_almacenista_client):
    resp = authenticated_almacenista_client.get("/api/v1/alerts/stats/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_active"] == 0
    assert data["by_severity"] == {}
    assert data["by_category"] == {}
