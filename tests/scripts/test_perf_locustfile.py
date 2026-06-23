"""Tests de estructura para los locustfiles de rendimiento.

Verifica que los user classes de carga estén correctamente definidos
sin levantar un servidor real. Se saltean si locust no está instalado.
"""
from __future__ import annotations

import pytest

pytest.importorskip("locust")

from scripts.perf.locustfile import HealthCheckUser  # noqa: E402
from tests.performance.locustfile import (  # noqa: E402
    AdminUser,
    AuxiliarUser,
    ICMUser,
)


class TestHealthCheckUser:
    """Verifica que HealthCheckUser (scripts/perf) esté bien estructurado."""

    def test_imports_cleanly(self):
        assert HealthCheckUser is not None

    def test_tasks_defined(self):
        assert HealthCheckUser.tasks is not None
        assert len(HealthCheckUser.tasks) >= 2

    def test_has_wait_time(self):
        assert HealthCheckUser.wait_time is not None


class TestICMUser:
    """ICMUser (almacenista) — clase de carga principal con lectura y escritura."""

    def test_imports_cleanly(self):
        assert ICMUser is not None

    def test_has_wait_time(self):
        assert ICMUser.wait_time is not None

    def test_has_tasks(self):
        assert ICMUser.tasks is not None
        assert len(ICMUser.tasks) >= 5

    def test_has_on_start(self):
        assert hasattr(ICMUser, "on_start")

    def test_has_token_attribute(self):
        assert hasattr(ICMUser, "token")

    def test_has_auth_helper(self):
        assert hasattr(ICMUser, "_auth")

    def test_has_create_product_helper(self):
        assert hasattr(ICMUser, "_create_product")

    def test_has_create_supplier_helper(self):
        assert hasattr(ICMUser, "_create_supplier")


class TestAuxiliarUser:
    """AuxiliarUser (auxiliar_despacho) — solo lectura."""

    def test_imports_cleanly(self):
        assert AuxiliarUser is not None

    def test_has_wait_time(self):
        assert AuxiliarUser.wait_time is not None

    def test_has_tasks(self):
        assert AuxiliarUser.tasks is not None
        assert len(AuxiliarUser.tasks) >= 4

    def test_has_on_start(self):
        assert hasattr(AuxiliarUser, "on_start")

    def test_has_auth_helper(self):
        assert hasattr(AuxiliarUser, "_auth")


class TestAdminUser:
    """AdminUser (administrador) — solo lectura de reportes y auditoría."""

    def test_imports_cleanly(self):
        assert AdminUser is not None

    def test_has_wait_time(self):
        assert AdminUser.wait_time is not None

    def test_has_tasks(self):
        assert AdminUser.tasks is not None
        assert len(AdminUser.tasks) >= 4

    def test_has_on_start(self):
        assert hasattr(AdminUser, "on_start")

    def test_has_auth_helper(self):
        assert hasattr(AdminUser, "_auth")

    def test_wait_time_is_callable(self):
        """wait_time debe ser un callable devuelto por between()."""
        assert callable(AdminUser.wait_time)
