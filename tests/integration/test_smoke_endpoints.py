from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_reports_kpi_endpoint_available(authenticated_almacenista_client):
    r = authenticated_almacenista_client.get("/api/v1/reports/kpi/")
    assert r.status_code in (200, 204)


@pytest.mark.django_db
def test_reports_inventory_summary_endpoint(authenticated_almacenista_client):
    r = authenticated_almacenista_client.get("/api/v1/reports/inventory/summary/")
    assert r.status_code in (200, 204)
