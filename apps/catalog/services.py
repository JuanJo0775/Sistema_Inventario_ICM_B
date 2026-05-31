"""Servicios de catálogo (RF-003, BR-04, BR-12, BR-13)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.catalog.models import Category, ComboItem, Product, ProductCombo, Subcategory
from shared.exceptions import (
    InvalidSKUFormatError,
    UnauthorizedCredentialManagementError,
)
from shared.utils.barcode import build_product_barcode
from shared.utils.validators import validate_sku_format

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.authentication.models import User


def _require_almacenista(user: User) -> None:
    if getattr(user, "role", None) != "almacenista":
        raise UnauthorizedCredentialManagementError()


@transaction.atomic
def create_product(
    user: User, data: dict[str, Any], *, request: HttpRequest | None = None
) -> Product:
    """
    RF-003, BR-04, BR-12 — Crea producto; validaciones de formato de SKU y serial por categoría.
    """
    _require_almacenista(user)
    sku = (data.get("sku") or "").strip()
    validate_sku_format(sku)
    brand = (data.get("brand") or "Can").strip() or "Can"
    category = Category.objects.get(pk=data["category_id"])
    product = Product.objects.create(
        sku=sku,
        name=data["name"],
        category=category,
        subcategory_id=data.get("subcategory_id"),
        barcode=data.get("barcode") or None,
        brand=brand,
        expiration_date=data.get("expiration_date") or data.get("expiry_date"),
        requires_expiration=bool(data.get("requires_expiration")),
        weight_grams=data.get("weight_grams"),
        requires_cold_chain=bool(data.get("requires_cold_chain")),
        is_active=bool(data.get("is_active", True)),
        notes=data.get("notes") or "",
        reorder_point=int(data.get("reorder_point", 0)),
    )
    if not product.barcode:
        product.barcode = build_product_barcode(product.id)
        product.save(update_fields=("barcode",))
    log_event(
        AuditEventType.PRODUCT_CREATED,
        description=f"Producto creado: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )
    return product


@transaction.atomic
def update_product(
    user: User,
    product_id,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> Product:
    """
    RF-003, BR-12 — Actualiza producto; valida formato de SKU si cambia.

    Raises:
        UnauthorizedCredentialManagementError: Si el ejecutor no es almacenista.
        InvalidSKUFormatError: BR-12.
    """
    _require_almacenista(user)
    product = (
        Product.objects.select_for_update()
        .select_related("category")
        .get(pk=product_id)
    )
    new_sku = (data.get("sku") or product.sku or "").strip()
    brand = (data.get("brand") or product.brand or "Can").strip() or "Can"
    if new_sku != product.sku or brand != product.brand:
        try:
            validate_sku_format(new_sku)
        except Exception as exc:
            raise InvalidSKUFormatError(str(exc)) from exc
    for field in (
        "name",
        "sku",
        "brand",
        "expiration_date",
        "requires_expiration",
        "weight_grams",
        "requires_cold_chain",
        "is_active",
        "notes",
        "reorder_point",
    ):
        if field in data:
            setattr(product, field, data[field])
    if "category_id" in data:
        product.category_id = data["category_id"]
    if "subcategory_id" in data:
        product.subcategory_id = data.get("subcategory_id")
    if not product.barcode:
        product.barcode = data.get("barcode") or build_product_barcode(product.id)
    product.save()
    log_event(
        AuditEventType.PRODUCT_UPDATED,
        description=f"Producto actualizado: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id)},
    )
    return product


@transaction.atomic
def create_combo(
    user: User,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> ProductCombo:
    """
    RF-003 — Crea combo y sus ítems; todos los productos deben existir y estar activos.

    Args:
        user: Ejecutor (almacenista).
        data: `name`, `sku`, `items`: list[{"product_id": UUID, "quantity": int}].

    Raises:
        ValueError: Si falta un producto o hay SKU inválido.
    """
    _require_almacenista(user)
    sku = (data.get("sku") or "").strip()
    validate_sku_format(sku)
    name = (data.get("name") or "").strip()
    items = data.get("items") or []
    if not name or not items:
        raise ValueError("name e items son obligatorios.")
    product_ids = [i["product_id"] for i in items]
    products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
    if len(products) != len(set(product_ids)):
        raise ValueError("Uno o más product_id no existen.")
    for row in items:
        pid = str(row["product_id"])
        p = products[pid]

        if not p.is_active:
            from shared.exceptions import DomainValidationError

            raise DomainValidationError(f"Producto {p.sku} no está activo.")
    combo = ProductCombo.objects.create(
        name=name,
        sku=sku,
        is_active=bool(data.get("is_active", True)),
    )
    for row in items:
        ComboItem.objects.create(
            combo=combo,
            product_id=row["product_id"],
            quantity=int(row.get("quantity", 1)),
        )
    log_event(
        AuditEventType.COMBO_CREATED,
        description=f"Combo creado: {combo.sku}",
        user=user,
        request=request,
        detail={"combo_id": str(combo.id), "sku": combo.sku},
    )
    return combo


@transaction.atomic
def create_category(
    user: User,
    *,
    name: str,
    description: str = "",
    requires_serial_number: bool = False,
    is_returnable: bool = False,
    request: HttpRequest | None = None,
) -> Category:
    """RF-003 — Crea categoría (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)
    base = slugify(name) or "categoria"
    slug = base
    n = 0
    while Category.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    cat = Category.objects.create(
        name=name.strip(),
        slug=slug,
        description=description or "",
        requires_serial_number=requires_serial_number,
        is_returnable=is_returnable,
    )
    log_event(
        AuditEventType.CATEGORY_CREATED,
        description=f"Categoría creada: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )
    return cat


def resolve_identifier(value: str) -> Product:
    """
    BR-13 — Resuelve barcode, SKU o coincidencia parcial de nombre a `Product`.

    Prioridad: SKU exacto, código de barras exacto, nombre icontains.

    Raises:
        Product.DoesNotExist: Si no hay producto activo coincidente.
    """
    raw = (value or "").strip()
    if not raw:
        raise Product.DoesNotExist("Identificador vacío.")
    p = (
        Product.objects.filter(sku__iexact=raw, is_active=True)
        .select_related("category")
        .first()
    )
    if p:
        return p
    p = (
        Product.objects.filter(barcode__iexact=raw, is_active=True)
        .select_related("category")
        .first()
    )
    if p:
        return p
    p = (
        Product.objects.filter(name__icontains=raw, is_active=True)
        .select_related("category")
        .first()
    )
    if p:
        return p
    raise Product.DoesNotExist(
        f"No se encontró producto activo para el identificador «{raw}»."
    )


@transaction.atomic
def create_subcategory(
    user: User,
    *,
    category_id: Any,
    name: str,
    request: HttpRequest | None = None,
) -> Subcategory:
    """RF-003 — Crea subcategoría (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)
    category = Category.objects.get(pk=category_id)
    base = slugify(name) or "subcategoria"
    slug = base
    n = 0
    while Subcategory.objects.filter(category=category, slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"

    subcat = Subcategory.objects.create(
        category=category,
        name=name.strip(),
        slug=slug,
    )
    log_event(
        AuditEventType.SUBCATEGORY_CREATED,
        description=f"Subcategoría creada: {subcat.name} en {category.name}",
        user=user,
        request=request,
        detail={"subcategory_id": str(subcat.id), "category_id": str(category.id)},
    )
    return subcat
