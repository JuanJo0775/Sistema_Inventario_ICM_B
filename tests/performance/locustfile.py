"""Load testing for ICM Sistema de Inventario.

Usage (requires a running server and `pip install locust`):

    locust -f tests/performance/locustfile.py \
           --headless -H http://localhost:8000 \
           -u 10 -r 2 --run-time 60s --only-summary

Three user classes model the system roles:
- ICMUser (almacenista, weight=5): reads across all modules + writes (entries, dispatches,
  transfers, adjustments, returns, billing, product creation, purchase orders).
  28 tasks (21 read + 7 write).
- AuxiliarUser (auxiliar_despacho): read-only browse across permitted modules.
- AdminUser (administrador): read-only access to reports, KPI, audit, and billing.

Write tasks are no-ops when no product/location/supplier is cached.
In CI the seeds create default locations — products and suppliers are created
on demand by ICMUser during `on_start` so every user has data to work with.
"""

from __future__ import annotations

import itertools

from locust import HttpUser, between, task


def _safe_results(data):
    """Extract result list from a paginated API response or plain list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("results") or data
    return []


class ICMUser(HttpUser):
    """Simula un almacenista con acceso completo de lectura y escritura.

    weight=5 refleja que el almacenista es el rol principal del sistema:
    el mayor número de usuarios concurrentes corresponde a este perfil.
    """

    weight = 5
    wait_time = between(0.5, 2)
    token: str = ""
    _product_id: str = ""
    _location_a: str = ""
    _location_b: str = ""
    _supplier_id: str = ""
    _category_id: str = ""

    _counter = itertools.count(1)

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/login/",
            json={"username": "almacenista", "password": "testpass123"},
        )
        if r.status_code == 200:
            data = r.json()
            self.token = data.get("access", "") if isinstance(data, dict) else ""

        # Cache locations (seeded by migration 0003)
        lr = self.client.get("/api/v1/inventory/locations/", headers=self._auth())
        if lr.status_code == 200:
            locs = _safe_results(lr.json())
            if len(locs) >= 2:
                self._location_a = str(locs[0].get("id", ""))
                self._location_b = str(locs[1].get("id", ""))

        # Cache first category
        cr = self.client.get("/api/v1/catalog/categories/", headers=self._auth())
        if cr.status_code == 200:
            cats = _safe_results(cr.json())
            if cats:
                self._category_id = str(cats[0].get("id", ""))

        # Cache or create a product
        pr = self.client.get("/api/v1/catalog/products/", headers=self._auth())
        if pr.status_code == 200:
            prods = _safe_results(pr.json())
            if prods:
                self._product_id = str(prods[0].get("id", ""))
        if not self._product_id:
            self._create_product()

        # Cache or create a supplier
        sr = self.client.get("/api/v1/purchasing/suppliers/", headers=self._auth())
        if sr.status_code == 200:
            sups = _safe_results(sr.json())
            if sups:
                self._supplier_id = str(sups[0].get("id", ""))
        if not self._supplier_id:
            self._create_supplier()

    def _create_product(self):
        if not self._category_id:
            return
        n = next(self._counter)
        r = self.client.post(
            "/api/v1/catalog/products/",
            json={
                "sku": f"LTP-{n:04d}",
                "name": f"Load Test Product {n}",
                "category_id": self._category_id,
                "brand": "LoadTest",
                "reorder_point": 5,
            },
            headers=self._auth(),
            name="/api/v1/catalog/products/ [create]",
        )
        if r.status_code == 201:
            data = r.json()
            self._product_id = str(data.get("id", ""))

    def _create_supplier(self):
        n = next(self._counter)
        r = self.client.post(
            "/api/v1/purchasing/suppliers/",
            json={
                "nombre_comercial": f"Load Test Supplier {n}",
                "pais": "CO",
                "correo": "test@localtest.com",
                "telefono": "0000000000",
                "direccion": "Test Address",
            },
            headers=self._auth(),
            name="/api/v1/purchasing/suppliers/ [create]",
        )
        if r.status_code in (201, 200):
            data = r.json()
            self._supplier_id = str(data.get("id", ""))

    # ── Read: Inventory ──────────────────────────────────────────────────────

    @task(4)
    def get_inventory(self):
        self.client.get("/api/v1/inventory/", headers=self._auth())

    @task(2)
    def search_product(self):
        self.client.get(
            "/api/v1/inventory/search/", params={"q": "CAN"}, headers=self._auth()
        )

    @task(2)
    def get_stock_by_product(self):
        if not self._product_id:
            return
        self.client.get(
            f"/api/v1/inventory/stock/product/{self._product_id}/",
            headers=self._auth(),
            name="/api/v1/inventory/stock/product/ [id]",
        )

    @task(1)
    def get_locations(self):
        self.client.get("/api/v1/inventory/locations/", headers=self._auth())

    # ── Read: Movements ──────────────────────────────────────────────────────

    @task(3)
    def get_movements(self):
        self.client.get("/api/v1/movements/", headers=self._auth())

    @task(1)
    def get_entries(self):
        self.client.get("/api/v1/movements/entries/", headers=self._auth())

    @task(1)
    def get_dispatches(self):
        self.client.get("/api/v1/movements/dispatches/", headers=self._auth())

    @task(1)
    def get_transfers(self):
        self.client.get("/api/v1/movements/transfers/", headers=self._auth())

    # ── Read: Catalog ────────────────────────────────────────────────────────

    @task(2)
    def get_catalog_products(self):
        self.client.get("/api/v1/catalog/products/", headers=self._auth())

    @task(1)
    def get_categories(self):
        self.client.get("/api/v1/catalog/categories/", headers=self._auth())

    # ── Read: Alerts, Dashboard, Audit, Reports ──────────────────────────────

    @task(2)
    def get_alerts(self):
        self.client.get("/api/v1/alerts/", headers=self._auth())

    @task(1)
    def get_alerts_poll(self):
        self.client.get("/api/v1/alerts/poll/", headers=self._auth())

    @task(1)
    def get_dashboard_overview(self):
        self.client.get("/api/v1/dashboard/overview/", headers=self._auth())

    @task(1)
    def get_audit(self):
        self.client.get("/api/v1/audit/", headers=self._auth())

    @task(1)
    def get_kpi(self):
        self.client.get("/api/v1/reports/kpi/", headers=self._auth())

    @task(1)
    def get_inventory_summary(self):
        self.client.get("/api/v1/reports/inventory/summary/", headers=self._auth())

    # ── Read: Purchasing ─────────────────────────────────────────────────────

    @task(1)
    def get_suppliers(self):
        self.client.get("/api/v1/purchasing/suppliers/", headers=self._auth())

    @task(1)
    def get_purchase_orders(self):
        self.client.get("/api/v1/purchasing/purchase-orders/", headers=self._auth())

    # ── Write: Movements ─────────────────────────────────────────────────────

    @task(1)
    def post_entry(self):
        if not self._product_id or not self._location_a:
            return
        self.client.post(
            "/api/v1/movements/entries/",
            json={
                "product_id": self._product_id,
                "location_id": self._location_a,
                "quantity": 1,
                "cold_chain_acknowledged": True,
                "electrical_safety_acknowledged": True,
            },
            headers=self._auth(),
            name="/api/v1/movements/entries/ [write]",
        )

    @task(1)
    def post_dispatch(self):
        if not self._product_id or not self._location_a:
            return
        self.client.post(
            "/api/v1/movements/dispatches/",
            json={
                "product_id": self._product_id,
                "location_id": self._location_a,
                "quantity": 1,
                "movement_type": "despacho_normal",
                "order_sku": f"ORD-{next(self._counter):04d}",
                "scanned_code": f"ORD-{next(self._counter):04d}",
                "cold_chain_acknowledged": True,
                "electrical_safety_acknowledged": True,
                "privacy_notice_acknowledged": True,
            },
            headers=self._auth(),
            name="/api/v1/movements/dispatches/ [write]",
        )

    @task(1)
    def post_transfer(self):
        if not self._product_id or not self._location_a or not self._location_b:
            return
        self.client.post(
            "/api/v1/movements/transfers/",
            json={
                "product_id": self._product_id,
                "origin_id": self._location_a,
                "destination_id": self._location_b,
                "quantity": 1,
            },
            headers=self._auth(),
            name="/api/v1/movements/transfers/ [write]",
        )

    @task(1)
    def post_adjustment(self):
        if not self._product_id or not self._location_a:
            return
        self.client.post(
            "/api/v1/movements/adjustments/",
            json={
                "product_id": self._product_id,
                "location_id": self._location_a,
                "new_quantity": 5,
                "justification": "Load test adjustment",
            },
            headers=self._auth(),
            name="/api/v1/movements/adjustments/ [write]",
        )

    @task(1)
    def post_return(self):
        if not self._product_id or not self._location_a:
            return
        self.client.post(
            "/api/v1/movements/returns/",
            json={
                "product_id": self._product_id,
                "location_id": self._location_a,
                "quantity": 1,
            },
            headers=self._auth(),
            name="/api/v1/movements/returns/ [write]",
        )

    # ── Write: Purchasing ────────────────────────────────────────────────────

    @task(1)
    def post_purchase_order(self):
        if not self._supplier_id or not self._product_id:
            return
        self.client.post(
            "/api/v1/purchasing/purchase-orders/",
            json={
                "supplier_id": self._supplier_id,
                "items": [{"product": self._product_id, "quantity_ordered": 5}],
            },
            headers=self._auth(),
            name="/api/v1/purchasing/purchase-orders/ [write]",
        )

    # ── Read: Billing ────────────────────────────────────────────────────────

    @task(1)
    def get_billing_invoices(self):
        self.client.get("/api/v1/billing/invoices/", headers=self._auth())

    @task(1)
    def get_billing_stats(self):
        self.client.get("/api/v1/billing/invoices/stats/", headers=self._auth())

    # ── Read: Storage ────────────────────────────────────────────────────────

    @task(1)
    def get_storage_types(self):
        self.client.get("/api/v1/inventory/storage-types/", headers=self._auth())

    @task(1)
    def get_storage_templates(self):
        self.client.get("/api/v1/inventory/storage-templates/", headers=self._auth())


class AuxiliarUser(HttpUser):
    """Simula un auxiliar de despacho — solo tareas de lectura."""

    weight = 3
    wait_time = between(1, 3)
    token: str = ""

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/login/",
            json={"username": "auxiliar", "password": "testpass123"},
        )
        if r.status_code == 200:
            data = r.json()
            self.token = data.get("access", "") if isinstance(data, dict) else ""

    # ── Read tasks ───────────────────────────────────────────────────────────

    @task(4)
    def get_inventory(self):
        self.client.get("/api/v1/inventory/", headers=self._auth())

    @task(3)
    def get_movements(self):
        self.client.get("/api/v1/movements/", headers=self._auth())

    @task(3)
    def search_product(self):
        self.client.get(
            "/api/v1/inventory/search/", params={"q": "CAN"}, headers=self._auth()
        )

    @task(2)
    def get_entries(self):
        self.client.get("/api/v1/movements/entries/", headers=self._auth())

    @task(2)
    def get_dispatches(self):
        self.client.get("/api/v1/movements/dispatches/", headers=self._auth())

    @task(1)
    def get_transfers(self):
        self.client.get("/api/v1/movements/transfers/", headers=self._auth())

    @task(1)
    def get_locations(self):
        self.client.get("/api/v1/inventory/locations/", headers=self._auth())

    @task(1)
    def get_alerts_poll(self):
        self.client.get("/api/v1/alerts/poll/", headers=self._auth())


class AdminUser(HttpUser):
    """Simula un administrador — solo lectura de reportes, KPI, auditoría y facturación."""

    weight = 2
    wait_time = between(2, 5)
    token: str = ""

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/login/",
            json={"username": "administrador", "password": "testpass123"},
        )
        if r.status_code == 200:
            data = r.json()
            self.token = data.get("access", "") if isinstance(data, dict) else ""

    @task(4)
    def get_kpi(self):
        self.client.get("/api/v1/reports/kpi/", headers=self._auth())

    @task(3)
    def get_inventory_summary(self):
        self.client.get("/api/v1/reports/inventory/summary/", headers=self._auth())

    @task(2)
    def get_audit_logs(self):
        self.client.get("/api/v1/audit/", headers=self._auth())

    @task(2)
    def get_billing_stats(self):
        self.client.get("/api/v1/billing/invoices/stats/", headers=self._auth())

    @task(2)
    def get_movements_summary(self):
        self.client.get("/api/v1/reports/movements/summary/", headers=self._auth())

    @task(1)
    def get_inventory_full(self):
        self.client.get("/api/v1/inventory/", headers=self._auth())
