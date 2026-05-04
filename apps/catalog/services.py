"""Servicios de catálogo (RF-003, BR-04, BR-12, BR-13)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.catalog.models import Category, Product
from shared.exceptions import UnauthorizedCredentialManagementError
from shared.utils.validators import validate_can_sku, validate_sku_format

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.authentication.models import User


def _require_almacenista(user: User) -> None:
    if getattr(user, "role", None) != "almacenista":
        raise UnauthorizedCredentialManagementError()


@transaction.atomic
def create_product(user: User, data: dict[str, Any], *, request: HttpRequest | None = None) -> Product:
    """
    RF-003, BR-04, BR-12 — Crea producto; validaciones de marca y serial por categoría.
    """
    _require_almacenista(user)
    sku = (data.get("sku") or "").strip()
    validate_sku_format(sku)
    brand = (data.get("brand") or "Can").strip() or "Can"
    validate_can_sku(sku, brand=brand)
    category = Category.objects.get(pk=data["category_id"])
    product = Product.objects.create(
        sku=sku,
        name=data["name"],
        category=category,
        subcategory_id=data.get("subcategory_id"),
        barcode=data.get("barcode") or None,
        brand=brand,
        expiration_date=data.get("expiration_date") or data.get("expiry_date"),
        weight_grams=data.get("weight_grams"),
        requires_cold_chain=bool(data.get("requires_cold_chain")),
        is_active=bool(data.get("is_active", True)),
        notes=data.get("notes") or "",
        reorder_point=int(data.get("reorder_point", 0)),
    )
    log_event(
        AuditEventType.PRODUCT_CREATED,
        description=f"Producto creado: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )
    return product


def resolve_identifier(value: str) -> Product | None:
    """
    BR-13 — Resuelve barcode, SKU o coincidencia parcial de nombre a `Product`.

    Prioridad: SKU exacto, código de barras exacto, nombre icontains.
    """
    raw = (value or "").strip()
    if not raw:
        return None
    p = Product.objects.filter(sku__iexact=raw, is_active=True).select_related("category").first()
    if p:
        return p
    p = Product.objects.filter(barcode__iexact=raw, is_active=True).select_related("category").first()
    if p:
        return p
    return Product.objects.filter(name__icontains=raw, is_active=True).select_related("category").first()
