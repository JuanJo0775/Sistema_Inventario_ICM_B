"""Tests de endpoints REST del módulo de movimientos."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.models import StockByLocation
from apps.movements.models import MovementType


@pytest.mark.django_db
def test_entry_endpoint_returns_201(
    authenticated_almacenista_client, sample_product, sample_locations
):
    loc = sample_locations[0]
    response = authenticated_almacenista_client.post(
        "/api/v1/movements/entries/",
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 5,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["movement_type"] == MovementType.ENTRADA
    assert response.data["quantity"] == 5


@pytest.mark.django_db
def test_dispatch_endpoint_returns_201(
    authenticated_almacenista_client, sample_product, sample_locations
):
    loc = sample_locations[0]
    StockByLocation.objects.create(
        product=sample_product, location=loc, current_stock=10
    )
    response = authenticated_almacenista_client.post(
        "/api/v1/movements/dispatches/",
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 3,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_transfer_endpoint_returns_201(
    authenticated_almacenista_client, sample_product, sample_locations
):
    origin = sample_locations[1]
    destination = sample_locations[2]
    StockByLocation.objects.create(
        product=sample_product, location=origin, current_stock=10
    )
    response = authenticated_almacenista_client.post(
        "/api/v1/movements/transfers/",
        {
            "product_id": str(sample_product.id),
            "origin_id": str(origin.id),
            "destination_id": str(destination.id),
            "quantity": 4,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["movement_type"] == MovementType.TRASLADO


@pytest.mark.django_db
def test_movement_list_returns_200(authenticated_almacenista_client):
    response = authenticated_almacenista_client.get("/api/v1/movements/")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data


@pytest.mark.django_db
def test_movement_detail_returns_200(
    authenticated_almacenista_client, almacenista_user, sample_product, sample_locations
):
    from apps.movements.services import register_entry

    loc = sample_locations[0]
    movement = register_entry(almacenista_user, sample_product.id, loc.id, 2)
    response = authenticated_almacenista_client.get(
        f"/api/v1/movements/{movement.id}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert str(response.data["id"]) == str(movement.id)


@pytest.mark.django_db
def test_dispatch_returns_409_on_insufficient_stock(
    authenticated_almacenista_client, sample_product, sample_locations
):
    loc = sample_locations[0]
    # No stock setup — _lock_stock creates row with current_stock=0 → InsufficientStockError
    response = authenticated_almacenista_client.post(
        "/api/v1/movements/dispatches/",
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 99,
            "movement_type": MovementType.SALIDA_VENTA_MENOR,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["error"] == "INSUFFICIENT_STOCK"


@pytest.mark.django_db
def test_corrections_endpoint_returns_201(
    authenticated_almacenista_client,
    almacenista_user,
    sample_product,
    sample_locations,
):
    from apps.movements.services import register_internal_transfer

    origin = sample_locations[1]
    destination = sample_locations[2]
    StockByLocation.objects.create(
        product=sample_product, location=origin, current_stock=10
    )
    transfer = register_internal_transfer(
        almacenista_user,
        sample_product.id,
        origin.id,
        destination.id,
        5,
    )
    # Reversal restores origin to 10; fixed transfer sends 3 from origin to destination
    response = authenticated_almacenista_client.post(
        f"/api/v1/movements/{transfer.id}/corrections/",
        {
            "origin_id": str(origin.id),
            "destination_id": str(destination.id),
            "quantity": 3,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_auxiliar_can_create_entry(auxiliar_user, sample_product, sample_locations):
    client = APIClient()
    client.force_authenticate(user=auxiliar_user)
    loc = sample_locations[0]
    response = client.post(
        "/api/v1/movements/entries/",
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 2,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_administrador_cannot_create_entry(
    administrador_user, sample_product, sample_locations
):
    client = APIClient()
    client.force_authenticate(user=administrador_user)
    loc = sample_locations[0]
    response = client.post(
        "/api/v1/movements/entries/",
        {
            "product_id": str(sample_product.id),
            "location_id": str(loc.id),
            "quantity": 2,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
