"""Pruebas de integración HTTP (API v1) con cliente DRF."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse

_BOGOTA = ZoneInfo("America/Bogota")


@pytest.mark.django_db
def test_reports_kpi_requires_auth(api_client):
    url = reverse("reports-kpi")
    assert api_client.get(url).status_code == 401


@pytest.mark.django_db
def test_reports_kpi_almacenista_200(authenticated_almacenista_client):
    url = reverse("reports-kpi")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == 200
    assert "movements_today" in r.data


@pytest.mark.django_db
def test_inventory_full_list_authenticated(
    authenticated_almacenista_client, sample_product
):
    url = reverse("inventory-full")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == 200
    assert "results" in r.data


@pytest.mark.django_db
def test_catalog_resolve_identifier_param(
    authenticated_almacenista_client, sample_product
):
    url = reverse("catalog-resolve")
    r = authenticated_almacenista_client.get(url, {"identifier": sample_product.sku})
    assert r.status_code == 200
    assert r.data["sku"] == sample_product.sku


@pytest.mark.django_db
def test_auth_login_with_username_returns_jwt_and_profile(api_client, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "testpass123"},
        format="json",
    )
    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data
    assert r.data["user"]["username"] == almacenista_user.username
    assert r.data["user"]["email"] == almacenista_user.email
    assert "phone" in r.data["user"]
    assert r.data["user"]["role"] == almacenista_user.role


@pytest.mark.django_db
def test_auth_login_with_email_returns_jwt(api_client, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"email": almacenista_user.email, "password": "testpass123"},
        format="json",
    )
    assert r.status_code == 200
    assert r.data["user"]["id"] == almacenista_user.id


@pytest.mark.django_db
def test_auth_token_refresh_auxiliar_outside_hours_forbidden(api_client, auxiliar_user):
    """
    RF-001, BR-03 — Sesión renovada: auxiliar sin acceso fuera de franja.

    Extiende el criterio Gherkin del ERS (`docs/requisitos/ERS_ICM_Requisitos.md`):
    Feature «Inicio de sesión…», Scenario 3 (acceso bloqueado fuera de horario).
    La renovación con `refresh` debe aplicar la misma restricción que el login,
    para no eludir BR-03 manteniendo una sesión larga (coherente con informe de elicitación, restricción horaria auxiliar).
    """
    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    outer = datetime(2026, 5, 5, 13, 0, 0, tzinfo=_BOGOTA)
    login_url = reverse("token_obtain_pair")
    refresh_url = reverse("token_refresh")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.post(
            login_url,
            {"username": auxiliar_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code == 200, r.data
    token = r.data["refresh"]
    with patch("django.utils.timezone.now", return_value=outer):
        r2 = api_client.post(refresh_url, {"refresh": token}, format="json")
    assert r2.status_code == 403


@pytest.mark.django_db
def test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window(
    api_client, almacenista_user
):
    """
    RF-001 — Contraste con Scenario 3 (solo aplica a auxiliar).

    ERS Scenario 1 (login almacenista) y Scenario 5 (administrador sin restricción horaria «laboral»):
    roles distintos de auxiliar no quedan bloqueados por BR-03 al renovar token.
    """
    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    outer = datetime(2026, 5, 5, 13, 0, 0, tzinfo=_BOGOTA)
    login_url = reverse("token_obtain_pair")
    refresh_url = reverse("token_refresh")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.post(
            login_url,
            {"username": almacenista_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code == 200
    token = r.data["refresh"]
    with patch("django.utils.timezone.now", return_value=outer):
        r2 = api_client.post(refresh_url, {"refresh": token}, format="json")
    assert r2.status_code == 200
    assert "access" in r2.data


@pytest.mark.django_db
def test_auth_user_disable_route(api_client, almacenista_user, auxiliar_user):
    url = reverse("auth-user-disable", kwargs={"pk": auxiliar_user.pk})
    api_client.force_authenticate(user=almacenista_user)
    r = api_client.post(url)
    assert r.status_code == 204
    auxiliar_user.refresh_from_db()
    assert auxiliar_user.is_active is False


@pytest.mark.django_db
def test_alerts_list_uses_is_resolved_filter(
    authenticated_almacenista_client, sample_product
):
    from apps.alerts.models import Alert, AlertType

    Alert.objects.create(
        product=sample_product,
        alert_type=AlertType.LOW_STOCK,
        message="x",
        is_resolved=False,
    )
    url = reverse("alerts-list")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == 200
    assert len(r.data["results"]) >= 1
