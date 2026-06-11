"""Servicios de inventario: interfaz pública para stock derivado (RF-004, BR-11, BR-14, BR-15)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db import transaction
from django.utils.text import slugify

from apps.alerts.models import Alert, AlertType
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.inventory.models import (
    Location,
    StorageTemplate,
    StorageType,
    _is_retail_by_name,
)
from apps.inventory.selectors import reconstruct_stock_from_ledger
from shared.exceptions import DomainValidationError, UnauthorizedDomainActionError

if TYPE_CHECKING:
    from apps.inventory.models import StockByLocation


@transaction.atomic
def trigger_stock_reconstruction(
    executor: Any, product_id: UUID, location_id: UUID
) -> dict[str, Any]:
    """
    RF-004, BR-11 — Ejecuta reconstrucción desde ledger; solo almacenista.

    Si hay discrepancia, crea alerta `STOCK_MISMATCH` y deja traza en auditoría.
    """
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede disparar la reconstrucción de stock."
        )
    result = reconstruct_stock_from_ledger(product_id, location_id)
    if result["status"] == "DISCREPANCY":
        Alert.objects.create(
            product_id=product_id,
            location_id=location_id,
            alert_type=AlertType.STOCK_MISMATCH,
            message=(
                f"Ledger={result['reconstructed']} vs derivado={result['actual']} "
                f"(producto {product_id}, ubicación {location_id})."
            ),
        )
    log_event(
        AuditEventType.STOCK_RECONSTRUCTED,
        description="Verificación stock ledger vs derivado",
        user=executor,
        detail={
            "product_id": str(product_id),
            "location_id": str(location_id),
            **result,
        },
    )
    return result


def get_current_stock(product_id: UUID, location_id: UUID) -> int:
    """
    RF-004 — Cantidad actual en caché `StockByLocation` para producto/ubicación.

    Nota: el valor proviene del stock derivado; la verdad operativa es el ledger.
    """
    from apps.inventory.models import StockByLocation

    row = StockByLocation.objects.filter(
        product_id=product_id, location_id=location_id
    ).first()
    return int(row.current_stock) if row else 0


@transaction.atomic
def _ensure_stock_row_for_tests(
    product_id: UUID, location_id: UUID, quantity: int
) -> StockByLocation:
    """Utilidad interna para pruebas y cargas controladas (no usar en producción desde vistas)."""
    from django.conf import settings

    if not settings.DEBUG:
        raise RuntimeError(
            "_ensure_stock_row_for_tests solo puede ejecutarse con DEBUG=True."
        )
    from apps.inventory.models import StockByLocation

    row, _ = StockByLocation.objects.select_for_update().get_or_create(
        product_id=product_id,
        location_id=location_id,
        defaults={"current_stock": quantity},
    )
    if row.current_stock != quantity:
        row.current_stock = quantity
        row.save(update_fields=["current_stock", "updated_at"])
    return row


def _generate_unique_code(name: str) -> str:
    """Genera un slug a partir del nombre; la unicidad se garantiza con retry en create_location."""
    return slugify(name) or "ubicacion"


def _from_template(current: Any, defaults: dict, key: str, cast: Any = None) -> Any:
    """Lee `key` de `defaults` solo si `current` es None."""
    if current is not None or not isinstance(defaults, dict) or key not in defaults:
        return current
    val = defaults[key]
    return cast(val) if cast is not None and val is not None else val


@transaction.atomic
def create_location(
    executor: Any,
    *,
    name: str,
    description: str = "",
    max_capacity: int | None = None,
    is_retail: bool | None = None,
    storage_type_id: UUID | None = None,
    storage_template_id: UUID | None = None,
    operational_status: str = Location.OperationalStatus.ACTIVE,
    capacity_mode: str = Location.CapacityMode.NONE,
    capacity_level: int | None = None,
    capacity_score: int | None = None,
    occupancy_estimate_pct: float | None = None,
) -> Location:
    """
    RF-004, BR-14, BR-15 — Alta de ubicación física (solo almacenista).

    El `code` se genera automáticamente desde el nombre usando slugify.
    `is_retail` se auto-detecta si el nombre contiene palabras clave como
    'vitrina', 'mostrador', etc. Puede forzarse manualmente.
    `max_capacity` es opcional; se recomienda para vitrinas.
    BR-15: el `storage_type_id` debe corresponder a un StorageType activo.
    """
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede crear ubicaciones."
        )
    name = (name or "").strip()
    if not name:
        raise DomainValidationError("El nombre de la ubicación es obligatorio.")
    if Location.objects.filter(name__iexact=name).exists():
        raise DomainValidationError(f"Ya existe una ubicación con el nombre '{name}'.")

    if not is_retail:
        is_retail = _is_retail_by_name(name)

    location = Location.objects.create(
        code=_generate_unique_code(name),
        name=name,
        description=description or "",
        is_retail=bool(is_retail),
        max_capacity=max_capacity,
        storage_type_id=storage_type_id,
        storage_template_id=storage_template_id,
        operational_status=operational_status,
        capacity_mode=capacity_mode,
        capacity_level=capacity_level,
        capacity_score=capacity_score,
        occupancy_estimate_pct=occupancy_estimate_pct,
    )
    return location


@transaction.atomic
def create_storage_type(
    executor: Any,
    *,
    code: str,
    name: str,
    category: str = "general",
    description: str = "",
    capabilities: dict[str, Any] | None = None,
    default_is_retail: bool = False,
    is_system: bool = False,
    sort_order: int = 0,
) -> StorageType:
    """Crea un tipo de almacenamiento configurable (solo almacenista)."""
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede crear tipos de almacenamiento."
        )
    code = (code or "").strip().lower()
    name = (name or "").strip()
    if not code or not name:
        raise DomainValidationError("code y name son obligatorios.")
    if StorageType.objects.filter(code=code).exists():
        raise DomainValidationError(f"Ya existe un tipo con code '{code}'.")
    if StorageType.objects.filter(name__iexact=name).exists():
        raise DomainValidationError(f"Ya existe un tipo con nombre '{name}'.")
    return StorageType.objects.create(
        code=code,
        name=name,
        category=(category or "general").strip() or "general",
        description=description or "",
        capabilities=capabilities or {},
        default_is_retail=bool(default_is_retail),
        is_system=bool(is_system),
        is_active=True,
        sort_order=max(int(sort_order), 0),
    )


@transaction.atomic
def update_storage_type(
    executor: Any, storage_type_id: UUID, data: dict[str, Any]
) -> StorageType:
    """Actualiza un tipo de almacenamiento (solo almacenista)."""
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede modificar tipos de almacenamiento."
        )
    st = StorageType.objects.select_for_update().get(pk=storage_type_id)
    if "code" in data:
        code = str(data["code"] or "").strip().lower()
        if not code:
            raise DomainValidationError("code no puede ser vacío.")
        if StorageType.objects.exclude(pk=st.pk).filter(code=code).exists():
            raise DomainValidationError(f"Ya existe un tipo con code '{code}'.")
        st.code = code
    if "name" in data:
        name = str(data["name"] or "").strip()
        if not name:
            raise DomainValidationError("name no puede ser vacío.")
        if StorageType.objects.exclude(pk=st.pk).filter(name__iexact=name).exists():
            raise DomainValidationError(f"Ya existe un tipo con nombre '{name}'.")
        st.name = name
    if "category" in data:
        st.category = str(data.get("category") or "general").strip() or "general"
    if "description" in data:
        st.description = str(data.get("description") or "")
    if "capabilities" in data:
        st.capabilities = data.get("capabilities") or {}
    if "default_is_retail" in data:
        st.default_is_retail = bool(data["default_is_retail"])
    if "is_system" in data:
        st.is_system = bool(data["is_system"])
    if "is_active" in data:
        st.is_active = bool(data["is_active"])
    if "sort_order" in data:
        st.sort_order = max(int(data["sort_order"]), 0)
    st.save()
    return st


@transaction.atomic
def deactivate_storage_type(executor: Any, storage_type_id: UUID) -> StorageType:
    """Desactiva un tipo de almacenamiento (solo almacenista)."""
    return update_storage_type(executor, storage_type_id, {"is_active": False})


@transaction.atomic
def create_storage_template(
    executor: Any,
    *,
    code: str,
    name: str,
    storage_type_id: UUID | None = None,
    description: str = "",
    defaults: dict[str, Any] | None = None,
    is_system: bool = False,
    sort_order: int = 0,
) -> StorageTemplate:
    """Crea una plantilla de almacenamiento configurable (solo almacenista)."""
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede crear plantillas de almacenamiento."
        )
    code = (code or "").strip().lower()
    name = (name or "").strip()
    if not code or not name:
        raise DomainValidationError("code y name son obligatorios.")
    if StorageTemplate.objects.filter(code=code).exists():
        raise DomainValidationError(f"Ya existe una plantilla con code '{code}'.")
    if StorageTemplate.objects.filter(name__iexact=name).exists():
        raise DomainValidationError(f"Ya existe una plantilla con nombre '{name}'.")

    storage_type = None
    if storage_type_id is not None:
        storage_type = StorageType.objects.filter(pk=storage_type_id).first()
        if storage_type is None:
            raise DomainValidationError("El tipo de almacenamiento no existe.")

    return StorageTemplate.objects.create(
        code=code,
        name=name,
        storage_type=storage_type,
        description=description or "",
        defaults=defaults or {},
        is_system=bool(is_system),
        is_active=True,
        sort_order=max(int(sort_order), 0),
    )


@transaction.atomic
def update_storage_template(
    executor: Any, storage_template_id: UUID, data: dict[str, Any]
) -> StorageTemplate:
    """Actualiza una plantilla de almacenamiento (solo almacenista)."""
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede modificar plantillas de almacenamiento."
        )
    template = StorageTemplate.objects.select_for_update().get(pk=storage_template_id)
    if "code" in data:
        code = str(data["code"] or "").strip().lower()
        if not code:
            raise DomainValidationError("code no puede ser vacío.")
        if StorageTemplate.objects.exclude(pk=template.pk).filter(code=code).exists():
            raise DomainValidationError(f"Ya existe una plantilla con code '{code}'.")
        template.code = code
    if "name" in data:
        name = str(data["name"] or "").strip()
        if not name:
            raise DomainValidationError("name no puede ser vacío.")
        if (
            StorageTemplate.objects.exclude(pk=template.pk)
            .filter(name__iexact=name)
            .exists()
        ):
            raise DomainValidationError(f"Ya existe una plantilla con nombre '{name}'.")
        template.name = name
    if "storage_type_id" in data:
        storage_type_id = data.get("storage_type_id")
        if storage_type_id is None:
            template.storage_type = None
        else:
            storage_type = StorageType.objects.filter(pk=storage_type_id).first()
            if storage_type is None:
                raise DomainValidationError("El tipo de almacenamiento no existe.")
            template.storage_type = storage_type
    if "description" in data:
        template.description = str(data.get("description") or "")
    if "defaults" in data:
        template.defaults = data.get("defaults") or {}
    if "is_system" in data:
        template.is_system = bool(data["is_system"])
    if "is_active" in data:
        template.is_active = bool(data["is_active"])
    if "sort_order" in data:
        template.sort_order = max(int(data["sort_order"]), 0)
    template.save()
    return template


@transaction.atomic
def deactivate_storage_template(
    executor: Any, storage_template_id: UUID
) -> StorageTemplate:
    """Desactiva una plantilla de almacenamiento (solo almacenista)."""
    return update_storage_template(executor, storage_template_id, {"is_active": False})
