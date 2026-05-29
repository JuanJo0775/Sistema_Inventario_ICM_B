from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.selectors import get_lots_expiring_soon
from apps.movements.services import register_entry
from apps.reports.selectors import rotation_by_category
from tests.factories import CategoryFactory, LotFactory, ProductFactory


@pytest.mark.django_db
def test_rotation_by_category_counts_units(almacenista_user):
    cat_a = CategoryFactory(name="Cat A")
    cat_b = CategoryFactory(name="Cat B")

    p1 = ProductFactory(category=cat_a)
    p2 = ProductFactory(category=cat_b)

    loc_id = None
    # create some movements via services to ensure ledger entries
    # use register_entry to create entries
    from tests.factories import LocationFactory

    loc = LocationFactory()
    loc_id = loc.id

    register_entry(
        almacenista_user,
        p1.id,
        loc_id,
        5,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )
    register_entry(
        almacenista_user,
        p2.id,
        loc_id,
        3,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    start = timezone.now() - timedelta(days=1)
    end = timezone.now() + timedelta(days=1)

    rows = rotation_by_category(start=start, end=end)
    # expect both categories present and counts matching
    mapping = {r["category"]: r["units"] for r in rows}
    assert mapping.get(cat_a.name, 0) >= 5
    assert mapping.get(cat_b.name, 0) >= 3


@pytest.mark.django_db
def test_get_lots_expiring_soon_filters_by_window():
    p = ProductFactory()
    # create near-expiry lot and far-expiry lot
    LotFactory(
        product=p,
        code="NEAR",
        expiration_date=timezone.now().date() + timedelta(days=5),
    )
    LotFactory(
        product=p,
        code="FAR",
        expiration_date=timezone.now().date() + timedelta(days=60),
    )

    q = get_lots_expiring_soon(days=10)
    codes = [l.code for l in q]
    assert "NEAR" in codes
    assert "FAR" not in codes


from apps.reports.selectors import (
    get_discard_operational_summary,
    get_quality_operational_summary,
    get_warehouse_utilization,
)


def test_get_warehouse_utilization_uses_capacity_and_stock(db):
    from apps.inventory.models import Location, StockByLocation
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = Location.objects.create(
        code="UTIL-1",
        name="Utilización 1",
        max_capacity=25,
        is_active=True,
    )
    StockByLocation.objects.create(product=product, location=location, current_stock=5)

    data = get_warehouse_utilization()

    row = next(item for item in data["by_location"] if item["code"] == "UTIL-1")
    assert row["occupied_units"] == 5
    assert row["capacity_units"] == 25
    assert row["utilization_pct"] == 20.0
    assert row["capacity_configured"] is True


def test_get_quality_operational_summary_groups_damage_and_returns(
    almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_DANO,
        product=product,
        quantity=2,
        origin_location=location,
        executed_by=almacenista_user,
    )
    Movement.objects.create(
        movement_type=MovementType.DEVOLUCION,
        product=product,
        quantity=1,
        origin_location=location,
        destination_location=location,
        executed_by=almacenista_user,
    )

    data = get_quality_operational_summary(period_days=30)

    assert data["totals"]["units"] >= 3
    assert data["breakdown"]["incident_units"] >= 3
    assert data["breakdown"]["damage_units"] == 2
    assert data["breakdown"]["return_units"] == 1
    assert data["breakdown"]["quality_index_pct"] == 100.0
    assert any(item["movement_type"] == "SALIDA_DANO" for item in data["by_type"])
    assert any(item["movement_type"] == "DEVOLUCION" for item in data["by_type"])


def test_get_discard_operational_summary_excludes_returns(
    almacenista_user, sample_locations, db
):
    from apps.movements.models import Movement, MovementType
    from tests.factories import ProductFactory

    product = ProductFactory()
    location = sample_locations[0]
    Movement.objects.create(
        movement_type=MovementType.SALIDA_DANO,
        product=product,
        quantity=3,
        origin_location=location,
        executed_by=almacenista_user,
    )
    Movement.objects.create(
        movement_type=MovementType.DEVOLUCION,
        product=product,
        quantity=2,
        origin_location=location,
        destination_location=location,
        executed_by=almacenista_user,
    )

    data = get_discard_operational_summary(period_days=30)

    assert data["totals"]["units"] == 3
    assert any(item["movement_type"] == "SALIDA_DANO" for item in data["by_type"])
    assert all(item["movement_type"] != "DEVOLUCION" for item in data["by_type"])
