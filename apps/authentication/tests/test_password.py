"""Tests de self-service change-password, forgot-password y reset-password (RF-001)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework import status

CHANGE_URL = "/api/v1/auth/change-password/"
FORGOT_URL = "/api/v1/auth/forgot-password/"
RESET_URL = "/api/v1/auth/reset-password/"

STRONG_PASSWORD = "S3cur0P@ssw0rd#2026"
NEW_PASSWORD = "N3wP@ssw0rd#2026!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reset_token(user, *, expired: bool = False, used: bool = False):
    from apps.authentication.models import PasswordResetToken

    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    now = timezone.now()
    expires_at = (now - timedelta(hours=2)) if expired else (now + timedelta(hours=1))
    PasswordResetToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at,
        used=used,
        used_at=now if used else None,
    )
    return raw


# ===========================================================================
# ChangePasswordView  POST /api/v1/auth/change-password/
# ===========================================================================


@pytest.mark.django_db
class TestChangePasswordView:
    def test_success_changes_password_and_logs_audit(
        self, authenticated_almacenista_client, almacenista_user
    ):
        almacenista_user.set_password(STRONG_PASSWORD)
        almacenista_user.save()

        response = authenticated_almacenista_client.post(
            CHANGE_URL,
            {
                "current_password": STRONG_PASSWORD,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data

        from apps.audit.models import AuditEventType, AuditLog

        assert AuditLog.objects.filter(
            event_type=AuditEventType.PASSWORD_CHANGED,
            user=almacenista_user,
        ).exists()

    def test_success_blacklists_jwt_tokens(
        self, authenticated_almacenista_client, almacenista_user
    ):
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        RefreshToken.for_user(almacenista_user)
        almacenista_user.set_password(STRONG_PASSWORD)
        almacenista_user.save()

        before_blacklisted = BlacklistedToken.objects.filter(
            token__user=almacenista_user
        ).count()

        authenticated_almacenista_client.post(
            CHANGE_URL,
            {
                "current_password": STRONG_PASSWORD,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        outstanding = OutstandingToken.objects.filter(user=almacenista_user).count()
        after_blacklisted = BlacklistedToken.objects.filter(
            token__user=almacenista_user
        ).count()
        assert after_blacklisted > before_blacklisted or outstanding == 0

    def test_wrong_current_password_returns_422(
        self, authenticated_almacenista_client
    ):
        response = authenticated_almacenista_client.post(
            CHANGE_URL,
            {
                "current_password": "wrong-password",
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_passwords_mismatch_returns_400(
        self, authenticated_almacenista_client, almacenista_user
    ):
        almacenista_user.set_password(STRONG_PASSWORD)
        almacenista_user.save()

        response = authenticated_almacenista_client.post(
            CHANGE_URL,
            {
                "current_password": STRONG_PASSWORD,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": "different-password",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.post(
            CHANGE_URL,
            {
                "current_password": STRONG_PASSWORD,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auxiliar_can_change_own_password(self, api_client, auxiliar_user):
        auxiliar_user.set_password(STRONG_PASSWORD)
        auxiliar_user.save()
        api_client.force_authenticate(user=auxiliar_user)

        response = api_client.post(
            CHANGE_URL,
            {
                "current_password": STRONG_PASSWORD,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK


# ===========================================================================
# ForgotPasswordView  POST /api/v1/auth/forgot-password/
# ===========================================================================


@pytest.mark.django_db
class TestForgotPasswordView:
    def test_existing_email_returns_200_and_sends_email(
        self, api_client, almacenista_user
    ):
        mail.outbox.clear()

        response = api_client.post(
            FORGOT_URL, {"email": almacenista_user.email}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        assert len(mail.outbox) == 1
        assert almacenista_user.email in mail.outbox[0].to

    def test_nonexistent_email_returns_same_200_anti_enumeration(self, api_client):
        mail.outbox.clear()

        response = api_client.post(
            FORGOT_URL, {"email": "no-existe@example.com"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 0

    def test_inactive_user_returns_same_200_anti_enumeration(
        self, api_client, auxiliar_user
    ):
        auxiliar_user.is_active = False
        auxiliar_user.save()
        mail.outbox.clear()

        response = api_client.post(
            FORGOT_URL, {"email": auxiliar_user.email}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 0

    def test_invalid_email_format_returns_400(self, api_client):
        response = api_client.post(
            FORGOT_URL, {"email": "not-an-email"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_second_request_invalidates_previous_token(
        self, api_client, almacenista_user
    ):
        from apps.authentication.models import PasswordResetToken

        api_client.post(
            FORGOT_URL, {"email": almacenista_user.email}, format="json"
        )
        first_token = PasswordResetToken.objects.filter(
            user=almacenista_user, used=False
        ).first()
        assert first_token is not None

        api_client.post(
            FORGOT_URL, {"email": almacenista_user.email}, format="json"
        )

        first_token.refresh_from_db()
        assert first_token.used is True

        active_tokens = PasswordResetToken.objects.filter(
            user=almacenista_user, used=False
        ).count()
        assert active_tokens == 1

    def test_creates_audit_log(self, api_client, almacenista_user):
        from apps.audit.models import AuditEventType, AuditLog

        api_client.post(
            FORGOT_URL, {"email": almacenista_user.email}, format="json"
        )

        assert AuditLog.objects.filter(
            event_type=AuditEventType.PASSWORD_RESET_REQUESTED,
            user=almacenista_user,
        ).exists()


# ===========================================================================
# ResetPasswordView  POST /api/v1/auth/reset-password/
# ===========================================================================


@pytest.mark.django_db
class TestResetPasswordView:
    def test_success_resets_password_and_marks_token_used(
        self, api_client, almacenista_user
    ):
        from apps.authentication.models import PasswordResetToken

        raw_token = _make_reset_token(almacenista_user)

        response = api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        reset_token = PasswordResetToken.objects.get(token_hash=token_hash)
        assert reset_token.used is True
        assert reset_token.used_at is not None

    def test_success_blacklists_active_sessions(
        self, api_client, almacenista_user
    ):
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        from rest_framework_simplejwt.tokens import RefreshToken

        RefreshToken.for_user(almacenista_user)
        raw_token = _make_reset_token(almacenista_user)

        api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        assert BlacklistedToken.objects.filter(
            token__user=almacenista_user
        ).exists()

    def test_success_creates_audit_log(self, api_client, almacenista_user):
        from apps.audit.models import AuditEventType, AuditLog

        raw_token = _make_reset_token(almacenista_user)

        api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        assert AuditLog.objects.filter(
            event_type=AuditEventType.PASSWORD_RESET_COMPLETED,
            user=almacenista_user,
        ).exists()

    def test_invalid_token_returns_422(self, api_client):
        response = api_client.post(
            RESET_URL,
            {
                "token": "token-que-no-existe",
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_expired_token_returns_422(self, api_client, almacenista_user):
        raw_token = _make_reset_token(almacenista_user, expired=True)

        response = api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_used_token_returns_422(self, api_client, almacenista_user):
        raw_token = _make_reset_token(almacenista_user, used=True)

        response = api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_inactive_user_token_returns_422(self, api_client, auxiliar_user):
        raw_token = _make_reset_token(auxiliar_user)
        auxiliar_user.is_active = False
        auxiliar_user.save()

        response = api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_passwords_mismatch_returns_400(self, api_client, almacenista_user):
        raw_token = _make_reset_token(almacenista_user)

        response = api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": "different-password",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_reuse_after_success_returns_422(self, api_client, almacenista_user):
        """Seguridad: reutilización del token después de uso exitoso."""
        raw_token = _make_reset_token(almacenista_user)

        api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        second_response = api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": STRONG_PASSWORD,
                "new_password_confirm": STRONG_PASSWORD,
            },
            format="json",
        )
        assert second_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_old_password_fails_after_reset(self, api_client, almacenista_user):
        """Seguridad: las credenciales antiguas son inválidas tras el reset."""
        old_password = STRONG_PASSWORD
        almacenista_user.set_password(old_password)
        almacenista_user.save()

        raw_token = _make_reset_token(almacenista_user)

        api_client.post(
            RESET_URL,
            {
                "token": raw_token,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        login_response = api_client.post(
            "/api/v1/auth/login/",
            {"username": almacenista_user.username, "password": old_password},
            format="json",
        )
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


# ===========================================================================
# UserListCreateView — filtros y paginación
# ===========================================================================


@pytest.mark.django_db
class TestUserListFilters:
    def test_filter_by_role(
        self, authenticated_almacenista_client, almacenista_user, auxiliar_user
    ):
        response = authenticated_almacenista_client.get(
            "/api/v1/auth/users/?role=auxiliar_despacho"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        # Puede venir paginado o sin paginar
        items = data.get("results", data) if isinstance(data, dict) else data
        roles = [u["role"] for u in items]
        assert all(r == "auxiliar_despacho" for r in roles)

    def test_search_by_username(
        self, authenticated_almacenista_client, almacenista_user
    ):
        response = authenticated_almacenista_client.get(
            f"/api/v1/auth/users/?search={almacenista_user.username[:4]}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        items = data.get("results", data) if isinstance(data, dict) else data
        usernames = [u["username"] for u in items]
        assert almacenista_user.username in usernames

    def test_pagination_with_page_param(
        self, authenticated_almacenista_client, almacenista_user, auxiliar_user
    ):
        response = authenticated_almacenista_client.get(
            "/api/v1/auth/users/?page=1&page_size=1"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data
        assert len(response.data["results"]) <= 1
