"""Servicios de inventario: interfaz pública para stock derivado (RF-004, BR-11)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db import transaction

from apps.alerts.models import Alert, AlertType
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.inventory.models import Location, LocationChoices
from apps.inventory.selectors import reconstruct_stock_from_ledger
from shared.exceptions import DomainValidationError, UnauthorizedDomainActionError

if TYPE_CHECKING:
    from apps.inventory.models import StockByLocation


@transaction.atomic
def trigger_stock_reconstruction(executor: Any, product_id: UUID, location_id: UUID) -> dict[str, Any]:
    """
    RF-004, BR-11 — Ejecuta reconstrucción desde ledger; solo almacenista.

    Si hay discrepancia, crea alerta `STOCK_MISMATCH` y deja traza en auditoría.
    """
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError("Solo el almacenista puede disparar la reconstrucción de stock.")
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
        detail={"product_id": str(product_id), "location_id": str(location_id), **result},
    )
    return result


def get_current_stock(product_id: UUID, location_id: UUID) -> int:
    """
    RF-004 — Cantidad actual en caché `StockByLocation` para producto/ubicación.

    Nota: el valor proviene del stock derivado; la verdad operativa es el ledger.
    """
    from apps.inventory.models import StockByLocation

    row = StockByLocation.objects.filter(product_id=product_id, location_id=location_id).first()
    return int(row.current_stock) if row else 0


@transaction.atomic
def ensure_stock_row_for_tests(product_id: UUID, location_id: UUID, quantity: int) -> StockByLocation:
    """Utilidad interna para pruebas y cargas controladas (no usar en producción desde vistas)."""
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


@transaction.atomic
def create_location(
    executor: Any,
    *,
    code: str,
    name: str,
    description: str = "",
    is_retail: bool = False,
) -> Location:
    """
    RF-004 — Alta de ubicación física (solo almacenista).

    `code` debe ser uno de los códigos ICM (`LocationChoices`).
    """
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError("Solo el almacenista puede crear ubicaciones.")
    code = (code or "").strip().upper()
    if code not in LocationChoices.values:
        raise DomainValidationError(f"Código de ubicación no válido: {code}.")
    if Location.objects.filter(code=code).exists():
        raise DomainValidationError(f"Ya existe una ubicación con código {code}.")
    if is_retail and code != LocationChoices.VITRINA:
        raise DomainValidationError("is_retail=True solo aplica a la ubicación VITRINA (BR-11).")
    return Location.objects.create(
        code=code,
        name=name.strip(),
        description=description or "",
        is_retail=is_retail,
        is_active=True,
    )


@transaction.atomic
def update_location(executor: Any, location_id: UUID, data: dict[str, Any]) -> Location:
    """RF-004 — Actualiza nombre, descripción, banderas de ubicación (solo almacenista)."""
    if getattr(executor, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError("Solo el almacenista puede modificar ubicaciones.")
    loc = Location.objects.select_for_update().get(pk=location_id)
    if "name" in data:
        loc.name = str(data["name"]).strip()
    if "description" in data:
        loc.description = str(data.get("description") or "")
    if "is_retail" in data:
        is_retail = bool(data["is_retail"])
        if is_retail and loc.code != LocationChoices.VITRINA:
            raise DomainValidationError("Solo la vitrina puede marcarse como punto minorista (is_retail).")
        loc.is_retail = is_retail
    if "is_active" in data:
        loc.is_active = bool(data["is_active"])
    loc.save()
    return loc


@transaction.atomic
def deactivate_location(executor: Any, location_id: UUID) -> Location:
    """RF-004 — Desactiva ubicación (no borrado físico)."""
    return update_location(executor, location_id, {"is_active": False})
