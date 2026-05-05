from __future__ import annotations

import pytest
from rest_framework.exceptions import AuthenticationFailed

from apps.audit.models import AuditEventType, AuditLog
from apps.audit.services import log_event
from apps.authentication.services import authenticate_user
from tests.factories import UserFactory


@pytest.mark.django_db
def test_login_success_logged(almacenista_user):
    before = AuditLog.objects.count()
    authenticate_user(almacenista_user.username, "testpass123")
    assert (
        AuditLog.objects.filter(event_type=AuditEventType.LOGIN_SUCCESS).count()
        >= before + 1
    )


@pytest.mark.django_db
def test_login_failure_logged():
    with pytest.raises(AuthenticationFailed):
        authenticate_user("no_existe", "bad")
    assert AuditLog.objects.filter(event_type=AuditEventType.LOGIN_FAILED).exists()


@pytest.mark.django_db
def test_movement_creation_logged(almacenista_user, sample_product, sample_locations):
    from apps.movements.services import register_entry

    loc = sample_locations[0]
    m = register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        1,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    assert AuditLog.objects.filter(
        event_type=AuditEventType.MOVEMENT_CREATED, movement=m
    ).exists()


@pytest.mark.django_db
def test_audit_log_metadata_mutable_in_memory(almacenista_user):
    """El modelo no impide mutar el objeto en memoria; la inmutabilidad es por contrato de API (BR-10)."""
    log = log_event(
        AuditEventType.LOGOUT, description="Cierre", user=almacenista_user, detail={}
    )
    log.metadata = {"x": 1}
    assert log.metadata["x"] == 1
