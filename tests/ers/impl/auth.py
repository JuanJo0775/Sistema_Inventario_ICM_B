"""Implementaciones Gherkin — RF001 (Autenticación) y RF002 (Gestión de credenciales)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import UserRole

_BOGOTA = ZoneInfo("America/Bogota")

# --- RF-001 -----------------------------------------------------------------


def impl_rf001_s01(api_client: APIClient, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "testpass123"},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert "access" in r.data and "refresh" in r.data
    assert r.data["user"]["role"] == UserRole.ALMACENISTA


def impl_rf001_s02(api_client: APIClient, auxiliar_user):
    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    url = reverse("token_obtain_pair")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.post(
            url,
            {"username": auxiliar_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["user"]["role"] == UserRole.AUXILIAR_DESPACHO


def impl_rf001_s03(api_client: APIClient, auxiliar_user):
    outer = datetime(2026, 5, 5, 13, 0, 0, tzinfo=_BOGOTA)
    url = reverse("token_obtain_pair")
    with patch("django.utils.timezone.now", return_value=outer):
        r = api_client.post(
            url,
            {"username": auxiliar_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


def impl_rf001_s04(api_client: APIClient, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "MALA_CLAVE"},
        format="json",
    )
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def impl_rf001_s05(api_client: APIClient, administrador_user):
    outer = datetime(2026, 5, 5, 22, 0, 0, tzinfo=_BOGOTA)
    url = reverse("token_obtain_pair")
    with patch("django.utils.timezone.now", return_value=outer):
        r = api_client.post(
            url,
            {"username": administrador_user.username, "password": "testpass123"},
            format="json",
        )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["user"]["role"] == UserRole.ADMINISTRADOR


# --- RF-002 -----------------------------------------------------------------


def impl_rf002_s01(api_client: APIClient, almacenista_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-users")
    r = api_client.post(
        url,
        {
            "username": "nuevo_gherkin_rf002",
            "email": "nuevo_gherkin_rf002@example.com",
            "password": "secreto12345",
            "role": UserRole.AUXILIAR_DESPACHO,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rf002_s02(api_client: APIClient, almacenista_user, auxiliar_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-user-detail", kwargs={"pk": auxiliar_user.pk})
    r = api_client.patch(url, {"password": "otraClaveSegura1"}, format="json")
    assert r.status_code == status.HTTP_200_OK


def impl_rf002_s03(api_client: APIClient, almacenista_user, auxiliar_user):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    u = User.objects.create(
        username="para_deshabilitar_rf002",
        email="para_deshabilitar_rf002@example.com",
        role=UserRole.AUXILIAR_DESPACHO,
    )
    u.set_password("xSecreto99")
    u.save()
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-user-disable", kwargs={"pk": u.pk})
    r = api_client.post(url)
    assert r.status_code == status.HTTP_204_NO_CONTENT
    u.refresh_from_db()
    assert u.is_active is False


def impl_rf002_s04(api_client: APIClient, auxiliar_user):
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("auth-user-detail", kwargs={"pk": auxiliar_user.pk})
    r = api_client.patch(url, {"first_name": "NoDebe"}, format="json")
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rf002_s05(api_client: APIClient, almacenista_user):
    api_client.force_authenticate(user=almacenista_user)
    url = reverse("auth-users")
    r = api_client.post(
        url,
        {
            "username": almacenista_user.username,
            "email": "dup_rf002@example.com",
            "password": "secreto12345",
            "role": UserRole.AUXILIAR_DESPACHO,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_400_BAD_REQUEST


IMPLEMENTATIONS: dict[str, object] = {
    "RF001-S01": impl_rf001_s01,
    "RF001-S02": impl_rf001_s02,
    "RF001-S03": impl_rf001_s03,
    "RF001-S04": impl_rf001_s04,
    "RF001-S05": impl_rf001_s05,
    "RF002-S01": impl_rf002_s01,
    "RF002-S02": impl_rf002_s02,
    "RF002-S03": impl_rf002_s03,
    "RF002-S04": impl_rf002_s04,
    "RF002-S05": impl_rf002_s05,
}
