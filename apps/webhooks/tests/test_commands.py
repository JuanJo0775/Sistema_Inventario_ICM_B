"""Tests para el management command deliver_webhooks."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.audit.models import AuditEventType, AuditLog


@pytest.mark.django_db
def test_deliver_webhooks_no_pending():
    """Sin webhooks pendientes, el command informa que no hay nada."""
    out = StringIO()
    with patch(
        "apps.webhooks.management.commands.deliver_webhooks.deliver_pending_webhooks",
        return_value=(0, 0),
    ):
        call_command("deliver_webhooks", stdout=out)
    assert "No hay webhooks pendientes" in out.getvalue()


@pytest.mark.django_db
def test_deliver_webhooks_with_deliveries():
    """Con webhooks entregados, el command reporta los totales."""
    out = StringIO()
    with patch(
        "apps.webhooks.management.commands.deliver_webhooks.deliver_pending_webhooks",
        return_value=(5, 1),
    ):
        call_command("deliver_webhooks", stdout=out)
    output = out.getvalue()
    assert "6" in output  # total procesados
    assert "5" in output  # entregados
    assert "1" in output  # fallidos
    assert AuditLog.objects.filter(
        event_type=AuditEventType.BATCH_JOB_EXECUTED,
        metadata__job_name="deliver_webhooks",
        metadata__status="COMPLETED",
    ).exists()


@pytest.mark.django_db
def test_deliver_webhooks_custom_batch_size():
    """El argumento --batch-size se pasa correctamente al servicio."""
    out = StringIO()
    with patch(
        "apps.webhooks.management.commands.deliver_webhooks.deliver_pending_webhooks",
        return_value=(0, 0),
    ) as mock_deliver:
        call_command("deliver_webhooks", "--batch-size=25", stdout=out)
    mock_deliver.assert_called_once_with(batch_size=25)
