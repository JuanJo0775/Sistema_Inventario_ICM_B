from locust import HttpUser, task, between
import os


class HealthCheckUser(HttpUser):
    wait_time = between(1, 2)

    @task(8)
    def health(self):
        self.client.get("/health/")

    @task(2)
    def inventory(self):
        # GET inventory endpoint - may require auth depending on deployment
        self.client.get("/api/v1/inventory/stock/", params={"page": 1})


if __name__ == "__main__":
    print("Run with: locust -f scripts/perf/locustfile.py --host=http://localhost:8000")
