"""Load testing for ICM Sistema de Inventario.

Usage (requires a running server and `pip install locust`):

    locust -f tests/performance/locustfile.py \
           --headless -H http://localhost:8000 \
           -u 10 -r 2 --run-time 60s --only-summary

This is intentionally NOT part of the pytest suite — run it separately against
a live server before releases or to catch N+1 regressions under realistic load.
"""

from __future__ import annotations

from locust import HttpUser, between, task


class ICMUser(HttpUser):
    wait_time = between(0.5, 2)
    token: str = ""

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/login/",
            json={"username": "almacenista", "password": "testpass123"},
        )
        if r.status_code == 200:
            self.token = r.json().get("access", "")

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

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
