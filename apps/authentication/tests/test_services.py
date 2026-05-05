from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.authentication.models import UserRole
from rest_framework.exceptions import AuthenticationFailed

from apps.authentication.services import authenticate_user, create_user, is_within_operating_hours
from apps.audit.models import AuditEventType, AuditLog
from shared.exceptions import OutsideOperatingHoursError, UnauthorizedCredentialManagementError
from tests.factories import AlmacenistaFactory, UserFactory


@pytest.mark.django_db
def test_auxiliar_blocked_outside_hours(auxiliar_user):
    with patch("apps.authentication.services.is_within_operating_hours", return_value=False):
        with pytest.raises(OutsideOperatingHoursError):
            authenticate_user(auxiliar_user.username, "testpass123")


@pytest.mark.django_db
def test_only_almacenista_creates_users(auxiliar_user):
    with pytest.raises(UnauthorizedCredentialManagementError):
        create_user(
            auxiliar_user,
            {
                "username": "nuevo_aux",
                "email": "nuevo_aux@example.com",
                "password": "secreto123",
                "role": UserRole.AUXILIAR_DESPACHO,
            },
        )


@pytest.mark.django_db
def test_disabled_user_cannot_login():
    u = UserFactory(is_active=False)
    with pytest.raises(AuthenticationFailed):
        authenticate_user(u.username, "testpass123")


@pytest.mark.django_db
def test_operating_hours_enforced_per_request(auxiliar_user):
    from rest_framework.test import APIRequestFactory

    from shared.permissions import IsWithinOperatingHours

    factory = APIRequestFactory()
    request = factory.get("/dummy")
    request.user = auxiliar_user
    with patch("apps.authentication.services.is_within_operating_hours", return_value=False):
        assert IsWithinOperatingHours().has_permission(request, view=None) is False
    with patch("apps.authentication.services.is_within_operating_hours", return_value=True):
        assert IsWithinOperatingHours().has_permission(request, view=None) is True
