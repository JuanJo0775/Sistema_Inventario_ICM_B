"""Tests para el endpoint de rehabilitación de usuarios y el filtro include_inactive."""

from __future__ import annotations

import pytest

from apps.audit.models import AuditEventType, AuditLog
from apps.authentication.services import disable_user, enable_user
from shared.exceptions import UnauthorizedCredentialManagementError
from tests.factories import AlmacenistaFactory, UserFactory

# ===========================================================================
# enable_user — servicio
# ===========================================================================


class TestEnableUserService:
    @pytest.mark.django_db
    def test_enable_reactivates_disabled_user(self, almacenista_user):
        target = UserFactory(is_active=False)
        result = enable_user(almacenista_user, target.id)
        target.refresh_from_db()
        assert target.is_active is True
        assert result.is_active is True

    @pytest.mark.django_db
    def test_enable_logs_audit_event(self, almacenista_user):
        target = UserFactory(is_active=False)
        enable_user(almacenista_user, target.id)
        log = AuditLog.objects.filter(event_type=AuditEventType.USER_ENABLED).first()
        assert log is not None
        assert target.username in log.description

    @pytest.mark.django_db
    def test_enable_raises_if_not_almacenista(self, auxiliar_user):
        target = UserFactory(is_active=False)
        with pytest.raises(UnauthorizedCredentialManagementError):
            enable_user(auxiliar_user, target.id)

    @pytest.mark.django_db
    def test_enable_already_active_user_is_idempotent(self, almacenista_user):
        target = UserFactory(is_active=True)
        result = enable_user(almacenista_user, target.id)
        target.refresh_from_db()
        assert target.is_active is True
        assert result.is_active is True


# ===========================================================================
# POST /api/v1/auth/users/{id}/enable/ — endpoint HTTP
# ===========================================================================


class TestUserEnableEndpoint:
    @pytest.mark.django_db
    def test_enable_returns_200_with_user_data(self, authenticated_almacenista_client):
        target = UserFactory(is_active=False)
        resp = authenticated_almacenista_client.post(
            f"/api/v1/auth/users/{target.id}/enable/"
        )
        assert resp.status_code == 200
        assert resp.data["id"] == str(target.id)
        assert resp.data["is_active"] is True
        target.refresh_from_db()
        assert target.is_active is True

    @pytest.mark.django_db
    def test_enable_requires_almacenista(self, authenticated_administrador_client):
        target = UserFactory(is_active=False)
        resp = authenticated_administrador_client.post(
            f"/api/v1/auth/users/{target.id}/enable/"
        )
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_enable_requires_authentication(self, api_client):
        target = UserFactory(is_active=False)
        resp = api_client.post(f"/api/v1/auth/users/{target.id}/enable/")
        assert resp.status_code == 401

    @pytest.mark.django_db
    def test_enable_404_on_nonexistent_user(self, authenticated_almacenista_client):
        import uuid

        resp = authenticated_almacenista_client.post(
            f"/api/v1/auth/users/{uuid.uuid4()}/enable/"
        )
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_disable_then_enable_roundtrip(
        self, authenticated_almacenista_client, almacenista_user
    ):
        target = UserFactory(is_active=True)
        # Disable
        resp_disable = authenticated_almacenista_client.post(
            f"/api/v1/auth/users/{target.id}/disable/"
        )
        assert resp_disable.status_code == 204
        target.refresh_from_db()
        assert target.is_active is False
        # Re-enable
        resp_enable = authenticated_almacenista_client.post(
            f"/api/v1/auth/users/{target.id}/enable/"
        )
        assert resp_enable.status_code == 200
        target.refresh_from_db()
        assert target.is_active is True


# ===========================================================================
# GET /api/v1/auth/users/ — filtro include_inactive
# ===========================================================================


class TestUserListIncludeInactive:
    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(self, authenticated_almacenista_client):
        active = UserFactory(is_active=True)
        inactive = UserFactory(is_active=False)
        resp = authenticated_almacenista_client.get("/api/v1/auth/users/")
        assert resp.status_code == 200
        results = resp.data.get("results", resp.data)
        ids = [u["id"] for u in results]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(self, authenticated_almacenista_client):
        inactive = UserFactory(is_active=False)
        resp = authenticated_almacenista_client.get(
            "/api/v1/auth/users/?include_inactive=true"
        )
        assert resp.status_code == 200
        results = resp.data.get("results", resp.data)
        ids = [u["id"] for u in results]
        assert str(inactive.id) in ids

    @pytest.mark.django_db
    def test_list_accessible_by_administrador(self, authenticated_administrador_client):
        UserFactory(is_active=True)
        resp = authenticated_administrador_client.get("/api/v1/auth/users/")
        assert resp.status_code == 200

    @pytest.mark.django_db
    def test_list_not_accessible_unauthenticated(self, api_client):
        resp = api_client.get("/api/v1/auth/users/")
        assert resp.status_code == 401
