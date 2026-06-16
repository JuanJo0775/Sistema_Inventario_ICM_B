"""Tests de endpoints REST del módulo de autenticación."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from apps.authentication.views import (
    HealthCheckView,
    ICMTokenObtainPairView,
    UserListCreateView,
)


def test_administrador_can_read_users_but_cannot_write(
    authenticated_administrador_client, almacenista_user
):
    list_response = authenticated_administrador_client.get(reverse("auth-users"))
    assert list_response.status_code == status.HTTP_200_OK

    detail_response = authenticated_administrador_client.get(
        reverse("auth-user-detail", kwargs={"pk": almacenista_user.pk})
    )
    assert detail_response.status_code == status.HTTP_200_OK

    create_response = authenticated_administrador_client.post(
        reverse("auth-users"),
        {
            "username": "admin_no_write",
            "email": "admin_no_write@example.com",
            "password": "secreto12345",
            "role": "auxiliar_despacho",
        },
        format="json",
    )
    assert create_response.status_code == status.HTTP_403_FORBIDDEN

    patch_response = authenticated_administrador_client.patch(
        reverse("auth-user-detail", kwargs={"pk": almacenista_user.pk}),
        {"first_name": "No"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_403_FORBIDDEN


def test_auth_views_are_exposed():
    assert HealthCheckView is not None
    assert ICMTokenObtainPairView is not None
    assert UserListCreateView is not None


@pytest.mark.django_db
def test_me_endpoint_returns_current_user(
    authenticated_almacenista_client, almacenista_user
):
    response = authenticated_almacenista_client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == almacenista_user.username


@pytest.mark.django_db
def test_logout_returns_204(authenticated_almacenista_client, almacenista_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(almacenista_user)
    response = authenticated_almacenista_client.post(
        "/api/v1/auth/logout/",
        {"refresh": str(refresh)},
        format="json",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_user_disable_returns_204(authenticated_almacenista_client, auxiliar_user):
    response = authenticated_almacenista_client.post(
        f"/api/v1/auth/users/{auxiliar_user.pk}/disable/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_user_enable_returns_200(authenticated_almacenista_client, auxiliar_user):
    auxiliar_user.is_active = False
    auxiliar_user.save()
    response = authenticated_almacenista_client.post(
        f"/api/v1/auth/users/{auxiliar_user.pk}/enable/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_active"] is True
