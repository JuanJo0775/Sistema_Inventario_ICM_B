"""
Garantía de no-regresión: el módulo de precios es completamente transparente
para el flujo de trabajo actual del frontend.

Todos los tests aquí usan exclusivamente la API pública sin ningún campo
de precio en las requests — exactamente como lo haría un frontend que aún
no implementa la funcionalidad de precios.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status

from apps.catalog.models import ProductCombo, ComboItem
from apps.movements.models import Movement, MovementType
from apps.movements.services import register_entry
from tests.factories import LocationFactory, ProductFactory

# ---------------------------------------------------------------------------
# Despacho sin precios configurados en el producto
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dispatch_api_works_without_any_price_fields(
    authenticated_almacenista_client, almacenista_user, sample_locations
):
    """POST /dispatches/ sin discount_pct ni ningún campo de precio → 201."""
    product = ProductFactory()  # sin precios
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 10)

    url = reverse("movements-dispatches")
    resp = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(product.id),
            "location_id": str(loc.id),
            "quantity": 3,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    # Los campos de precio existen en la respuesta pero son null — no bloquean
    assert data["unit_price"] is None
    assert data["total_amount"] is None
    assert data["customer_snapshot"] is None
    assert data["quantity"] == 3


@pytest.mark.django_db
def test_dispatch_wholesale_without_prices_still_works(
    authenticated_almacenista_client, almacenista_user, sample_locations
):
    """Venta mayor sin precio configurado: flujo completo sin bloqueo."""
    product = ProductFactory()
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 10)

    url = reverse("movements-dispatches")
    resp = authenticated_almacenista_client.post(
        url,
        {
            "product_id": str(product.id),
            "location_id": str(loc.id),
            "quantity": 2,
            "movement_type": MovementType.SALIDA_VENTA_MAYOR,
            "customer_data": {
                "customer_name": "Test SA",
                "customer_email": "test@test.com",
                "customer_phone": "3001234567",
                "customer_address": "Calle 1",
                "privacy_notice_acknowledged": True,
            },
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_movement_list_response_is_backward_compatible(
    authenticated_almacenista_client, almacenista_user, sample_locations
):
    """GET /movements/ devuelve los campos de precio como null — sin ruptura de contrato."""
    product = ProductFactory()
    loc = sample_locations[1]
    register_entry(almacenista_user, product.id, loc.id, 5)

    from apps.movements.services import register_dispatch

    register_dispatch(
        almacenista_user, product.id, loc.id, 1, MovementType.SALIDA_VENTA_MENOR
    )

    url = reverse("movements-dispatches")
    resp = authenticated_almacenista_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    results = resp.json()["results"]
    assert len(results) >= 1
    # Los campos de precio están en la respuesta pero son null — no rompen nada
    assert "unit_price" in results[0]
    assert results[0]["unit_price"] is None


# ---------------------------------------------------------------------------
# Catálogo: product GET/POST/PATCH no requiere precios
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_product_create_without_prices(authenticated_almacenista_client):
    """POST /catalog/products/ sin campos de precio → 201, precios null en respuesta."""
    from tests.factories import CategoryFactory

    cat = CategoryFactory()
    url = reverse("catalog-products")
    resp = authenticated_almacenista_client.post(
        url,
        {"sku": "TST-0001", "name": "Producto sin precio", "category_id": str(cat.id)},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["unit_cost"] is None
    assert data["sale_price_retail"] is None
    assert data["sale_price_wholesale"] is None
    assert data["tax_rate_pct"] is None
    assert data["currency"] == "COP"


@pytest.mark.django_db
def test_product_patch_without_price_fields_unchanged(authenticated_almacenista_client):
    """PATCH /catalog/products/<id>/ sin campos de precio → precios se mantienen intactos."""
    from decimal import Decimal
    from apps.catalog.services import update_product_prices
    from tests.factories import AlmacenistaFactory

    user = AlmacenistaFactory()
    product = ProductFactory(sale_price_retail=Decimal("5000.0000"))
    update_product_prices(user, product.id, sale_price_retail=Decimal("5000.0000"))

    url = reverse("catalog-product-detail", kwargs={"pk": product.id})
    resp = authenticated_almacenista_client.patch(
        url, {"name": "Nuevo nombre"}, format="json"
    )
    assert resp.status_code == status.HTTP_200_OK
    product.refresh_from_db()
    # El precio no fue tocado por el PATCH general
    assert product.sale_price_retail == Decimal("5000.0000")


@pytest.mark.django_db
def test_product_get_exposes_prices_as_nullable_info(authenticated_almacenista_client):
    """GET /catalog/products/<id>/ retorna campos de precio como info null — no bloquea."""
    product = ProductFactory()
    url = reverse("catalog-product-detail", kwargs={"pk": product.id})
    resp = authenticated_almacenista_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    for field in (
        "unit_cost",
        "sale_price_retail",
        "sale_price_wholesale",
        "tax_rate_pct",
    ):
        assert field in data, f"Campo {field} debería estar en la respuesta"
        assert (
            data[field] is None
        ), f"Campo {field} debería ser null para productos sin precio"
    assert data["currency"] == "COP"


# ---------------------------------------------------------------------------
# Combos: create/update sin precios
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_combo_create_without_price_strategy_uses_derived(
    authenticated_almacenista_client,
):
    """POST /catalog/combos/ sin price_strategy → usa 'derived' por defecto."""
    product = ProductFactory(sku="CMB-NOPR1")
    url = reverse("catalog-combos")
    resp = authenticated_almacenista_client.post(
        url,
        {
            "name": "Kit sin precio",
            "sku": "KIT-0099",
            "items": [{"product_id": str(product.id), "quantity": 1}],
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["price_strategy"] == "derived"
    assert data["fixed_price_retail"] is None
    assert data["fixed_price_wholesale"] is None


@pytest.mark.django_db
def test_combo_dispatch_without_prices_completes_normally(
    authenticated_almacenista_client, almacenista_user, db
):
    """POST /movements/combo-dispatch/ sin precios configurados → 201 sin bloqueo."""
    product = ProductFactory(sku="CMB-NOPR2")
    location = LocationFactory(code="BODEGA_NOPR", name="Bodega Sin Precio")

    from apps.inventory.models import StockByLocation

    StockByLocation.objects.create(product=product, location=location, current_stock=10)

    combo = ProductCombo.objects.create(name="Kit NoPrecio", sku="KIT-0098")
    ComboItem.objects.create(combo=combo, product=product, quantity=2)

    url = reverse("movements-combo-dispatch")
    resp = authenticated_almacenista_client.post(
        url,
        {"combo_id": str(combo.id), "location_id": str(location.id)},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    # Los movimientos existen y el price_type indica que es un combo
    assert len(data) == 1
    assert data[0]["price_type"] == "combo"
    assert data[0]["unit_price"] is None  # sin precio: null, no error
