"""Load testing for ICM Sistema de Inventario.

Usage (requires a running server and `pip install locust`):

    locust -f tests/performance/locustfile.py \
           --headless -H http://localhost:8000 \
           -u 10 -r 2 --run-time 60s --only-summary

This is intentionally NOT part of the pytest suite — run it separately against
a live server before releases or to catch N+1 regressions under realistic load.

Read tasks (weights 1-4) simulate typical browse traffic.
Write tasks (weight 1) simulate entry registrations; they require at least one
product and location to exist. If none are found on startup, write tasks become
no-ops so the suite still runs against a minimal seed environment.

Two user classes model the two main roles with different access patterns:
- ICMUser (almacenista): full read/write access, no time restriction.
- AuxiliarUser (auxiliar_despacho): read-only browse — no write tasks
  because the time-window restriction would cause 403s outside business hours.
"""

from __future__ import annotations

from locust import HttpUser, between, task


class ICMUser(HttpUser):
    """Simula un almacenista con acceso completo de lectura y escritura."""

    wait_time = between(0.5, 2)
    token: str = ""
    _product_id: str = ""
    _location_id: str = ""

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/login/",
            json={"username": "almacenista", "password": "testpass123"},
        )
        if r.status_code == 200:
            self.token = r.json().get("access", "")

        # Cache first available product and location for write tasks
        pr = self.client.get("/api/v1/catalog/products/", headers=self._auth())
        if pr.status_code == 200:
            results = pr.json().get("results") or pr.json()
            if isinstance(results, list) and results:
                self._product_id = str(results[0].get("id", ""))

        lr = self.client.get("/api/v1/inventory/locations/", headers=self._auth())
        if lr.status_code == 200:
            results = lr.json().get("results") or lr.json()
            if isinstance(results, list) and results:
                self._location_id = str(results[0].get("id", ""))

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    # ── Read tasks ────────────────────────────────────────────────────────────

    @task(4)
    def get_inventory(self):
        self.client.get("/api/v1/inventory/", headers=self._auth())

    @task(3)
    def search_product(self):
        self.client.get(
            "/api/v1/inventory/search/", params={"q": "CAN"}, headers=self._auth()
        )

    @task(2)
    def get_movements(self):
        self.client.get("/api/v1/movements/", headers=self._auth())

    @task(1)
    def get_kpi(self):
        self.client.get("/api/v1/reports/kpi/", headers=self._auth())

    @task(1)
    def get_audit(self):
        self.client.get("/api/v1/audit/", headers=self._auth())

    @task(1)
    def get_dashboard_overview(self):
        self.client.get("/api/v1/dashboard/overview/", headers=self._auth())

    # ── Write tasks ───────────────────────────────────────────────────────────

    @task(1)
    def post_entry(self):
        """Registra una entrada de 1 unidad. No-op si no hay producto/ubicación en seed."""
        if not self._product_id or not self._location_id:
            return
        self.client.post(
            "/api/v1/movements/entries/",
            json={
                "product_id": self._product_id,
                "destination_location_id": self._location_id,
                "quantity": 1,
                "cold_chain_acknowledged": True,
                "electrical_safety_acknowledged": True,
            },
            headers=self._auth(),
            name="/api/v1/movements/entries/ [write]",
        )


class AuxiliarUser(HttpUser):
    """Simula un auxiliar de despacho — solo tareas de lectura (sin restricción horaria)."""

    wait_time = between(1, 3)
    token: str = ""

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/login/",
            json={"username": "auxiliar", "password": "testpass123"},
        )
        if r.status_code == 200:
            self.token = r.json().get("access", "")

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(4)
    def get_inventory(self):
        self.client.get("/api/v1/inventory/", headers=self._auth())

    @task(3)
    def get_movements(self):
        self.client.get("/api/v1/movements/", headers=self._auth())

    @task(2)
    def get_alerts(self):
        self.client.get("/api/v1/alerts/", headers=self._auth())

    @task(1)
    def search_product(self):
        self.client.get(
            "/api/v1/inventory/search/", params={"q": "CAN"}, headers=self._auth()
        )
