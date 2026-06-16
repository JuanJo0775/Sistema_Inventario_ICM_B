"""Tests para scripts/perf/locustfile.py — verifica importación y estructura básica.

Requiere locust (development dependency). Los tests se skippean si no está instalado.
"""

from __future__ import annotations

import pytest

pytest.importorskip("locust")

from scripts.perf.locustfile import HealthCheckUser  # noqa: E402


class TestHealthCheckUser:
    """Verifica que la clase HealthCheckUser esté bien estructurada."""

    def test_imports_cleanly(self):
        assert HealthCheckUser is not None

    def test_tasks_defined(self):
        tasks = HealthCheckUser.tasks
        assert tasks is not None
        assert len(tasks) >= 2

    def test_has_wait_time(self):
        assert HealthCheckUser.wait_time is not None
