"""Implementaciones Gherkin — RNF003-RNF006 (Requisitos no funcionales)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import UserRole

_BOGOTA = ZoneInfo("America/Bogota")

# --- RNF-003 (Seguridad e integridad de datos) --------------------------------


def impl_rnf003_s01(api_client: APIClient):
    import importlib
    import os
    import sys
    from unittest.mock import patch

    sys.modules.pop("config.settings.production", None)
    db_env = {
        "DB_NAME": "ci_test",
        "DB_USER": "ci_user",
        "DB_PASSWORD": "ci_pass",
        "DB_HOST": "localhost",
    }
    with patch.dict(os.environ, db_env):
        production_settings = importlib.import_module("config.settings.production")

    assert production_settings.SECURE_SSL_REDIRECT is True
    assert production_settings.SESSION_COOKIE_SECURE is True
    assert production_settings.CSRF_COOKIE_SECURE is True
    assert (
        "django.middleware.security.SecurityMiddleware"
        in production_settings.MIDDLEWARE
    )


def impl_rnf003_s02(api_client: APIClient, auxiliar_user):
    from django.utils import timezone

    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    api_client.force_authenticate(user=auxiliar_user)
    url = reverse("auth-users")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.post(
            url,
            {
                "username": "hack_aux",
                "email": "hack_aux@example.com",
                "password": "secreto12345",
                "role": UserRole.ALMACENISTA,
            },
            format="json",
        )
    assert r.status_code == status.HTTP_403_FORBIDDEN


def impl_rnf003_s03(almacenista_user):
    assert not almacenista_user.password.startswith("plaintext")
    assert len(almacenista_user.password) > 20


def impl_rnf003_s04(
    authenticated_almacenista_client: APIClient,
    almacenista_user,
    sample_product,
    sample_locations,
    db,
):
    from apps.audit.models import AuditEventType, AuditLog
    from apps.inventory.models import StockByLocation
    from apps.movements.models import Movement

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    sale = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": "SALIDA_VENTA_MENOR",
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-IMM-0034",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    movement = Movement.objects.get(pk=sale.data["id"])
    response = authenticated_almacenista_client.patch(
        reverse("movements-detail", kwargs={"pk": movement.id}),
        {"quantity": 2},
        format="json",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert AuditLog.objects.filter(
        event_type=AuditEventType.MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD
    ).exists()


# --- RNF-004 (Rendimiento de consultas y operaciones) -------------------------


def impl_rnf004_s01(
    authenticated_almacenista_client: APIClient,
    sample_product,
    django_assert_num_queries,
):
    url = reverse("inventory-product-stock", kwargs={"product_id": sample_product.id})
    with django_assert_num_queries(3):
        r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rnf004_s02(
    authenticated_almacenista_client: APIClient,
    sample_product,
    sample_locations,
    db,
    django_assert_num_queries,
):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    with django_assert_num_queries(21):
        r = authenticated_almacenista_client.post(
            reverse("movements-entries"),
            {
                "product_id": str(sample_product.id),
                "location_id": str(loc.id),
                "quantity": 1,
                "serial_number": "SN-RNF004-02",
                "cold_chain_acknowledged": True,
                "electrical_safety_acknowledged": True,
            },
            format="json",
        )
    assert r.status_code == status.HTTP_201_CREATED


def impl_rnf004_s03(
    authenticated_almacenista_client: APIClient,
    authenticated_administrador_client: APIClient,
    auxiliar_user,
    sample_product,
    sample_locations,
    db,
    django_assert_num_queries,
):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    aux_client = APIClient()
    aux_client.force_authenticate(user=auxiliar_user)

    with django_assert_num_queries(2):
        response_1 = authenticated_almacenista_client.get(reverse("inventory-full"))

    with django_assert_num_queries(4):
        response_2 = authenticated_administrador_client.get(reverse("reports-kpi"))

    with django_assert_num_queries(1):
        response_3 = aux_client.get(
            reverse("inventory-search"), {"q": sample_product.sku[:3]}
        )

    assert response_1.status_code == status.HTTP_200_OK
    assert response_2.status_code == status.HTTP_200_OK
    assert response_3.status_code == status.HTTP_200_OK


# --- RNF-005 (Mantenibilidad y estándares técnicos) ---------------------------


def impl_rnf005_s01(api_client: APIClient):
    """Contrato OpenAPI: el esquema es accesible sin autenticación."""
    url = reverse("schema")
    r = api_client.get(url)
    assert r.status_code == status.HTTP_200_OK
    assert r.headers.get("Content-Type", "").startswith("application/vnd.oai.openapi")


def impl_rnf005_s02(api_client: APIClient):
    schema = api_client.get(reverse("schema"), {"format": "json"})
    assert schema.status_code == status.HTTP_200_OK
    data = schema.json()
    paths = data["paths"]
    expected = [
        "/api/v1/auth/users/",
        "/api/v1/movements/entries/",
        "/api/v1/movements/dispatches/",
        "/api/v1/movements/transfers/",
        "/api/v1/reports/sales/summary/",
        "/api/v1/alerts/",
        "/api/v1/audit/",
    ]
    for path in expected:
        assert path in paths


def impl_rnf005_s03(db):
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for app in ("movements", "catalog", "inventory", "purchasing"):
        assert (
            root / "apps" / app / "services.py"
        ).exists(), f"Falta services.py en {app}"
        assert (
            root / "apps" / app / "selectors.py"
        ).exists(), f"Falta selectors.py en {app}"


# --- RNF-006 (Cumplimiento legal — Ley 1581/2012) ----------------------------


def impl_rnf006_s01(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    """Ley 1581: venta mayor sin consentimiento explícito → error de dominio."""
    loc = sample_locations[0]
    from apps.inventory.models import StockByLocation
    from apps.movements.models import MovementType

    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    _MAJEUR_NO_CONSENT = {
        "customer_name": "Mayorista SA",
        "customer_email": "mayor@example.com",
        "customer_phone": "3001112233",
        "customer_address": "Carrera 1 # 2-3",
    }
    url = reverse("movements-dispatches")
    r = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-1581",
            "customer_data": _MAJEUR_NO_CONSENT,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def impl_rnf006_s02(
    api_client: APIClient, auxiliar_user, sample_product, sample_locations, db
):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=5
    )
    api_client.force_authenticate(user=auxiliar_user)
    response = api_client.get(reverse("reports-invoices"))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def impl_rnf006_s03(
    authenticated_almacenista_client: APIClient,
    sample_product,
    sample_locations,
    db,
):
    from apps.inventory.models import StockByLocation
    from apps.movements.models import MovementType

    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    _without_consent = {
        "customer_name": "Mayorista SA",
        "customer_email": "mayor@example.com",
        "customer_phone": "3001112233",
        "customer_address": "Carrera 1 # 2-3",
    }
    r = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 1,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "customer_data": _without_consent,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


IMPLEMENTATIONS: dict[str, object] = {
    "RNF003-S01": impl_rnf003_s01,
    "RNF003-S02": impl_rnf003_s02,
    "RNF003-S03": impl_rnf003_s03,
    "RNF003-S04": impl_rnf003_s04,
    "RNF004-S01": impl_rnf004_s01,
    "RNF004-S02": impl_rnf004_s02,
    "RNF004-S03": impl_rnf004_s03,
    "RNF005-S01": impl_rnf005_s01,
    "RNF005-S02": impl_rnf005_s02,
    "RNF005-S03": impl_rnf005_s03,
    "RNF006-S01": impl_rnf006_s01,
    "RNF006-S02": impl_rnf006_s02,
    "RNF006-S03": impl_rnf006_s03,
}
