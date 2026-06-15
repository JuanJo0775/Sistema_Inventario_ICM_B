"""Servicios de catálogo (RF-003, BR-04, BR-12, BR-13)."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.catalog.models import (
    Brand,
    Category,
    ComboItem,
    Product,
    ProductCombo,
    ProductPriceHistory,
)
from apps.inventory.models import StockByLocation
from apps.purchasing.models import (
    PurchaseOrderItem,
    PurchaseOrderStatus,
    ReceptionItem,
    ReceptionStatus,
)
from shared.exceptions import (
    DomainValidationError,
    UnauthorizedCredentialManagementError,
)
from shared.utils.barcode import build_product_barcode
from shared.utils.db import get_for_update_or_404
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
    category = Category.objects.get(pk=data["category_id"])
    if not category.is_active:
        raise DomainValidationError(
            f"La categoría '{category.name}' está inactiva y no puede recibir nuevos productos."
        )
    if data.get("brand_id"):
        brand = Brand.objects.get(pk=data["brand_id"])
        if not brand.is_active:
            raise DomainValidationError(
                f"La marca '{brand.name}' está inactiva y no puede asignarse a nuevos productos."
            )
    try:
        product = Product.objects.create(
            sku=sku,
            name=data["name"],
            category=category,
            brand_id=data.get("brand_id"),
            barcode=build_product_barcode(sku),
            expiration_date=data.get("expiration_date") or data.get("expiry_date"),
            requires_expiration=bool(data.get("requires_expiration")),
            weight_grams=data.get("weight_grams"),
            requires_cold_chain=bool(data.get("requires_cold_chain")),
            is_active=bool(data.get("is_active", True)),
            notes=data.get("notes") or "",
            reorder_point=int(data.get("reorder_point", 0)),
            # Campos de precio opcionales
            unit_cost=data.get("unit_cost"),
            sale_price_retail=data.get("sale_price_retail"),
            sale_price_wholesale=data.get("sale_price_wholesale"),
            tax_rate_pct=data.get("tax_rate_pct"),
            currency=data.get("currency") or "COP",
        )
    except IntegrityError:
        raise DomainValidationError(f"El SKU '{sku}' ya existe.")
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
    product_id: Any,
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
    product = get_for_update_or_404(
        Product.objects.select_related("category"), pk=product_id
    )
    new_sku = (data.get("sku") or product.sku or "").strip()
    if new_sku != product.sku:
        raise DomainValidationError("El SKU es inmutable; no puede modificarse.")
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
    if "category_id" in data and data["category_id"] != product.category_id:
        new_cat = Category.objects.get(pk=data["category_id"])
        if not new_cat.is_active:
            raise DomainValidationError(
                f"La categoría '{new_cat.name}' está inactiva y no puede asignarse."
            )
        product.category = new_cat
    if "brand_id" in data:
        if data["brand_id"] is None:
            product.brand = None
        elif data["brand_id"] != (product.brand_id if product.brand_id else None):
            new_brand = Brand.objects.get(pk=data["brand_id"])
            if not new_brand.is_active:
                raise DomainValidationError(
                    f"La marca '{new_brand.name}' está inactiva y no puede asignarse."
                )
            product.brand_id = data["brand_id"]
    if not product.barcode:
        product.barcode = build_product_barcode(product.sku)
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
            raise DomainValidationError(f"Producto {p.sku} no está activo.")
    try:
        combo = ProductCombo.objects.create(
            name=name,
            sku=sku,
            price_strategy=data.get("price_strategy", "derived"),
            fixed_price_retail=data.get("fixed_price_retail"),
            fixed_price_wholesale=data.get("fixed_price_wholesale"),
        )
    except IntegrityError:
        raise DomainValidationError(f"El SKU '{sku}' ya existe en otro combo.")
    try:
        for row in items:
            ComboItem.objects.create(
                combo=combo,
                product_id=row["product_id"],
                quantity=int(row.get("quantity", 1)),
            )
    except IntegrityError:
        # @transaction.atomic hace rollback automático de todo el bloque,
        # incluyendo la creación del combo. No se necesita combo.delete() aquí.
        raise DomainValidationError("Uno o más productos ya están en el combo.")
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
    try:
        cat = Category.objects.create(
            name=name.strip(),
            slug=slug,
            description=description or "",
            requires_serial_number=requires_serial_number,
            is_returnable=is_returnable,
        )
    except IntegrityError:
        raise DomainValidationError(
            f"Ya existe una categoría con el nombre '{name.strip()}'."
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
def create_brand(
    user: User,
    *,
    name: str,
    description: str = "",
    request: HttpRequest | None = None,
) -> Brand:
    """RF-003 — Crea marca (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)

    base = slugify(name) or "marca"
    slug = base
    n = 0
    while Brand.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"

    try:
        brand = Brand.objects.create(
            name=name.strip(),
            slug=slug,
            description=description or "",
        )
    except IntegrityError:
        raise DomainValidationError(
            f"Ya existe una marca con el nombre '{name.strip()}'."
        )
    log_event(
        AuditEventType.BRAND_CREATED,
        description=f"Marca creada: {brand.name}",
        user=user,
        request=request,
        detail={"brand_id": str(brand.id)},
    )
    return brand


