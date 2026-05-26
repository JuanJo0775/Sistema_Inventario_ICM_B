from __future__ import annotations

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
