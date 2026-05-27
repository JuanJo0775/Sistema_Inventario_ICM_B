from __future__ import annotations

import pytest

from apps.alerts.models import Alert, AlertType
from apps.alerts.services import resolve_alert
from shared.exceptions import UnauthorizedDomainActionError
from tests.factories import LotFactory, ProductFactory


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


@pytest.mark.django_db
def test_sync_expiry_alerts_for_product_creates_lot_alert(db):
    from datetime import timedelta

    from django.utils import timezone

    from apps.alerts.services import sync_expiry_alerts_for_product

    product = ProductFactory(requires_expiration=True)
    lot = LotFactory(
        product=product,
        expiration_date=timezone.now().date() + timedelta(days=60),
        code="L-ALERT",
    )
    sync_expiry_alerts_for_product(product.id)
    alert = Alert.objects.get(product=product, lot=lot, alert_type=AlertType.EXPIRATION_60)
    assert alert.message.startswith("El lote L-ALERT")
