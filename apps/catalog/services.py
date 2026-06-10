"""Servicios de catálogo (RF-003, BR-04, BR-12, BR-13)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.catalog.models import (
    Category,
    ComboItem,
    Product,
    ProductCombo,
    ProductPriceHistory,
    Subcategory,
)
from shared.exceptions import (
    DomainValidationError,
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
        barcode=build_product_barcode(sku),
        brand=brand,
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
    if "category_id" in data:
        product.category_id = data["category_id"]
    if "subcategory_id" in data:
        product.subcategory_id = data.get("subcategory_id")
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
            from shared.exceptions import DomainValidationError

            raise DomainValidationError(f"Producto {p.sku} no está activo.")
    combo = ProductCombo.objects.create(
        name=name,
        sku=sku,
        is_active=bool(data.get("is_active", True)),
        price_strategy=data.get("price_strategy", "derived"),
        fixed_price_retail=data.get("fixed_price_retail"),
        fixed_price_wholesale=data.get("fixed_price_wholesale"),
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
    category_id: Any = None,
    name: str,
    description: str = "",
    request: HttpRequest | None = None,
) -> Subcategory:
    """RF-003 — Crea subcategoría / marca (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)

    # Si no se provee category_id, usa la primera categoría activa disponible
    if category_id:
        category = Category.objects.get(pk=category_id)
    else:
        category = Category.objects.filter(is_active=True).order_by("name").first()
        if not category:
            category = Category.objects.order_by("name").first()
        if not category:
            raise ValueError(
                "No existe ninguna categoría en el sistema. Crea al menos una categoría antes de crear marcas."
            )

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
        description=description or "",
    )
    log_event(
        AuditEventType.SUBCATEGORY_CREATED,
        description=f"Subcategoría/Marca creada: {subcat.name} en {category.name}",
        user=user,
        request=request,
        detail={"subcategory_id": str(subcat.id), "category_id": str(category.id)},
    )
    return subcat


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
    cat = Category.objects.select_for_update().get(pk=category_id)
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


