from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.inventory.selectors import get_stock_by_product, search_products_duration_seconds
from apps.movements.services import register_entry
from tests.factories import ManoCategoryFactory, ProductFactory


@pytest.mark.django_db
def test_stock_query_returns_per_location_and_total(almacenista_user, sample_product, sample_locations):
    loc = sample_locations[0]
    register_entry(
        almacenista_user,
        sample_product.id,
        loc.id,
        4,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    data = get_stock_by_product(sample_product.id)
    assert data["total"] == 4
    assert len(data["per_location"]) >= 1


@pytest.mark.django_db
def test_negative_stock_constraint_enforced(sample_product, sample_locations):
    from apps.inventory.models import StockByLocation

    loc = sample_locations[0]
    with pytest.raises(IntegrityError):
        StockByLocation.objects.create(product=sample_product, location=loc, current_stock=-1)


@pytest.mark.django_db
def test_search_products_performance_under_2s(db, almacenista_user):
    cat = ManoCategoryFactory()
    for i in range(50):
        ProductFactory(
            category=cat,
            sku=f"CAN-PERF-{i:04d}",
            name=f"Producto perf {i}",
        )
    _, elapsed = search_products_duration_seconds("perf")
    assert elapsed < 2.0
