"""Tests de integración HTTP para los endpoints de horario y permisos temporales."""

from __future__ import annotations

from datetime import time, timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse

from apps.authentication.models import TemporaryAccessPermit, UserRole, UserSchedule
from tests.factories import UserFactory


@pytest.mark.django_db
class TestUserScheduleEndpoint:
    """GET/POST /api/v1/auth/users/<pk>/schedule/"""

    def test_get_schedule_returns_404_when_none_exists(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        response = authenticated_almacenista_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_almacenista_can_create_schedule(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "morning_start": "08:00:00",
            "morning_end": "11:00:00",
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert UserSchedule.objects.filter(user=auxiliar_user).exists()

    def test_almacenista_can_get_existing_schedule(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        UserSchedule.objects.create(
            user=auxiliar_user,
            morning_start=time(8, 0),
            morning_end=time(11, 0),
        )
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        response = authenticated_almacenista_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["morning_start"] == "08:00:00"

    def test_administrador_can_read_schedule(
        self, authenticated_administrador_client, auxiliar_user
    ):
        UserSchedule.objects.create(
            user=auxiliar_user,
            morning_start=time(8, 0),
            morning_end=time(11, 0),
        )
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        response = authenticated_administrador_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_administrador_cannot_write_schedule(
        self, authenticated_administrador_client, auxiliar_user
    ):
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        payload = {"morning_start": "08:00:00", "morning_end": "11:00:00"}
        response = authenticated_administrador_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_schedule_with_invalid_range_returns_400(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "morning_start": "11:00:00",
            "morning_end": "08:00:00",  # end before start
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_schedule_for_nonexistent_user_returns_404(
        self, authenticated_almacenista_client
    ):
        import uuid

        url = reverse("auth-user-schedule", kwargs={"pk": uuid.uuid4()})
        payload = {"morning_start": "08:00:00", "morning_end": "11:00:00"}
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_request_returns_401(self, api_client, auxiliar_user):
        url = reverse("auth-user-schedule", kwargs={"pk": auxiliar_user.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTemporaryPermitListCreateEndpoint:
    """GET/POST /api/v1/auth/users/<pk>/temporary-permits/"""

    def test_almacenista_can_list_empty_permits(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        response = authenticated_almacenista_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_almacenista_can_grant_24_7_permit(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=2)).isoformat(),
            "allow_24_7": True,
            "reason": "Inventario nocturno urgente",
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert TemporaryAccessPermit.objects.filter(user=auxiliar_user).exists()
        assert response.data["allow_24_7"] is True

    def test_almacenista_can_grant_permit_with_custom_ranges(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=3)).isoformat(),
            "allow_24_7": False,
            "custom_morning_start": "01:00:00",
            "custom_morning_end": "04:00:00",
            "reason": "Turno nocturno especial",
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_permit_without_range_when_not_24_7_returns_400(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=2)).isoformat(),
            "allow_24_7": False,
            "reason": "Sin franjas horarias definidas",
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_permit_with_inverted_datetimes_returns_400(
        self, authenticated_almacenista_client, auxiliar_user
    ):
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "start_datetime": (timezone.now() + timedelta(hours=2)).isoformat(),
            "end_datetime": timezone.now().isoformat(),  # end before start
            "allow_24_7": True,
            "reason": "Fechas invertidas",
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_administrador_can_list_permits(
        self, authenticated_administrador_client, almacenista_user, auxiliar_user
    ):
        TemporaryAccessPermit.objects.create(
            user=auxiliar_user,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=1),
            allow_24_7=True,
            reason="Test permit",
            granted_by=almacenista_user,
        )
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        response = authenticated_administrador_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_administrador_cannot_grant_permit(
        self, authenticated_administrador_client, auxiliar_user
    ):
        url = reverse("auth-user-temporary-permits", kwargs={"pk": auxiliar_user.pk})
        payload = {
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=1)).isoformat(),
            "allow_24_7": True,
            "reason": "Intento de admin",
        }
        response = authenticated_administrador_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_grant_permit_for_nonexistent_user_returns_404(
        self, authenticated_almacenista_client
    ):
        import uuid

        url = reverse("auth-user-temporary-permits", kwargs={"pk": uuid.uuid4()})
        payload = {
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=1)).isoformat(),
            "allow_24_7": True,
            "reason": "Usuario inexistente",
        }
        response = authenticated_almacenista_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTemporaryPermitRevokeEndpoint:
    """POST /api/v1/auth/temporary-permits/<pk>/revoke/"""

    def _create_permit(self, almacenista, auxiliar):
        return TemporaryAccessPermit.objects.create(
            user=auxiliar,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=2),
            allow_24_7=True,
            reason="Permit to revoke",
            granted_by=almacenista,
        )

    def test_almacenista_can_revoke_permit(
        self, authenticated_almacenista_client, almacenista_user, auxiliar_user
    ):
        permit = self._create_permit(almacenista_user, auxiliar_user)
        url = reverse("auth-temporary-permit-revoke", kwargs={"pk": permit.pk})
        response = authenticated_almacenista_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        permit.refresh_from_db()
        assert permit.is_active is False

    def test_revoke_is_idempotent(
        self, authenticated_almacenista_client, almacenista_user, auxiliar_user
    ):
        permit = self._create_permit(almacenista_user, auxiliar_user)
        url = reverse("auth-temporary-permit-revoke", kwargs={"pk": permit.pk})
        authenticated_almacenista_client.post(url)
        response = authenticated_almacenista_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        permit.refresh_from_db()
        assert permit.is_active is False

    def test_administrador_cannot_revoke_permit(
        self, authenticated_administrador_client, almacenista_user, auxiliar_user
    ):
        permit = self._create_permit(almacenista_user, auxiliar_user)
        url = reverse("auth-temporary-permit-revoke", kwargs={"pk": permit.pk})
        response = authenticated_administrador_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_revoke_nonexistent_permit_returns_404(
        self, authenticated_almacenista_client
    ):
        import uuid

        url = reverse("auth-temporary-permit-revoke", kwargs={"pk": uuid.uuid4()})
        response = authenticated_almacenista_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_response_contains_permit_data(
        self, authenticated_almacenista_client, almacenista_user, auxiliar_user
    ):
        permit = self._create_permit(almacenista_user, auxiliar_user)
        url = reverse("auth-temporary-permit-revoke", kwargs={"pk": permit.pk})
        response = authenticated_almacenista_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert str(permit.pk) == response.data["id"]
        assert response.data["is_active"] is False