@transaction.atomic
def update_category(
    user: User,
    category_id: Any,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> Category:
    """RF-003 — Actualiza categoría (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)
    cat = get_for_update_or_404(Category.objects, pk=category_id)
    if "name" in data:
        new_name = data["name"].strip()
        if new_name != cat.name:
            base = slugify(new_name) or "categoria"
            slug = base
            n = 0
            while Category.objects.filter(slug=slug).exclude(pk=cat.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            cat.name = new_name
            cat.slug = slug
    for field in ("description", "requires_serial_number", "is_returnable"):
        if field in data:
            setattr(cat, field, data[field])
    cat.save()
    log_event(
        AuditEventType.CATEGORY_UPDATED,
        description=f"Categoría actualizada: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )
    return cat


# ── Soft Delete ──────────────────────────────────────────────────────────────
# Responsabilidad: existencia lógica del registro.
# Bloquea si hay productos activos asociados.


@transaction.atomic
def soft_delete_category(
    user: User,
    category_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """
    Soft delete de categoría. Marca `deleted_at`.
    Bloquea con ValueError si existen productos activos asociados.
    """
    _require_almacenista(user)
    cat = get_for_update_or_404(Category.objects, pk=category_id)
    if cat.deleted_at:
        raise ValueError("La categoría ya está eliminada.")
    active_count = Product.objects.filter(category=cat, is_active=True).count()
    if active_count:
        raise ValueError(
            f"No se puede eliminar la categoría porque tiene {active_count} "
            f"producto(s) activo(s) asociado(s)."
        )
    cat.soft_delete()
    log_event(
        AuditEventType.CATEGORY_SOFT_DELETED,
        description=f"Categoría eliminada lógicamente: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )


@transaction.atomic
def restore_category(
    user: User,
    category_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Category:
    """Restaura una categoría previamente eliminada lógicamente."""
    _require_almacenista(user)
    cat = get_for_update_or_404(Category.objects, pk=category_id)
    if not cat.deleted_at:
        raise ValueError("La categoría no está eliminada.")
    cat.restore()
    log_event(
        AuditEventType.CATEGORY_RESTORED,
        description=f"Categoría restaurada: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )
    return cat


# ── Disponibilidad para asignación ───────────────────────────────────────────
# Responsabilidad: controlar si la categoría puede asignarse a nuevos productos.
# Nunca bloquea, incluso si hay productos activos.


@transaction.atomic
def disable_category_for_assignment(
    user: User,
    category_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Category:
    """
    Marca `is_active=False`. La categoría no puede asignarse a nuevos productos.
    No afecta relaciones históricas. Nunca bloquea.
    """
    _require_almacenista(user)
    cat = get_for_update_or_404(Category.objects, pk=category_id)
    if cat.deleted_at:
        raise ValueError(
            "No se puede modificar la disponibilidad de una categoría eliminada."
        )
    cat.is_active = False
    cat.save(update_fields=["is_active"])
    log_event(
        AuditEventType.CATEGORY_DISABLED,
        description=f"Categoría desactivada para asignación: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )
    return cat


@transaction.atomic
def enable_category_for_assignment(
    user: User,
    category_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Category:
    """
    Marca `is_active=True`. La categoría vuelve a estar disponible para nuevos productos.
    """
    _require_almacenista(user)
    cat = get_for_update_or_404(Category.objects, pk=category_id)
    if cat.deleted_at:
        raise ValueError(
            "No se puede modificar la disponibilidad de una categoría eliminada."
        )
    cat.is_active = True
    cat.save(update_fields=["is_active"])
    log_event(
        AuditEventType.CATEGORY_ENABLED,
        description=f"Categoría reactivada para asignación: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )
    return cat


@transaction.atomic
def update_brand(
    user: User,
    brand_id: Any,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> Brand:
    """RF-003 — Actualiza marca (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)
    brand = get_for_update_or_404(Brand.objects, pk=brand_id)
    if "name" in data:
        new_name = data["name"].strip()
        if new_name != brand.name:
            base = slugify(new_name) or "marca"
            slug = base
            n = 0
            while Brand.objects.filter(slug=slug).exclude(pk=brand.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            brand.name = new_name
            brand.slug = slug
    if "description" in data:
        brand.description = data["description"] or ""
    brand.save()
    log_event(
        AuditEventType.BRAND_UPDATED,
        description=f"Marca actualizada: {brand.name}",
        user=user,
        request=request,
        detail={"brand_id": str(brand.id)},
    )
    return brand


# ── Soft Delete ──────────────────────────────────────────────────────────────


@transaction.atomic
def soft_delete_brand(
    user: User,
    brand_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """
    Soft delete de marca. Marca `deleted_at`.
    Bloquea con ValueError si existen productos activos asociados.
    """
    _require_almacenista(user)
    brand = get_for_update_or_404(Brand.objects, pk=brand_id)
    if brand.deleted_at:
        raise ValueError("La marca ya está eliminada.")
    active_count = Product.objects.filter(brand=brand, is_active=True).count()
    if active_count:
        raise ValueError(
            f"No se puede eliminar la marca porque tiene {active_count} "
            f"producto(s) activo(s) asociado(s)."
        )
    brand.soft_delete()
    log_event(
        AuditEventType.BRAND_SOFT_DELETED,
        description=f"Marca eliminada lógicamente: {brand.name}",
        user=user,
        request=request,
        detail={"brand_id": str(brand.id)},
    )


@transaction.atomic
def restore_brand(
    user: User,
    brand_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Brand:
    """Restaura una marca previamente eliminada lógicamente."""
    _require_almacenista(user)
    brand = get_for_update_or_404(Brand.objects, pk=brand_id)
    if not brand.deleted_at:
        raise ValueError("La marca no está eliminada.")
    brand.restore()
    log_event(
        AuditEventType.BRAND_RESTORED,
        description=f"Marca restaurada: {brand.name}",
        user=user,
        request=request,
        detail={"brand_id": str(brand.id)},
    )
    return brand


# ── Disponibilidad para asignación ───────────────────────────────────────────


@transaction.atomic
def disable_brand_for_assignment(
    user: User,
    brand_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Brand:
    """
    Marca `is_active=False`. La marca no puede asignarse a nuevos productos.
    No afecta relaciones históricas. Nunca bloquea.
    """
    _require_almacenista(user)
    brand = get_for_update_or_404(Brand.objects, pk=brand_id)
    if brand.deleted_at:
        raise ValueError(
            "No se puede modificar la disponibilidad de una marca eliminada."
        )
    brand.is_active = False
    brand.save(update_fields=["is_active"])
    log_event(
        AuditEventType.BRAND_DISABLED,
        description=f"Marca desactivada para asignación: {brand.name}",
        user=user,
        request=request,
        detail={"brand_id": str(brand.id)},
    )
    return brand


@transaction.atomic
def enable_brand_for_assignment(
    user: User,
    brand_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Brand:
    """Marca `is_active=True`. La marca vuelve a estar disponible para nuevos productos."""
    _require_almacenista(user)
    brand = get_for_update_or_404(Brand.objects, pk=brand_id)
    if brand.deleted_at:
        raise ValueError(
            "No se puede modificar la disponibilidad de una marca eliminada."
        )
    brand.is_active = True
    brand.save(update_fields=["is_active"])
    log_event(
        AuditEventType.BRAND_ENABLED,
        description=f"Marca reactivada para asignación: {brand.name}",
        user=user,
        request=request,
        detail={"brand_id": str(brand.id)},
    )
    return brand


@transaction.atomic
def update_combo(
    user: User,
    combo_id: Any,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> ProductCombo:
    """
    RF-003 — Actualiza combo. Si se envían `items`, reemplaza completamente los ComboItem.

    Args:
        data: name, sku (todos opcionales). items: si presente, reemplaza lista completa.
              is_active NO se acepta aquí; usar DELETE/POST restore para activar/desactivar.
    """
    _require_almacenista(user)
    combo = get_for_update_or_404(ProductCombo.objects, pk=combo_id)
    if "name" in data:
        combo.name = data["name"].strip()
    if "sku" in data:
        new_sku = data["sku"].strip()
        validate_sku_format(new_sku)
        combo.sku = new_sku
    for field in ("price_strategy", "fixed_price_retail", "fixed_price_wholesale"):
        if field in data:
            setattr(combo, field, data[field])
    try:
        combo.save()
    except IntegrityError:
        new_sku = data.get("sku", combo.sku or "").strip()
        raise DomainValidationError(f"El SKU '{new_sku}' ya existe en otro combo.")

    if "items" in data:
        items = data["items"]
        product_ids = [i["product_id"] for i in items]
        products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
        if len(products) != len(set(str(pid) for pid in product_ids)):
            raise ValueError("Uno o más product_id no existen.")
        for row in items:
            p = products[str(row["product_id"])]
            if not p.is_active:
                raise DomainValidationError(f"Producto {p.sku} no está activo.")
        ComboItem.objects.filter(combo=combo).delete()
        for row in items:
            ComboItem.objects.create(
                combo=combo,
                product_id=row["product_id"],
                quantity=int(row.get("quantity", 1)),
            )

    log_event(
        AuditEventType.COMBO_UPDATED,
        description=f"Combo actualizado: {combo.sku}",
        user=user,
        request=request,
        detail={"combo_id": str(combo.id), "sku": combo.sku},
    )
    return combo


@transaction.atomic
def soft_delete_combo(
    user: User,
    combo_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Elimina lógicamente un combo (soft delete)."""
    _require_almacenista(user)
    combo = get_for_update_or_404(ProductCombo.objects, pk=combo_id)
    combo.deleted_at = timezone.now()
    combo.save(update_fields=["deleted_at", "updated_at"])
    log_event(
        AuditEventType.COMBO_SOFT_DELETED,
        description=f"Combo eliminado lógicamente: {combo.sku}",
        user=user,
        request=request,
        detail={"combo_id": str(combo.id), "sku": combo.sku},
    )


@transaction.atomic
def restore_combo(
    user: User,
    combo_id: Any,
    *,
    request: HttpRequest | None = None,
) -> ProductCombo:
    """Restaura un combo previamente eliminado lógicamente."""
    _require_almacenista(user)
    combo = get_for_update_or_404(ProductCombo.objects, pk=combo_id)
    combo.deleted_at = None
    combo.save(update_fields=["deleted_at", "updated_at"])
    log_event(
        AuditEventType.COMBO_RESTORED,
        description=f"Combo restaurado: {combo.sku}",
        user=user,
        request=request,
        detail={"combo_id": str(combo.id), "sku": combo.sku},
    )
    return combo


@transaction.atomic
def deactivate_combo(
    user: User,
    combo_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Desactiva un combo (legacy wrapper -> soft_delete_combo)."""
    import warnings

    warnings.warn(
        "deactivate_combo is deprecated; use soft_delete_combo",
        DeprecationWarning,
        stacklevel=2,
    )
    soft_delete_combo(user, combo_id, request=request)


@transaction.atomic
def activate_combo(
    user: User,
    combo_id: Any,
    *,
    request: HttpRequest | None = None,
) -> ProductCombo:
    """Reactiva un combo (legacy wrapper -> restore_combo)."""
    import warnings

    warnings.warn(
        "activate_combo is deprecated; use restore_combo",
        DeprecationWarning,
        stacklevel=2,
    )
    return restore_combo(user, combo_id, request=request)


@transaction.atomic
def update_product_prices(
    user: User,
    product_id: Any,
    *,
    unit_cost: Any = None,
    sale_price_retail: Any = None,
    sale_price_wholesale: Any = None,
    tax_rate_pct: Any = None,
    currency: str | None = None,
    request: HttpRequest | None = None,
) -> Product:
    """
    Actualiza los campos de precio de un producto y registra cada cambio en ProductPriceHistory.

    Solo almacenistas pueden ejecutar esta acción.
    Los campos no enviados (None) se dejan intactos.
    """
    _require_almacenista(user)
    product = get_for_update_or_404(Product.objects, pk=product_id)

    updates: dict[str, Any] = {}
    if unit_cost is not None:
        updates["unit_cost"] = unit_cost
    if sale_price_retail is not None:
        updates["sale_price_retail"] = sale_price_retail
    if sale_price_wholesale is not None:
        updates["sale_price_wholesale"] = sale_price_wholesale
    if tax_rate_pct is not None:
        updates["tax_rate_pct"] = tax_rate_pct
    if currency is not None:
        updates["currency"] = currency

    if not updates:
        return product

    history_entries = []
    for field, new_val in updates.items():
        old_val = getattr(product, field)
        if old_val != new_val:
            history_entries.append(
                ProductPriceHistory(
                    product=product,
                    changed_by=user,
                    field_changed=field,
                    old_value=old_val if field != "currency" else None,
                    new_value=new_val if field != "currency" else None,
                    currency=updates.get("currency") or product.currency,
                )
            )
        setattr(product, field, new_val)

    product.save(update_fields=list(updates.keys()))
    if history_entries:
        ProductPriceHistory.objects.bulk_create(history_entries)

    log_event(
        AuditEventType.PRODUCT_PRICE_UPDATED,
        description=f"Precios actualizados: {product.sku}",
        user=user,
        request=request,
    )
    return product


# =============================================================================
# Soft Delete / Disponibilidad — Product
# =============================================================================


@transaction.atomic
def soft_delete_product(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """
    Elimina lógicamente un producto (soft delete).

    Bloquea si:
    - Existe stock > 0 en cualquier ubicación
    - Existe PurchaseOrderItem con OC en BORRADOR, PENDIENTE o PARCIALMENTE_RECIBIDA
    - Existe ReceptionItem en BORRADOR para este producto
    - Existe ComboItem en combo no archivado (deleted_at=NULL)
    """
    _require_almacenista(user)
    product = get_for_update_or_404(Product.objects, pk=product_id)

    # 1. Stock > 0 en cualquier ubicación
    if StockByLocation.objects.filter(product=product, current_stock__gt=0).exists():
        raise ValueError("No se puede archivar: existe stock > 0 en ubicaciones.")

    # 2. OC en borrador, pendiente o parcialmente recibida
    blocking_po_statuses = {
        PurchaseOrderStatus.BORRADOR,
        PurchaseOrderStatus.PENDIENTE,
        PurchaseOrderStatus.PARCIALMENTE_RECIBIDA,
    }
    if PurchaseOrderItem.objects.filter(
        product=product, purchase_order__status__in=blocking_po_statuses
    ).exists():
        raise ValueError(
            "No se puede archivar: existen órdenes de compra activas "
            "(borrador, pendiente o parcialmente recibida)."
        )

    # 3. Recepción en borrador
    if ReceptionItem.objects.filter(
        purchase_order_item__product=product, reception__status=ReceptionStatus.BORRADOR
    ).exists():
        raise ValueError("No se puede archivar: existen recepciones en borrador.")

    # 4. Combo activo (no archivado) que incluya este producto
    if ComboItem.objects.filter(
        product=product,
        combo__deleted_at__isnull=True,  # no archivado
    ).exists():
        raise ValueError(
            "No se puede archivar: el producto pertenece a uno o más combos activos."
        )

    product.deleted_at = timezone.now()
    product.is_active = False  # sync legado
    product.save(update_fields=["deleted_at", "is_active", "updated_at"])

    log_event(
        AuditEventType.PRODUCT_SOFT_DELETED,
        description=f"Producto eliminado lógicamente: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )


@transaction.atomic
def restore_product(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Product:
    """Restaura un producto previamente eliminado lógicamente."""
    _require_almacenista(user)
    product = get_for_update_or_404(
        Product.objects.select_related("category"), pk=product_id
    )
    product.deleted_at = None
    product.is_active = True  # sync legado
    product.save(update_fields=["deleted_at", "is_active", "updated_at"])

    log_event(
        AuditEventType.PRODUCT_RESTORED,
        description=f"Producto restaurado: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )
    return product


@transaction.atomic
def disable_product_for_assignment(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Desactiva un producto para asignación (pausa temporal)."""
    _require_almacenista(user)
    product = get_for_update_or_404(Product.objects, pk=product_id)
    if product.deleted_at is not None:
        raise ValueError(
            "No se puede desactivar un producto archivado; restáurelo primero."
        )
    product.is_active = False
    product.save(update_fields=["is_active", "updated_at"])

    log_event(
        AuditEventType.PRODUCT_DISABLED,
        description=f"Producto desactivado para asignación: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )


@transaction.atomic
def enable_product_for_assignment(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Product:
    """Reactiva un producto para asignación."""
    _require_almacenista(user)
    product = get_for_update_or_404(
        Product.objects.select_related("category"), pk=product_id
    )
    if product.deleted_at is not None:
        raise ValueError(
            "No se puede activar un producto archivado; restáurelo primero."
        )
    product.is_active = True
    product.save(update_fields=["is_active", "updated_at"])

    log_event(
        AuditEventType.PRODUCT_ENABLED,
        description=f"Producto reactivado para asignación: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )
    return product


# =============================================================================
# Wrappers legacy (deprecados)
# =============================================================================


@transaction.atomic
def deactivate_product(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Legacy wrapper: desactiva producto -> soft_delete_product."""
    warnings.warn(
        "deactivate_product is deprecated; use soft_delete_product",
        DeprecationWarning,
        stacklevel=2,
    )
    soft_delete_product(user, product_id, request=request)


@transaction.atomic
def activate_product(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Product:
    """Legacy wrapper: reactiva producto -> restore_product."""
    warnings.warn(
        "activate_product is deprecated; use restore_product",
        DeprecationWarning,
        stacklevel=2,
    )
    return restore_product(user, product_id, request=request)
