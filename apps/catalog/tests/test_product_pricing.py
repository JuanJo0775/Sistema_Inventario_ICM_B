"""Tests para el módulo de precios de productos (Fase 1)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import Product, ProductPriceHistory
from apps.catalog.services import update_product_prices
from tests.factories import CategoryFactory, ProductFactory

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def product_with_category(db):
    return ProductFactory()


@pytest.fixture
def almacenista_client(api_client, almacenista_user):
    api_client.force_authenticate(user=almacenista_user)
    return api_client


@pytest.fixture
def auxiliar_client(api_client, auxiliar_user):
    api_client.force_authenticate(user=auxiliar_user)
    return api_client


# ---------------------------------------------------------------------------
# Modelo: campos de precio son nullable por defecto
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_product_price_fields_are_nullable_by_default():
    product = ProductFactory()
    assert product.unit_cost is None
    assert product.sale_price_retail is None
    assert product.sale_price_wholesale is None
    assert product.tax_rate_pct is None
    assert product.currency == "COP"


@pytest.mark.django_db
def test_product_can_store_all_price_fields():
    product = ProductFactory(
        unit_cost=Decimal("5000.0000"),
        sale_price_retail=Decimal("12000.0000"),
        sale_price_wholesale=Decimal("9500.0000"),
        tax_rate_pct=Decimal("19.00"),
        currency="COP",
    )
    product.refresh_from_db()
    assert product.unit_cost == Decimal("5000.0000")
    assert product.sale_price_retail == Decimal("12000.0000")
    assert product.sale_price_wholesale == Decimal("9500.0000")
    assert product.tax_rate_pct == Decimal("19.00")
    assert product.currency == "COP"


# ---------------------------------------------------------------------------
# Servicio: update_product_prices
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_price_creates_history_record(almacenista_user):
    product = ProductFactory()
    updated = update_product_prices(
        almacenista_user,
        product.id,
        sale_price_retail=Decimal("15000.0000"),
    )
    assert updated.sale_price_retail == Decimal("15000.0000")

    history = ProductPriceHistory.objects.filter(
        product=product, field_changed="sale_price_retail"
    )
    assert history.count() == 1
    entry = history.first()
    assert entry.old_value is None
    assert entry.new_value == Decimal("15000.0000")
    assert entry.changed_by == almacenista_user


@pytest.mark.django_db
def test_price_history_tracks_old_and_new_value(almacenista_user):
    product = ProductFactory(sale_price_retail=Decimal("10000.0000"))
    update_product_prices(
        almacenista_user,
        product.id,
        sale_price_retail=Decimal("12000.0000"),
    )
    entry = ProductPriceHistory.objects.get(
        product=product, field_changed="sale_price_retail"
    )
    assert entry.old_value == Decimal("10000.0000")
    assert entry.new_value == Decimal("12000.0000")


@pytest.mark.django_db
def test_update_multiple_price_fields_creates_multiple_history_records(
    almacenista_user,
):
    product = ProductFactory()
    update_product_prices(
        almacenista_user,
        product.id,
        unit_cost=Decimal("5000.0000"),
        sale_price_retail=Decimal("12000.0000"),
        sale_price_wholesale=Decimal("9000.0000"),
    )
    assert ProductPriceHistory.objects.filter(product=product).count() == 3


@pytest.mark.django_db
def test_update_with_same_value_does_not_create_history(almacenista_user):
    product = ProductFactory(sale_price_retail=Decimal("10000.0000"))
    update_product_prices(
        almacenista_user,
        product.id,
        sale_price_retail=Decimal("10000.0000"),
    )
    assert ProductPriceHistory.objects.filter(product=product).count() == 0


@pytest.mark.django_db
def test_update_no_fields_returns_product_unchanged(almacenista_user):
    product = ProductFactory(sale_price_retail=Decimal("10000.0000"))
    result = update_product_prices(almacenista_user, product.id)
    assert result.sale_price_retail == Decimal("10000.0000")
    assert ProductPriceHistory.objects.filter(product=product).count() == 0


@pytest.mark.django_db
def test_wholesale_price_can_differ_from_retail(almacenista_user):
    product = ProductFactory()
    update_product_prices(
        almacenista_user,
        product.id,
        sale_price_retail=Decimal("20000.0000"),
        sale_price_wholesale=Decimal("15000.0000"),
    )
    product.refresh_from_db()
    assert product.sale_price_wholesale < product.sale_price_retail


@pytest.mark.django_db
def test_update_prices_requires_almacenista_role(auxiliar_user):
    from shared.exceptions import UnauthorizedCredentialManagementError

    product = ProductFactory()
    with pytest.raises(UnauthorizedCredentialManagementError):
        update_product_prices(
            auxiliar_user, product.id, sale_price_retail=Decimal("9000.0000")
        )


# ---------------------------------------------------------------------------
# API: PATCH /catalog/products/<id>/prices/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_api_patch_prices_updates_product(almacenista_client):
    product = ProductFactory()
    url = reverse("catalog-product-prices", kwargs={"pk": product.id})
    resp = almacenista_client.patch(
        url,
        {"sale_price_retail": "12000.0000", "unit_cost": "5000.0000"},
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sale_price_retail"] == "12000.0000"
    assert data["unit_cost"] == "5000.0000"


@pytest.mark.django_db
def test_api_patch_prices_rejects_auxiliar(auxiliar_client):
    product = ProductFactory()
    url = reverse("catalog-product-prices", kwargs={"pk": product.id})
    resp = auxiliar_client.patch(
        url, {"sale_price_retail": "12000.0000"}, format="json"
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_patch_prices_rejects_negative_price(almacenista_client):
    product = ProductFactory()
    url = reverse("catalog-product-prices", kwargs={"pk": product.id})
    resp = almacenista_client.patch(url, {"sale_price_retail": "-100"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_patch_prices_rejects_tax_over_100(almacenista_client):
    product = ProductFactory()
    url = reverse("catalog-product-prices", kwargs={"pk": product.id})
    resp = almacenista_client.patch(url, {"tax_rate_pct": "150"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_get_price_history_returns_list(almacenista_client, almacenista_user):
    product = ProductFactory()
    update_product_prices(
        almacenista_user, product.id, sale_price_retail=Decimal("5000.0000")
    )
    url = reverse("catalog-product-prices", kwargs={"pk": product.id})
    resp = almacenista_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["field_changed"] == "sale_price_retail"


@pytest.mark.django_db
def test_product_serializer_exposes_price_fields(almacenista_client):
    product = ProductFactory(
        sale_price_retail=Decimal("8000.0000"),
        currency="COP",
    )
    url = reverse("catalog-product-detail", kwargs={"pk": product.id})
    resp = almacenista_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert "sale_price_retail" in data
    assert data["sale_price_retail"] == "8000.0000"
    assert data["currency"] == "COP"
