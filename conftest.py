"""Fixtures globales pytest (descubiertas desde la raíz del proyecto)."""

from __future__ import annotations

import pytest

from apps.authentication.models import UserRole
from tests.factories import (
    AdministradorFactory,
    AlmacenistaFactory,
    LocationFactory,
    ProductFactory,
    UserFactory,
)


@pytest.fixture
def almacenista_user(db):
    return AlmacenistaFactory()


@pytest.fixture
def auxiliar_user(db):
    return UserFactory(role=UserRole.AUXILIAR_DESPACHO)


@pytest.fixture
def administrador_user(db):
    return AdministradorFactory()


@pytest.fixture
def sample_product(db):
    return ProductFactory()


@pytest.fixture
def sample_locations(db):
    return [
        LocationFactory(code="VITRINA", name="Vitrina", is_retail=True),
        LocationFactory(code="BODEGA_1", name="Bodega 1"),
        LocationFactory(code="BODEGA_2", name="Bodega 2"),
    ]
