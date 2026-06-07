"""Implementaciones Gherkin — RF010 (Reportes y KPIs)."""

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.movements.models import MovementType

from .movements import _MAJEUR_CD

_BOGOTA = ZoneInfo("America/Bogota")

# --- RF-010 -----------------------------------------------------------------


def impl_rf010_s01(authenticated_almacenista_client: APIClient):
    from django.utils import timezone

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = timezone.now()
    url = reverse("reports-sales-summary")
    r = authenticated_almacenista_client.get(
        url, {"start": start.isoformat(), "end": end.isoformat()}
    )
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s02(authenticated_administrador_client: APIClient):
    url = reverse("reports-kpi")
    r = authenticated_administrador_client.get(url)
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s04(authenticated_almacenista_client: APIClient):
    from django.utils import timezone

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = timezone.now()
    url = reverse("reports-movements-history")
    r = authenticated_almacenista_client.get(
        url, {"start": start.isoformat(), "end": end.isoformat()}
    )
    assert r.status_code == status.HTTP_200_OK


def impl_rf010_s05(
    authenticated_almacenista_client: APIClient, almacenista_user, sample_locations, db
):
    from datetime import timedelta

    from django.utils import timezone

    from apps.movements.services import register_entry
    from apps.reports.selectors import get_expiring_products
    from tests.factories import LotFactory, ProductFactory

    product = ProductFactory(requires_expiration=True)
    location = sample_locations[0]
    LotFactory(
        product=product,
        code="L-REP-001",
        expiration_date=timezone.now().date() + timedelta(days=45),
    )
    register_entry(
        almacenista_user,
        product.id,
        location.id,
        4,
        lot_code="L-REP-001",
        lot_expiration_date=timezone.now().date() + timedelta(days=45),
        serial_number="SN-REP-001",
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    url = reverse("reports-expiring")
    r = authenticated_almacenista_client.get(url)
    assert r.status_code == status.HTTP_200_OK
    assert any(
        item["lot_code"] == "L-REP-001" for item in get_expiring_products(days=60)
    )


def impl_rf010_s03(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
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
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-RF010-03",
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    movement = Movement.objects.get(pk=sale.data["id"])
    start = movement.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
    end = movement.created_at
    report = authenticated_almacenista_client.get(
        reverse("reports-movements-history"),
        {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "product_id": str(sample_product.id),
        },
    )
    assert report.status_code == status.HTTP_200_OK
    rows = report.data
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["id", "movement_type", "product_sku", "quantity", "invoice_number"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "id": row["id"],
                "movement_type": row["movement_type"],
                "product_sku": row["product_sku"],
                "quantity": row["quantity"],
                "invoice_number": row.get("invoice_number") or "",
            }
        )
    csv_output = buffer.getvalue()
    assert str(movement.id) in csv_output
    assert sample_product.sku in csv_output


def impl_rf010_s06(
    authenticated_almacenista_client: APIClient, sample_product, sample_locations, db
):
    try:
        from weasyprint import HTML  # noqa: F401
    except Exception:
        pytest.skip("WeasyPrint no disponible en este entorno")

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
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "scanned_code": sample_product.barcode,
            "order_sku": sample_product.sku,
            "serial_number": "SN-RF010-06",
            "customer_data": _MAJEUR_CD,
            "cold_chain_acknowledged": True,
            "electrical_safety_acknowledged": True,
        },
        format="json",
    )
    assert sale.status_code == status.HTTP_201_CREATED
    movement = Movement.objects.get(pk=sale.data["id"])
    history = authenticated_almacenista_client.get(
        reverse("reports-invoices"), {"invoice_number": movement.invoice_number}
    )
    assert history.status_code == status.HTTP_200_OK
    invoice_rows = history.data.get("results", history.data)
    assert any(row["invoice_number"] == movement.invoice_number for row in invoice_rows)
    download = authenticated_almacenista_client.get(
        reverse("movements-dispatch-invoice", kwargs={"pk": movement.id})
    )
    assert download.status_code == status.HTTP_200_OK
    assert "application/pdf" in download["Content-Type"]


def impl_rf010_s07(api_client: APIClient, auxiliar_user):
    from datetime import timezone as dt_timezone

    inner = datetime(2026, 5, 5, 10, 0, 0, tzinfo=_BOGOTA)
    api_client.force_authenticate(user=auxiliar_user)
    start = datetime(2026, 5, 1, tzinfo=dt_timezone.utc)
    end = datetime(2026, 5, 31, tzinfo=dt_timezone.utc)
    url = reverse("reports-sales-summary")
    with patch("django.utils.timezone.now", return_value=inner):
        r = api_client.get(url, {"start": start.isoformat(), "end": end.isoformat()})
    assert r.status_code == status.HTTP_403_FORBIDDEN


IMPLEMENTATIONS: dict[str, object] = {
    "RF010-S01": impl_rf010_s01,
    "RF010-S02": impl_rf010_s02,
    "RF010-S03": impl_rf010_s03,
    "RF010-S04": impl_rf010_s04,
    "RF010-S05": impl_rf010_s05,
    "RF010-S06": impl_rf010_s06,
    "RF010-S07": impl_rf010_s07,
}
