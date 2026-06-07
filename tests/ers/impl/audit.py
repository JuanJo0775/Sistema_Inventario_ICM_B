"""Implementaciones Gherkin — RF012 (Log de auditoría e inmutabilidad)."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditEventType, AuditLog
from apps.authentication.models import UserRole
from apps.movements.models import MovementType

_BOGOTA = ZoneInfo("America/Bogota")

# --- RF-012 -----------------------------------------------------------------


def impl_rf012_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations
):
    from tests.ers.impl.movements import impl_rf005_s01

    impl_rf005_s01(authenticated_almacenista_client, sample_product, sample_locations)
    assert AuditLog.objects.filter(event_type=AuditEventType.MOVEMENT_CREATED).exists()


def impl_rf012_s02(api_client: APIClient, almacenista_user):
    url = reverse("token_obtain_pair")
    r = api_client.post(
        url,
        {"username": almacenista_user.username, "password": "testpass123"},
        format="json",
    )
    assert r.status_code == status.HTTP_200_OK
    assert AuditLog.objects.filter(event_type=AuditEventType.LOGIN_SUCCESS).exists()


def impl_rf012_s03(authenticated_almacenista_client: APIClient, almacenista_user, db):
    create = authenticated_almacenista_client.post(
        reverse("auth-users"),
        {
            "username": "rf012_cred_mgr",
            "email": "rf012_cred_mgr@example.com",
            "password": "secreto12345",
            "role": UserRole.AUXILIAR_DESPACHO,
        },
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    created_id = create.data["id"]
    update = authenticated_almacenista_client.patch(
        reverse("auth-user-detail", kwargs={"pk": created_id}),
        {"password": "otraClave123"},
        format="json",
    )
    assert update.status_code == status.HTTP_200_OK
    disable = authenticated_almacenista_client.post(
        reverse("auth-user-disable", kwargs={"pk": created_id})
    )
    assert disable.status_code == status.HTTP_204_NO_CONTENT
    assert AuditLog.objects.filter(event_type=AuditEventType.USER_CREATED).exists()
    assert AuditLog.objects.filter(event_type=AuditEventType.USER_UPDATED).exists()
    assert AuditLog.objects.filter(event_type=AuditEventType.USER_DISABLED).exists()


def impl_rf012_s04(authenticated_almacenista_client: APIClient, sample_locations, db):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement
    from tests.factories import ElectroCategoryFactory, ProductFactory

    cat = ElectroCategoryFactory()
    product = ProductFactory(category=cat, sku="P-1204")
    product.requires_cold_chain = True
    product.save(update_fields=["requires_cold_chain"])
    loc = sample_locations[0]
    StockByLocation.objects.create(product=product, location=loc, current_stock=0)
    entry = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-ACK-1204",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert entry.status_code == status.HTTP_201_CREATED
    movement_id = entry.data["id"]
    assert Movement.objects.filter(pk=movement_id).exists()
    assert AuditLog.objects.filter(
        event_type=AuditEventType.ALERT_ACKNOWLEDGED,
        movement_id=movement_id,
    ).exists()


def impl_rf012_s05(authenticated_almacenista_client: APIClient):
    url = reverse("audit-logs")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf012_s06(api_client: APIClient, auxiliar_user):
    from django.utils import timezone

    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("audit-logs")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.get(url)
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rf012_s07(
    api_client: APIClient, auxiliar_user, sample_product, sample_locations, db
):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement

    a, b = sample_locations[0], sample_locations[1]
    api_client.force_authenticate(user=auxiliar_user)
    StockByLocation.objects.create(product=sample_product, location=a, current_stock=10)
    create = api_client.post(
        reverse("movements-transfers"),
        {
            "product_id": str(sample_product.id),
            "origin_id": str(a.id),
            "destination_id": str(b.id),
            "quantity": 2,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    original = Movement.objects.get(pk=create.data["id"])
    corrected_at = original.created_at + timedelta(minutes=2)
    with patch("django.utils.timezone.now", return_value=corrected_at):
        corr = api_client.post(
            reverse("movements-corrections", kwargs={"pk": original.id}),
            {"origin_id": str(a.id), "destination_id": str(b.id), "quantity": 1},
            format="json",
        )
    assert corr.status_code == status.HTTP_201_CREATED
    assert AuditLog.objects.filter(event_type=AuditEventType.MOVEMENT_CREATED).exists()
    assert AuditLog.objects.filter(
        event_type=AuditEventType.MOVEMENT_CORRECTED
    ).exists()


def impl_rf012_s08(
    authenticated_almacenista_client: APIClient,
    almacenista_user,
    sample_product,
    sample_locations,
    db,
):
    from apps.audit.services import log_event
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    movement = authenticated_almacenista_client.post(
        reverse("movements-entries"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "serial_number": "SN-IMMUT",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert movement.status_code == status.HTTP_201_CREATED
    audit = log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Movimiento de prueba para inmutabilidad",
        user=almacenista_user,
        detail={"scenario": "RF012-S08"},
    )
    response = authenticated_almacenista_client.patch(
        reverse("audit-log-detail", kwargs={"pk": audit.id}),
        {"description": "modificado"},
        format="json",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert AuditLog.objects.filter(
        event_type=AuditEventType.MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD
    ).exists()


IMPLEMENTATIONS: dict[str, object] = {
    "RF012-S01": impl_rf012_s01,
    "RF012-S02": impl_rf012_s02,
    "RF012-S03": impl_rf012_s03,
    "RF012-S04": impl_rf012_s04,
    "RF012-S05": impl_rf012_s05,
    "RF012-S06": impl_rf012_s06,
    "RF012-S07": impl_rf012_s07,
    "RF012-S08": impl_rf012_s08,
}
