"""Tests de endpoints REST del módulo de auditoría."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditEventType
from apps.audit.services import log_event


@pytest.mark.django_db
def test_audit_log_list_returns_200_for_almacenista(
    authenticated_almacenista_client,
):
    response = authenticated_almacenista_client.get("/api/v1/audit/")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data


@pytest.mark.django_db
def test_audit_log_list_returns_403_for_auxiliar(auxiliar_user):
    client = APIClient()
    client.force_authenticate(user=auxiliar_user)
    response = client.get("/api/v1/audit/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_audit_log_detail_returns_200(
    authenticated_almacenista_client, almacenista_user
):
    log = log_event(
        AuditEventType.LOGIN_SUCCESS,
        description="Login de prueba",
        user=almacenista_user,
    )
    response = authenticated_almacenista_client.get(f"/api/v1/audit/{log.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert str(response.data["id"]) == str(log.id)


@pytest.mark.django_db
def test_audit_log_patch_returns_405(
    authenticated_almacenista_client, almacenista_user
):
    log = log_event(
        AuditEventType.LOGIN_SUCCESS,
        description="Login de prueba",
        user=almacenista_user,
    )
    response = authenticated_almacenista_client.patch(
        f"/api/v1/audit/{log.id}/",
        {"description": "modificado"},
        format="json",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
