"""Consultas de lectura del módulo de compras (sin side effects)."""

from __future__ import annotations

import uuid

from django.db.models import QuerySet

from .models import PurchaseOrder, Reception, Supplier


def get_suppliers(
    *,
    is_active: bool | None = None,
    include_archived: bool = False,
) -> QuerySet:
    qs = Supplier.objects.select_related("created_by").order_by("nombre_comercial")
    if not include_archived:
        qs = qs.filter(deleted_at__isnull=True)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def get_supplier(supplier_id: uuid.UUID) -> Supplier:
    return Supplier.objects.select_related("created_by").get(pk=supplier_id)


def get_purchase_orders(
    *,
    status: str | None = None,
    supplier_id: uuid.UUID | None = None,
) -> QuerySet:
    qs = (
        PurchaseOrder.objects.select_related(
            "supplier", "created_by", "confirmed_by", "cancelled_by"
        )
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    if status:
        qs = qs.filter(status=status)
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    return qs


def get_purchase_order(po_id: uuid.UUID) -> PurchaseOrder:
    return (
        PurchaseOrder.objects.select_related(
            "supplier", "created_by", "confirmed_by", "cancelled_by"
        )
        .prefetch_related(
            "items__product", "receptions__items__purchase_order_item__product"
        )
        .get(pk=po_id)
    )


def get_receptions(
    *,
    po_id: uuid.UUID | None = None,
    status: str | None = None,
) -> QuerySet:
    qs = (
        Reception.objects.select_related(
            "purchase_order__supplier",
            "destination_location",
            "received_by",
        )
        .prefetch_related(
            "items__purchase_order_item__product",
            "items__movement",
            "items__allocations__location",
            "items__allocations__movement",
        )
        .order_by("-created_at")
    )
    if po_id:
        qs = qs.filter(purchase_order_id=po_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def get_reception(reception_id: uuid.UUID) -> Reception:
    return (
        Reception.objects.select_related(
            "purchase_order__supplier",
            "destination_location",
            "received_by",
        )
        .prefetch_related(
            "items__purchase_order_item__product",
            "items__movement",
            "items__allocations__location",
            "items__allocations__movement",
        )
        .get(pk=reception_id)
    )
