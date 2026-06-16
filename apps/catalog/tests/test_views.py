"""Tests de endpoints REST del módulo de catálogo."""

from __future__ import annotations

import pytest
from rest_framework import status

from apps.catalog.views import (
    CategoryListCreateView,
    ProductBarcodeView,
    ProductListCreateView,
    ResolveIdentifierView,
)
from tests.factories import CategoryFactory, ProductFactory


def test_catalog_views_are_available():
    assert CategoryListCreateView is not None
    assert ProductListCreateView is not None
    assert ProductBarcodeView is not None
    assert ResolveIdentifierView is not None


@pytest.mark.django_db
def test_product_barcode_endpoint_returns_ready_to_consume_payload(
    authenticated_almacenista_client, sample_product
):
    url = f"/api/v1/catalog/products/{sample_product.id}/barcode/"

    response = authenticated_almacenista_client.get(url)

    assert response.status_code == 200
    assert response.data["product_id"] == str(sample_product.id)
    assert response.data["barcode"] == sample_product.barcode
    assert response.data["barcode_type"] == "Code128"
    assert response.data["render_format"] == "svg"
    assert response.data["barcode_svg"].startswith("<?xml")
    assert response.data["barcode_svg_data_uri"].startswith(
        "data:image/svg+xml;base64,"
    )


@pytest.mark.django_db
def test_product_list_returns_200(authenticated_almacenista_client):
    ProductFactory.create_batch(3)
    response = authenticated_almacenista_client.get("/api/v1/catalog/products/")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert response.data["count"] >= 3


@pytest.mark.django_db
def test_product_create_returns_201(authenticated_almacenista_client):
    category = CategoryFactory()
    response = authenticated_almacenista_client.post(
        "/api/v1/catalog/products/",
        {
            "sku": "TST-0001",
            "name": "Producto de prueba",
            "category_id": str(category.id),
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["sku"] == "TST-0001"


@pytest.mark.django_db
def test_category_create_returns_201(authenticated_almacenista_client):
    response = authenticated_almacenista_client.post(
        "/api/v1/catalog/categories/",
        {"name": "Categoría de prueba"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Categoría de prueba"


@pytest.mark.django_db
def test_resolve_by_sku_returns_200(authenticated_almacenista_client, sample_product):
    response = authenticated_almacenista_client.get(
        "/api/v1/catalog/products/resolve/", {"q": sample_product.sku}
    )
    assert response.status_code == status.HTTP_200_OK
    assert str(response.data["id"]) == str(sample_product.id)


@pytest.mark.django_db
def test_resolve_unknown_returns_404(authenticated_almacenista_client):
    response = authenticated_almacenista_client.get(
        "/api/v1/catalog/products/resolve/", {"q": "SKU-INEXISTENTE-9999"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_product_price_update_returns_200(
    authenticated_almacenista_client, sample_product
):
    response = authenticated_almacenista_client.patch(
        f"/api/v1/catalog/products/{sample_product.id}/prices/",
        {"sale_price_retail": "15000.00"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["sale_price_retail"] == "15000.0000"


@pytest.mark.django_db
def test_product_list_is_paginated(authenticated_almacenista_client):
    ProductFactory.create_batch(15)
    response = authenticated_almacenista_client.get("/api/v1/catalog/products/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] >= 15
    assert "next" in response.data
    assert "previous" in response.data


@pytest.mark.django_db
def test_product_create_duplicate_sku_returns_400(authenticated_almacenista_client):
    category = CategoryFactory()
    ProductFactory(sku="DUP-0001", category=category)
    response = authenticated_almacenista_client.post(
        "/api/v1/catalog/products/",
        {
            "sku": "DUP-0001",
            "name": "Producto duplicado",
            "category_id": str(category.id),
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "DUP-0001" in str(response.data)
    assert "ya existe" in str(response.data)


@pytest.mark.django_db
def test_combo_create_duplicate_sku_returns_400(authenticated_almacenista_client):
    category = CategoryFactory()
    product = ProductFactory(sku="PROD-CMB", category=category)
    payload = {
        "sku": "CMB-010",
        "name": "Combo original",
        "items": [{"product_id": str(product.id), "quantity": 1}],
    }
    authenticated_almacenista_client.post(
        "/api/v1/catalog/combos/",
        payload,
        format="json",
    )
    response = authenticated_almacenista_client.post(
        "/api/v1/catalog/combos/",
        payload,
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "CMB-010" in str(response.data)
    assert "ya existe" in str(response.data)


@pytest.mark.django_db
def test_combo_update_duplicate_sku_returns_400(authenticated_almacenista_client):
    category = CategoryFactory()
    product = ProductFactory(sku="PROD-CMB2", category=category)
    authenticated_almacenista_client.post(
        "/api/v1/catalog/combos/",
        {
            "sku": "CMB-020",
            "name": "Combo uno",
            "items": [{"product_id": str(product.id), "quantity": 1}],
        },
        format="json",
    )
    resp2 = authenticated_almacenista_client.post(
        "/api/v1/catalog/combos/",
        {
            "sku": "CMB-021",
            "name": "Combo dos",
            "items": [{"product_id": str(product.id), "quantity": 1}],
        },
        format="json",
    )
    combo2_id = resp2.data["id"]
    response = authenticated_almacenista_client.patch(
        f"/api/v1/catalog/combos/{combo2_id}/",
        {"sku": "CMB-020"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "CMB-020" in str(response.data)
    assert "ya existe" in str(response.data)
