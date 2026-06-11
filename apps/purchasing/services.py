"""
Lógica de negocio del módulo de compras.

Principio crítico: La actualización de stock NUNCA ocurre aquí directamente.
confirm_reception() delega cada entrada a movements.services.register_entry(),
garantizando que el ledger sea la única fuente de verdad.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.inventory.models import Location
from apps.movements import services as movements_services
from shared.exceptions import DomainValidationError

from .exceptions import (
    InvalidPOStatusTransitionError,
    POCancellationReasonRequiredError,
    POHasConfirmedReceptionsError,
    POItemQuantityExceededError,
    PONotReceivableError,
    PurchaseOrderImmutableError,
    ReceptionAllocationQuantityMismatchError,
    ReceptionDiscrepancyNoteRequiredError,
    ReceptionEmptyError,
    ReceptionNotInBorradorError,
    SupplierInactiveError,
    SupplierNITDuplicateError,
)
from .models import (
    PurchaseOrder,
    PurchaseOrderCounter,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    Reception,
    ReceptionItem,
    ReceptionItemAllocation,
    ReceptionStatus,
    Supplier,
)

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _next_po_number() -> str:
    """Genera el siguiente número de OC de forma atómica (igual que InvoiceCounter)."""
    row, _ = PurchaseOrderCounter.objects.select_for_update().get_or_create(
        pk=1, defaults={"last_number": 0}
    )
    row.last_number = int(row.last_number) + 1
    row.save(update_fields=["last_number"])
    return f"OC-{row.last_number:04d}"


def _update_po_status_from_receptions(po: PurchaseOrder) -> None:
    """Recalcula el status de la OC según la proporción de ítems recibidos."""
    items = list(po.items.all())
    if not items:
        return

    all_received = all(item.is_fully_received for item in items)
    any_received = any(item.quantity_received > 0 for item in items)

    if all_received:
        po.status = PurchaseOrderStatus.COMPLETADA
    elif any_received:
        po.status = PurchaseOrderStatus.PARCIALMENTE_RECIBIDA
    po.save(update_fields=["status", "updated_at"])


def _resolve_allocation_lot_values(
    *,
    item_lot_code: str | None,
    item_lot_expiration_date,
    allocation_lot_code: str | None,
    allocation_lot_expiration_date,
) -> tuple[str | None, Any | None]:
    """Resuelve lote/fecha de una porción avanzando con fallback al ítem."""
    lot_code = (allocation_lot_code or item_lot_code or "").strip() or None
    lot_expiration_date = allocation_lot_expiration_date or item_lot_expiration_date
    return lot_code, lot_expiration_date


# ---------------------------------------------------------------------------
# Servicios de Proveedor
# ---------------------------------------------------------------------------


@transaction.atomic
def create_supplier(created_by, data: dict[str, Any], *, request=None) -> Supplier:
    """Registra un nuevo proveedor. Solo almacenista."""
    nit = (data.get("nit") or "").strip() or None
    if nit and Supplier.objects.filter(nit=nit).exists():
        raise SupplierNITDuplicateError()

    supplier = Supplier.objects.create(
        nombre_comercial=data["nombre_comercial"],
        razon_social=data.get("razon_social", data["nombre_comercial"]),
        nit=nit,
        pais=data.get("pais", "Colombia"),
        correo=data.get("correo", ""),
        telefono=data.get("telefono", ""),
        ciudad=data.get("ciudad", ""),
        direccion=data.get("direccion", ""),
        observaciones=data.get("observaciones", ""),
        created_by=created_by,
    )

    log_event(
        AuditEventType.SUPPLIER_CREATED,
        description=f"Proveedor '{supplier.nombre_comercial}' (NIT {supplier.nit}) creado.",
        user=created_by,
        request=request,
        metadata={"supplier_id": str(supplier.id), "nit": supplier.nit},
    )
    return supplier


@transaction.atomic
def update_supplier(
    executor, supplier_id: uuid.UUID, data: dict[str, Any], *, request=None
) -> Supplier:
    """Actualiza datos de un proveedor existente. Solo almacenista."""
    supplier = Supplier.objects.select_for_update().get(pk=supplier_id)

    if "nit" in data:
        new_nit = (data["nit"] or "").strip() or None
        if new_nit != supplier.nit:
            if (
                new_nit
                and Supplier.objects.filter(nit=new_nit)
                .exclude(pk=supplier.pk)
                .exists()
            ):
                raise SupplierNITDuplicateError()
            supplier.nit = new_nit

    for field in (
        "nombre_comercial",
        "razon_social",
        "pais",
        "correo",
        "telefono",
        "ciudad",
        "direccion",
        "observaciones",
    ):
        if field in data:
            setattr(supplier, field, data[field])

    supplier.save()

    log_event(
        AuditEventType.SUPPLIER_UPDATED,
        description=f"Proveedor '{supplier.nombre_comercial}' actualizado.",
        user=executor,
        request=request,
        metadata={"supplier_id": str(supplier.id)},
    )
    return supplier


@transaction.atomic
def deactivate_supplier(executor, supplier_id: uuid.UUID, *, request=None) -> Supplier:
    """Desactiva un proveedor. No cancela OC existentes."""
    supplier = Supplier.objects.select_for_update().get(pk=supplier_id)
    supplier.is_active = False
    supplier.save(update_fields=["is_active", "updated_at"])

    log_event(
        AuditEventType.SUPPLIER_DEACTIVATED,
        description=f"Proveedor '{supplier.nombre_comercial}' desactivado.",
        user=executor,
        request=request,
        metadata={"supplier_id": str(supplier.id)},
    )
    return supplier


@transaction.atomic
def activate_supplier(executor, supplier_id: uuid.UUID, *, request=None) -> Supplier:
    """Reactiva un proveedor previamente desactivado."""
    supplier = Supplier.objects.select_for_update().get(pk=supplier_id)
    supplier.is_active = True
    supplier.save(update_fields=["is_active", "updated_at"])

    log_event(
        AuditEventType.SUPPLIER_ACTIVATED,
        description=f"Proveedor '{supplier.nombre_comercial}' reactivado.",
        user=executor,
        request=request,
        metadata={"supplier_id": str(supplier.id)},
    )
    return supplier


# ---------------------------------------------------------------------------
# Servicios de Orden de Compra
# ---------------------------------------------------------------------------


@transaction.atomic
def create_purchase_order(
    created_by, data: dict[str, Any], *, request=None
) -> PurchaseOrder:
    """
    Crea una OC en estado BORRADOR con sus ítems de línea.

    data = {
        "supplier_id": UUID,
        "expected_delivery": date | None,
        "notes": str,
        "items": [{"product_id": UUID, "quantity_ordered": int, "unit_cost": Decimal, "notes": str}]
    }
    """
    supplier = Supplier.objects.select_for_update().get(pk=data["supplier_id"])
    if not supplier.is_active:
        raise SupplierInactiveError()

    number = _next_po_number()

    po = PurchaseOrder.objects.create(
        number=number,
        supplier=supplier,
        expected_delivery=data.get("expected_delivery"),
        notes=data.get("notes", ""),
        created_by=created_by,
    )

    for item_data in data.get("items", []):
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product_id=item_data["product_id"],
            quantity_ordered=int(item_data["quantity_ordered"]),
            unit_cost=item_data["unit_cost"],
            notes=item_data.get("notes", ""),
        )

    log_event(
        AuditEventType.PURCHASE_ORDER_CREATED,
        description=f"OC {po.number} creada para proveedor '{supplier.nombre_comercial}'.",
        user=created_by,
        request=request,
        metadata={
            "po_id": str(po.id),
            "po_number": po.number,
            "supplier_id": str(supplier.id),
            "items_count": po.items.count(),
        },
    )
    return po


@transaction.atomic
def update_purchase_order(
    executor, po_id: uuid.UUID, data: dict[str, Any], *, request=None
) -> PurchaseOrder:
    """Actualiza una OC en estado BORRADOR. Solo se puede editar antes de confirmar."""
    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
    if not po.is_editable:
        raise PurchaseOrderImmutableError(
            f"La OC {po.number} no puede modificarse en estado '{po.status}'."
        )

    for field in ("expected_delivery", "notes"):
        if field in data:
            setattr(po, field, data[field])
    po.save()

    # Recreate items if provided in update payload
    if "items" in data:
        po.items.all().delete()
        for item_data in data["items"]:
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product_id=item_data["product_id"],
                quantity_ordered=int(item_data["quantity_ordered"]),
                unit_cost=item_data["unit_cost"],
                notes=item_data.get("notes", ""),
            )

    log_event(
        AuditEventType.PURCHASE_ORDER_UPDATED,
        user=executor,
        detail={
            "purchase_order_id": str(po.id),
            "po_number": po.number,
            "updated_fields": list(data.keys()),
            "_entity_type": "PurchaseOrder",
            "_entity_id": str(po.id),
            "_origin": "API",
        },
    )
    return po


@transaction.atomic
def confirm_purchase_order(
    executor, po_id: uuid.UUID, *, request=None
) -> PurchaseOrder:
    """BORRADOR → PENDIENTE. La OC queda bloqueada para modificaciones."""
    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)

    if po.status != PurchaseOrderStatus.BORRADOR:
        raise InvalidPOStatusTransitionError(
            f"Solo se puede confirmar una OC en estado BORRADOR. Estado actual: '{po.status}'."
        )

    po.status = PurchaseOrderStatus.PENDIENTE
    po.confirmed_by = executor
    po.confirmed_at = timezone.now()
    po.save(update_fields=["status", "confirmed_by", "confirmed_at", "updated_at"])

    log_event(
        AuditEventType.PURCHASE_ORDER_CONFIRMED,
        description=f"OC {po.number} confirmada — estado PENDIENTE.",
        user=executor,
        request=request,
        metadata={"po_id": str(po.id), "po_number": po.number},
    )
    return po


@transaction.atomic
def cancel_purchase_order(
    executor, po_id: uuid.UUID, reason: str, *, request=None
) -> PurchaseOrder:
    """
    Cancela una OC. Solo posible desde BORRADOR o PENDIENTE.
    No se puede cancelar si ya hay recepciones CONFIRMADAS.
    """
    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)

    if po.status in (PurchaseOrderStatus.COMPLETADA, PurchaseOrderStatus.CANCELADA):
        raise InvalidPOStatusTransitionError(
            f"No se puede cancelar una OC en estado '{po.status}'."
        )

    if not (reason or "").strip():
        raise POCancellationReasonRequiredError()

    confirmed_receptions = po.receptions.filter(
        status=ReceptionStatus.CONFIRMADA
    ).count()
    if confirmed_receptions > 0:
        raise POHasConfirmedReceptionsError()

    po.status = PurchaseOrderStatus.CANCELADA
    po.cancelled_by = executor
    po.cancelled_at = timezone.now()
    po.cancellation_reason = reason.strip()
    po.save(
        update_fields=[
            "status",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "updated_at",
        ]
    )

    log_event(
        AuditEventType.PURCHASE_ORDER_CANCELLED,
        description=f"OC {po.number} cancelada. Motivo: {reason.strip()}",
        user=executor,
        request=request,
        metadata={
            "po_id": str(po.id),
            "po_number": po.number,
            "reason": reason.strip(),
        },
    )
    return po


# ---------------------------------------------------------------------------
# Servicios de Recepción
# ---------------------------------------------------------------------------


@transaction.atomic
def create_reception(
    received_by, po_id: uuid.UUID, data: dict[str, Any], *, request=None
) -> Reception:
    """
    RF-005 / BR-11 — Crea una Recepción en estado BORRADOR asociada a una OC.

    Soporta modo simple (una ubicación destino por recepción) y modo avanzado
    con distribuciones por porción de stock, lote y ubicación.

    data = {
        "destination_location_id": UUID,
        "notes": str,
        "items": [
            {
                "purchase_order_item_id": UUID,
                "quantity_received": int,
                "lot_code": str,
                "lot_expiration_date": date | None,
                "discrepancy_note": str,
            }
        ]
    }
    """
    po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
    if not po.is_receivable:
        raise PONotReceivableError(
            f"La OC {po.number} está en estado '{po.status}' y no acepta recepciones."
        )

    location = Location.objects.filter(pk=data["destination_location_id"]).first()
    if location is None:
        raise DomainValidationError("La ubicación de destino no existe.")

    reception = Reception.objects.create(
        purchase_order=po,
        destination_location=location,
        received_by=received_by,
        notes=data.get("notes", ""),
    )

    for item_data in data.get("items", []):
        poi = PurchaseOrderItem.objects.get(
            pk=item_data["purchase_order_item_id"],
            purchase_order=po,
        )
        qty = int(item_data.get("quantity_received", 0))

        # Valida que no supere lo pendiente
        if qty > poi.quantity_pending:
            raise POItemQuantityExceededError(
                f"La cantidad a recibir ({qty}) supera la pendiente ({poi.quantity_pending}) "
                f"para el producto '{poi.product}'."
            )

        item = ReceptionItem.objects.create(
            reception=reception,
            purchase_order_item=poi,
            quantity_received=qty,
            lot_code=item_data.get("lot_code", ""),
            lot_expiration_date=item_data.get("lot_expiration_date"),
            discrepancy_note=item_data.get("discrepancy_note", ""),
        )

        allocations = list(item_data.get("allocations") or [])
        if allocations:
            total_allocated = sum(
                int(a.get("quantity_received", 0)) for a in allocations
            )
            if total_allocated != qty:
                raise ReceptionAllocationQuantityMismatchError(
                    detail={
                        "purchase_order_item_id": str(poi.id),
                        "quantity_received": qty,
                        "allocated": total_allocated,
                    }
                )
            for allocation_data in allocations:
                allocation_location = Location.objects.filter(
                    pk=allocation_data["location_id"]
                ).first()
                if allocation_location is None:
                    raise DomainValidationError(
                        "Una de las ubicaciones de distribución no existe."
                    )
                ReceptionItemAllocation.objects.create(
                    reception_item=item,
                    location=allocation_location,
                    quantity_received=int(allocation_data["quantity_received"]),
                    lot_code=(allocation_data.get("lot_code") or "").strip() or None,
                    lot_expiration_date=allocation_data.get("lot_expiration_date"),
                )

    log_event(
        AuditEventType.RECEPTION_CREATED,
        description=f"Recepción {reception.id} creada en BORRADOR para OC {po.number}.",
        user=received_by,
        request=request,
        metadata={
            "reception_id": str(reception.id),
            "po_id": str(po.id),
            "po_number": po.number,
            "location_id": str(location.id),
        },
    )
    return reception


@transaction.atomic
def confirm_reception(executor, reception_id: uuid.UUID, *, request=None) -> Reception:
    """
    RF-005 / BR-11 — BORRADOR → CONFIRMADA.

    Por cada ReceptionItem con qty > 0:
    1. Valida discrepancy_note si qty difiere de lo esperado.
    2. Si el ítem tiene allocaciones, crea un Movement por cada porción.
    3. Si no tiene allocaciones, usa el flujo simple con una sola ubicación.
    4. Llama movements.services.register_entry() — NUNCA toca StockByLocation directamente.
    5. Enlaza los movimientos generados a la recepción.
    6. Actualiza PurchaseOrderItem.quantity_received.
    7. Recalcula PurchaseOrder.status.
    8. Marca la recepción como CONFIRMADA.
    """
    reception = (
        Reception.objects.select_for_update()
        .select_related("purchase_order", "destination_location", "received_by")
        .get(pk=reception_id)
    )

    if reception.status != ReceptionStatus.BORRADOR:
        raise ReceptionNotInBorradorError()

    # Lock PO para evitar condición de carrera con otras recepciones
    po = PurchaseOrder.objects.select_for_update().get(pk=reception.purchase_order_id)

    items = list(
        reception.items.select_related("purchase_order_item__product")
        .prefetch_related(
            "allocations__location",
            "allocations__movement",
        )
        .all()
    )

    active_items = [item for item in items if item.quantity_received > 0]
    if not active_items:
        raise ReceptionEmptyError()

    # Validar discrepancias antes de iniciar movimientos
    for item in active_items:
        expected = item.quantity_expected
        if item.quantity_received != expected and not item.discrepancy_note.strip():
            raise ReceptionDiscrepancyNoteRequiredError(
                f"Ítem con producto '{item.purchase_order_item.product}': "
                f"cantidad recibida ({item.quantity_received}) difiere de la esperada ({expected}). "
                f"Debe registrar una nota de discrepancia."
            )

    # Validar ubicación operativa (BR-14)
    from shared.exceptions import LocationStateNotAllowedError

    location = reception.destination_location
    if location.operational_status not in ("active", "restricted"):
        raise LocationStateNotAllowedError(
            f"La ubicación '{location.name}' tiene estado '{location.operational_status}' "
            f"y no permite recepciones de mercancía."
        )

    movement_ids = []

    for item in active_items:
        poi = item.purchase_order_item
        product = poi.product

        allocations = list(item.allocations.all())
        if allocations:
            total_allocated = sum(a.quantity_received for a in allocations)
            if total_allocated != item.quantity_received:
                raise ReceptionAllocationQuantityMismatchError(
                    detail={
                        "reception_item_id": str(item.id),
                        "quantity_received": item.quantity_received,
                        "allocated": total_allocated,
                    }
                )

            last_movement = None
            for allocation in allocations:
                lot_code, lot_expiration_date = _resolve_allocation_lot_values(
                    item_lot_code=item.lot_code,
                    item_lot_expiration_date=item.lot_expiration_date,
                    allocation_lot_code=allocation.lot_code,
                    allocation_lot_expiration_date=allocation.lot_expiration_date,
                )
                movement = movements_services.register_entry(
                    executor,
                    product_id=product.id,
                    quantity=allocation.quantity_received,
                    location_id=allocation.location_id,
                    lot_code=lot_code,
                    lot_expiration_date=lot_expiration_date,
                    qty_invoiced=allocation.quantity_received,
                    discrepancy_note=item.discrepancy_note or None,
                    unit_cost=poi.unit_cost,
                )
                allocation.movement = movement
                allocation.save(update_fields=["movement", "updated_at"])
                movement_ids.append(str(movement.id))
                last_movement = movement

            if len(allocations) == 1 and last_movement is not None:
                item.movement = last_movement
                item.save(update_fields=["movement", "updated_at"])
        else:
            movement = movements_services.register_entry(
                executor,
                product_id=product.id,
                quantity=item.quantity_received,
                location_id=reception.destination_location_id,
                lot_code=item.lot_code or None,
                lot_expiration_date=item.lot_expiration_date,
                qty_invoiced=item.quantity_received,
                discrepancy_note=item.discrepancy_note or None,
                unit_cost=poi.unit_cost,
            )

            item.movement = movement
            item.save(update_fields=["movement", "updated_at"])
            movement_ids.append(str(movement.id))

        poi.quantity_received = (poi.quantity_received or 0) + item.quantity_received
        poi.save(update_fields=["quantity_received", "updated_at"])

    reception.status = ReceptionStatus.CONFIRMADA
    reception.confirmed_at = timezone.now()
    reception.save(update_fields=["status", "confirmed_at", "updated_at"])

    # Refresca los ítems de la OC para calcular nuevo status
    po.refresh_from_db()
    _update_po_status_from_receptions(po)

    log_event(
        AuditEventType.RECEPTION_CONFIRMED,
        description=(
            f"Recepción {reception.id} confirmada para OC {po.number}. "
            f"{len(movement_ids)} movimiento(s) de entrada generados."
        ),
        user=executor,
        request=request,
        metadata={
            "reception_id": str(reception.id),
            "po_id": str(po.id),
            "po_number": po.number,
            "movement_ids": movement_ids,
            "po_status_after": po.status,
        },
    )
    return reception


@transaction.atomic
def cancel_reception(executor, reception_id: uuid.UUID, *, request=None) -> Reception:
    """Cancela una recepción en estado BORRADOR. No tiene efecto en inventario."""
    reception = Reception.objects.select_for_update().get(pk=reception_id)

    if reception.status != ReceptionStatus.BORRADOR:
        raise ReceptionNotInBorradorError(
            "Solo se pueden cancelar recepciones en estado BORRADOR."
        )

    reception.status = ReceptionStatus.CANCELADA
    reception.save(update_fields=["status", "updated_at"])

    log_event(
        AuditEventType.RECEPTION_CANCELLED,
        description=f"Recepción {reception.id} cancelada (sin efecto en inventario).",
        user=executor,
        request=request,
        metadata={
            "reception_id": str(reception.id),
            "po_id": str(reception.purchase_order_id),
        },
    )
    return reception