@transaction.atomic
def deactivate_category(
    user: User,
    category_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Desactiva una categoría. Falla con ValueError si tiene productos activos."""
    _require_almacenista(user)
    cat = Category.objects.select_for_update().get(pk=category_id)
    active_count = Product.objects.filter(category=cat, is_active=True).count()
    if active_count:
        raise ValueError(
            f"No se puede desactivar la categoría porque tiene {active_count} "
            f"producto(s) activo(s) asociado(s)."
        )
    cat.is_active = False
    cat.save(update_fields=["is_active"])
    log_event(
        AuditEventType.CATEGORY_DEACTIVATED,
        description=f"Categoría desactivada: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )


@transaction.atomic
def activate_category(
    user: User,
    category_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Category:
    """Reactiva una categoría previamente desactivada."""
    _require_almacenista(user)
    cat = Category.objects.select_for_update().get(pk=category_id)
    cat.is_active = True
    cat.save(update_fields=["is_active"])
    log_event(
        AuditEventType.CATEGORY_ACTIVATED,
        description=f"Categoría reactivada: {cat.name}",
        user=user,
        request=request,
        detail={"category_id": str(cat.id)},
    )
    return cat


@transaction.atomic
def update_subcategory(
    user: User,
    subcategory_id: Any,
    data: dict[str, Any],
    *,
    request: HttpRequest | None = None,
) -> Subcategory:
    """RF-003 — Actualiza subcategoría / marca (solo almacenista)."""
    from django.utils.text import slugify

    _require_almacenista(user)
    subcat = (
        Subcategory.objects.select_for_update()
        .select_related("category")
        .get(pk=subcategory_id)
    )
    if "category_id" in data:
        subcat.category_id = data["category_id"]
    if "name" in data:
        new_name = data["name"].strip()
        if new_name != subcat.name:
            base = slugify(new_name) or "subcategoria"
            slug = base
            n = 0
            while (
                Subcategory.objects.filter(category_id=subcat.category_id, slug=slug)
                .exclude(pk=subcat.pk)
                .exists()
            ):
                n += 1
                slug = f"{base}-{n}"
            subcat.name = new_name
            subcat.slug = slug
    if "description" in data:
        subcat.description = data["description"] or ""
    if "is_active" in data:
        subcat.is_active = bool(data["is_active"])
    subcat.save()
    log_event(
        AuditEventType.SUBCATEGORY_UPDATED,
        description=f"Subcategoría/Marca actualizada: {subcat.name}",
        user=user,
        request=request,
        detail={"subcategory_id": str(subcat.id)},
    )
    return subcat


@transaction.atomic
def deactivate_subcategory(
    user: User,
    subcategory_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Desactiva una subcategoría. Falla con ValueError si tiene productos activos."""
    _require_almacenista(user)
    subcat = (
        Subcategory.objects.select_for_update()
        .select_related("category")
        .get(pk=subcategory_id)
    )
    active_count = Product.objects.filter(subcategory=subcat, is_active=True).count()
    if active_count:
        raise ValueError(
            f"No se puede desactivar la subcategoría porque tiene {active_count} "
            f"producto(s) activo(s) asociado(s)."
        )
    subcat.is_active = False
    subcat.save(update_fields=["is_active"])
    log_event(
        AuditEventType.SUBCATEGORY_DEACTIVATED,
        description=f"Subcategoría desactivada: {subcat.name}",
        user=user,
        request=request,
        detail={"subcategory_id": str(subcat.id)},
    )


@transaction.atomic
def activate_subcategory(
    user: User,
    subcategory_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Subcategory:
    """Reactiva una subcategoría previamente desactivada."""
    _require_almacenista(user)
    subcat = Subcategory.objects.select_for_update().get(pk=subcategory_id)
    subcat.is_active = True
    subcat.save(update_fields=["is_active"])
    log_event(
        AuditEventType.SUBCATEGORY_ACTIVATED,
        description=f"Subcategoría reactivada: {subcat.name}",
        user=user,
        request=request,
        detail={"subcategory_id": str(subcat.id)},
    )
    return subcat


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
    combo = ProductCombo.objects.select_for_update().get(pk=combo_id)
    if "name" in data:
        combo.name = data["name"].strip()
    if "sku" in data:
        new_sku = data["sku"].strip()
        validate_sku_format(new_sku)
        combo.sku = new_sku
    for field in ("price_strategy", "fixed_price_retail", "fixed_price_wholesale"):
        if field in data:
            setattr(combo, field, data[field])
    combo.save()

    if "items" in data:
        items = data["items"]
        product_ids = [i["product_id"] for i in items]
        products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
        if len(products) != len(set(str(pid) for pid in product_ids)):
            raise ValueError("Uno o más product_id no existen.")
        for row in items:
            p = products[str(row["product_id"])]
            if not p.is_active:
                from shared.exceptions import DomainValidationError

                raise DomainValidationError(f"Producto {p.sku} no está activo.")
        combo.combo_items.all().delete()
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
def deactivate_combo(
    user: User,
    combo_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """Desactiva un combo."""
    _require_almacenista(user)
    combo = ProductCombo.objects.select_for_update().get(pk=combo_id)
    combo.is_active = False
    combo.save(update_fields=["is_active"])
    log_event(
        AuditEventType.COMBO_DEACTIVATED,
        description=f"Combo desactivado: {combo.sku}",
        user=user,
        request=request,
        detail={"combo_id": str(combo.id), "sku": combo.sku},
    )


@transaction.atomic
def activate_combo(
    user: User,
    combo_id: Any,
    *,
    request: HttpRequest | None = None,
) -> ProductCombo:
    """Reactiva un combo previamente desactivado."""
    _require_almacenista(user)
    combo = ProductCombo.objects.select_for_update().get(pk=combo_id)
    combo.is_active = True
    combo.save(update_fields=["is_active"])
    log_event(
        AuditEventType.COMBO_ACTIVATED,
        description=f"Combo reactivado: {combo.sku}",
        user=user,
        request=request,
        detail={"combo_id": str(combo.id), "sku": combo.sku},
    )
    return combo


@transaction.atomic
def update_product_prices(
    user: "User",
    product_id: Any,
    *,
    unit_cost: Any = None,
    sale_price_retail: Any = None,
    sale_price_wholesale: Any = None,
    tax_rate_pct: Any = None,
    currency: str | None = None,
    request: "HttpRequest | None" = None,
) -> Product:
    """
    Actualiza los campos de precio de un producto y registra cada cambio en ProductPriceHistory.

    Solo almacenistas pueden ejecutar esta acción.
    Los campos no enviados (None) se dejan intactos.
    """
    _require_almacenista(user)
    product = Product.objects.select_for_update().get(pk=product_id)

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
        detail={"product_id": str(product.id), "fields": list(updates.keys())},
    )
    return product


@transaction.atomic
def deactivate_product(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> None:
    """
    Desactiva un producto (soft delete explícito).

    Raises:
        ValueError: Si el producto pertenece a uno o más combos activos.
    """
    _require_almacenista(user)
    product = Product.objects.select_for_update().get(pk=product_id)
    active_combo_count = ComboItem.objects.filter(
        product=product, combo__is_active=True
    ).count()
    if active_combo_count:
        raise ValueError(
            f"No se puede desactivar el producto porque pertenece a {active_combo_count} "
            f"combo(s) activo(s)."
        )
    product.is_active = False
    product.save(update_fields=["is_active"])
    log_event(
        AuditEventType.PRODUCT_DEACTIVATED,
        description=f"Producto desactivado: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )


@transaction.atomic
def activate_product(
    user: User,
    product_id: Any,
    *,
    request: HttpRequest | None = None,
) -> Product:
    """
    Reactiva un producto previamente desactivado.
    """
    _require_almacenista(user)
    # Fetch the product with a lock. Avoid select_related on nullable subcategory to prevent
    # FOR UPDATE errors on outer joins (PostgreSQL limitation).
    product = (
        Product.objects.select_related("category")
        .select_for_update()
        .get(pk=product_id)
    )
    product.is_active = True
    product.save(update_fields=["is_active"])
    log_event(
        AuditEventType.PRODUCT_ACTIVATED,
        description=f"Producto reactivado: {product.sku}",
        user=user,
        request=request,
        detail={"product_id": str(product.id), "sku": product.sku},
    )
    return product
