try:
    from locust import HttpUser, between, task
except ImportError:
    HttpUser = None  # type: ignore[assignment,misc]


if HttpUser is not None:

    class HealthCheckUser(HttpUser):
        wait_time = between(1, 2)

        @task(8)
        def health(self):
            self.client.get("/health/")

        @task(2)
        def inventory(self):
            self.client.get("/api/v1/inventory/stock/", params={"page": 1})


if __name__ == "__main__":
    if HttpUser is None:
        print("Error: locust no está instalado. Ejecuta: pip install locust")
        raise SystemExit(1)
    print("Run with: locust -f scripts/perf/locustfile.py --host=http://localhost:8000")
