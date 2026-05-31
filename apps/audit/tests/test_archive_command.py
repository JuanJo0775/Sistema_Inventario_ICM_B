"""Tests para el management command archive_old_audit_logs (M-02)."""

from __future__ import annotations

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.audit.models import AuditEventType, AuditLog, AuditLogArchive


def _create_log(days_ago: int) -> AuditLog:
    log = AuditLog.objects.create(
        event_type=AuditEventType.LOGIN_SUCCESS,
        description="Test log",
    )
    AuditLog.objects.filter(pk=log.pk).update(
        created_at=timezone.now() - timedelta(days=days_ago)
    )
    log.refresh_from_db()
    return log


@pytest.mark.django_db
def test_archive_moves_old_records(db):
    """Logs más antiguos que el threshold se mueven al archivo."""
    old_log = _create_log(400)
    recent_log = _create_log(10)

    out = StringIO()
    call_command("archive_old_audit_logs", "--older-than-days=365", stdout=out)

    assert not AuditLog.objects.filter(pk=old_log.pk).exists()
    assert AuditLogArchive.objects.filter(id=old_log.id).exists()
    assert AuditLog.objects.filter(pk=recent_log.pk).exists()


@pytest.mark.django_db
def test_archive_preserves_recent_records(db):
    """Logs dentro del threshold NO se archivan."""
    recent_log = _create_log(300)

    out = StringIO()
    call_command("archive_old_audit_logs", "--older-than-days=365", stdout=out)

    assert AuditLog.objects.filter(pk=recent_log.pk).exists()
    assert not AuditLogArchive.objects.filter(id=recent_log.id).exists()


@pytest.mark.django_db
def test_archive_dry_run_makes_no_changes(db):
    """--dry-run no modifica la base de datos."""
    old_log = _create_log(400)

    out = StringIO()
    call_command(
        "archive_old_audit_logs", "--older-than-days=365", "--dry-run", stdout=out
    )

    assert AuditLog.objects.filter(pk=old_log.pk).exists()
    assert not AuditLogArchive.objects.exists()
    assert (
        "dry-run" in out.getvalue().lower()
        or "dry_run" in out.getvalue().lower()
        or "DRY" in out.getvalue()
    )


@pytest.mark.django_db
def test_archive_batch_processing(db):
    """Procesa en batches; todos los registros candidatos se archivan."""
    old_logs = [_create_log(400) for _ in range(5)]

    out = StringIO()
    call_command(
        "archive_old_audit_logs",
        "--older-than-days=365",
        "--batch-size=2",
        stdout=out,
    )

    for log in old_logs:
        assert not AuditLog.objects.filter(pk=log.pk).exists()
        assert AuditLogArchive.objects.filter(id=log.id).exists()


@pytest.mark.django_db
def test_archive_empty_returns_early(db):
    """Sin logs candidatos, el command termina limpiamente."""
    _create_log(10)  # log reciente, no archivable

    out = StringIO()
    call_command("archive_old_audit_logs", "--older-than-days=365", stdout=out)

    assert "No hay logs" in out.getvalue()
