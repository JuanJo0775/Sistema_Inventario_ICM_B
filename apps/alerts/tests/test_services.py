from __future__ import annotations

import pytest

from apps.alerts.models import Alert, AlertType
from apps.alerts.services import resolve_alert
from shared.exceptions import UnauthorizedDomainActionError
from tests.factories import ProductFactory


@pytest.mark.django_db
def test_resolve_alert_almacenista(almacenista_user):
    p = ProductFactory()
    alert = Alert.objects.create(
        product=p,
        alert_type=AlertType.LOW_STOCK,
        message="test",
    )
    out = resolve_alert(almacenista_user, alert.id)
    assert out.is_resolved
    assert out.resolved_by_id == almacenista_user.id


@pytest.mark.django_db
def test_resolve_alert_rejects_auxiliar(auxiliar_user):
    p = ProductFactory()
    alert = Alert.objects.create(
        product=p,
        alert_type=AlertType.LOW_STOCK,
        message="test",
    )
    with pytest.raises(UnauthorizedDomainActionError):
        resolve_alert(auxiliar_user, alert.id)
