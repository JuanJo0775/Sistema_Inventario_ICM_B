"""Servicios del ledger de movimientos (RF-005–RF-009, BR-04–BR-11, BR-13)."""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.alerts import services as alert_services
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.authentication.services import BOGOTA, is_within_operating_hours
from apps.catalog.models import Product
from apps.catalog.services import resolve_identifier
from apps.inventory.models import StockByLocation
from apps.movements.models import InvoiceCounter, Movement, MovementType
from shared.exceptions import (
    AdjustmentJustificationRequiredError,
    AlertAcknowledgementRequiredError,
    CorrectionWindowClosedError,
    CrossValidationFailedError,
    DiscrepancyNoteRequiredError,
    InsufficientStockError,
    ProductNotReturnableError,
    SerialNumberRequiredError,
)

logger = logging.getLogger(__name__)


def _operating_band(local_dt: datetime) -> tuple[str, datetime.date] | None:
    """Retorna ('morning'|'afternoon', date) si está en franja auxiliar; si no, None."""
    t = local_dt.time()
    if time(7, 0) <= t <= time(12, 0):
        return "morning", local_dt.date()
    if time(14, 0) <= t <= time(17, 0):
        return "afternoon", local_dt.date()
    return None


def _same_auxiliar_correction_window(created_at: datetime, *, now: datetime | None = None) -> bool:
    """BR-06 — Misma franja horaria calendario local que la creación."""
    now = now or timezone.now()
    c_local = timezone.localtime(created_at, BOGOTA)
    n_local = timezone.localtime(now, BOGOTA)
    b1 = _operating_band(c_local)
    b2 = _operating_band(n_local)
    return bool(b1 and b2 and b1 == b2)


def _lock_stock(product_id: UUID, location_id: UUID) -> StockByLocation:
    row, _ = (
        StockByLocation.objects.select_for_update()
        .get_or_create(
            product_id=product_id,
            location_id=location_id,
            defaults={"current_stock": 0},
        )
    )
    return row


def _next_invoice_number() -> str:
    """BR-13 — Numeración ICM-0001 atómica (singleton id=1)."""
    row, _ = InvoiceCounter.objects.select_for_update().get_or_create(pk=1, defaults={"last_number": 0})
    row.last_number = int(row.last_number) + 1
    row.save(update_fields=["last_number"])
    return f"ICM-{row.last_number:04d}"


def _try_build_invoice_pdf(
    *,
    invoice_number: str,
    product: Product,
    quantity: int,
    movement_type: str,
) -> ContentFile | None:
    """BR-13 — Genera PDF y lo retorna como ContentFile (sin mutar el movimiento post-insert)."""
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - entorno sin WeasyPrint
        logger.warning("WeasyPrint no disponible: %s", exc)
        return None
    now = timezone.now()
    html = f"""
    <html><head><meta charset="utf-8"/></head><body>
      <h1>ICM — Comprobante</h1>
      <p><strong>Número:</strong> {invoice_number}</p>
      <p><strong>Fecha UTC:</strong> {now}</p>
      <p><strong>SKU:</strong> {product.sku}</p>
      <p><strong>Cantidad:</strong> {quantity}</p>
      <p><strong>Tipo:</strong> {movement_type}</p>
    </body></html>
    """
    pdf_bytes = HTML(string=html).write_pdf()
    return ContentFile(pdf_bytes, name=f"{invoice_number}.pdf")


def _product_allows_returns(product: Product) -> bool:
    """BR-05 — Solo categorías marcadas como retornables."""
    return bool(product.category.is_returnable)


def _requires_ack_flags(product: Product) -> tuple[bool, bool]:
    cold = product.requires_cold_chain
    electric = bool(product.category.requires_serial_number)
    return cold, electric


@transaction.atomic
def register_entry(
    user,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    *,
    serial_number: str | None = None,
    qty_invoiced: int | None = None,
    discrepancy_note: str | None = None,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
) -> Movement:
    """
    RF-005 — Entrada de mercancía.

    Valida BR-04 (serial en categorías que lo exigen) y BR-09 (nota si hay discrepancia).
    """
    product = Product.objects.select_for_update().select_related("category").get(pk=product_id)
    if product.category.requires_serial_number and not (serial_number or "").strip():
        raise SerialNumberRequiredError()
    if qty_invoiced is not None and qty_invoiced != quantity and not (discrepancy_note or "").strip():
        raise DiscrepancyNoteRequiredError()

    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError("Debe reconocer la alerta de cadena de frío.")
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError("Debe reconocer la alerta de seguridad eléctrica.")

    dest = _lock_stock(product_id, location_id)
    before = dest.current_stock
    after = before + quantity
    dest.current_stock = after
    dest.last_movement_at = timezone.now()
    dest.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    movement = Movement.objects.create(
        movement_type=MovementType.ENTRADA,
        product_id=product_id,
        destination_location_id=location_id,
        quantity=quantity,
        stock_previo_destino=before,
        stock_resultante_destino=after,
        serial_number=serial_number,
        quantity_invoiced=qty_invoiced,
        discrepancy_note=discrepancy_note,
        executed_by=user,
    )
    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Entrada de mercancía",
        user=user,
        movement=movement,
        detail={"type": MovementType.ENTRADA},
    )
    alert_services.sync_stock_alerts_for_product(product_id)
    return movement


@transaction.atomic
def register_dispatch(
    user,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    movement_type: str,
    *,
    scanned_code: str,
    order_sku: str,
    customer_data: dict[str, Any] | None = None,
    note: str | None = None,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
    privacy_notice_acknowledged: bool = False,
) -> Movement:
    """
    RF-006, BR-08, BR-11, BR-13 — Salida con validación cruzada y factura digital.

    `scanned_code` debe resolver al mismo SKU que `order_sku`.
    Datos de cliente mayorista (Ley 1581) solo en auditoría, no en el ledger.
    """
    if movement_type not in {
        MovementType.SALIDA_VENTA_MAYOR,
        MovementType.SALIDA_VENTA_MENOR,
        MovementType.SALIDA_DANO,
        MovementType.SALIDA_VENCIMIENTO,
    }:
        raise ValueError("Tipo de salida inválido.")

    scanned_product = resolve_identifier(scanned_code)
    if scanned_product is None or scanned_product.id != product_id:
        raise CrossValidationFailedError(detail={"scanned": scanned_code, "expected_product_id": str(product_id)})
    product = Product.objects.select_related("category").get(pk=product_id)
    if product.sku != order_sku:
        raise CrossValidationFailedError(detail={"resolved_sku": product.sku, "order_sku": order_sku})

    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError("Debe reconocer la alerta de cadena de frío.")
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError("Debe reconocer la alerta de seguridad eléctrica.")

    extra_audit: dict[str, Any] = {}
    if movement_type == MovementType.SALIDA_VENTA_MAYOR:
        cd = customer_data or {}
        required = ("customer_name", "customer_email", "customer_phone", "customer_address")
        missing = [k for k in required if not (cd.get(k) or "").strip()]
        if missing:
            raise CrossValidationFailedError(
                "La venta mayor requiere datos completos del cliente.",
                detail={"missing": missing},
            )
        if not privacy_notice_acknowledged:
            raise CrossValidationFailedError(
                "Debe confirmar el aviso de privacidad (Ley 1581) antes de almacenar datos personales.",
            )
        extra_audit["customer_data"] = cd
    if note:
        extra_audit["note"] = note

    origin = _lock_stock(product_id, location_id)
    if origin.current_stock < quantity:
        raise InsufficientStockError(
            detail={
                "product_id": str(product_id),
                "location_id": str(location_id),
                "available": origin.current_stock,
                "requested": quantity,
            }
        )
    before = origin.current_stock
    after = before - quantity
    origin.current_stock = after
    origin.last_movement_at = timezone.now()
    origin.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    invoice_number = _next_invoice_number()
    pdf_file = _try_build_invoice_pdf(
        invoice_number=invoice_number,
        product=product,
        quantity=quantity,
        movement_type=movement_type,
    )
    movement = Movement.objects.create(
        movement_type=movement_type,
        product_id=product_id,
        origin_location_id=location_id,
        quantity=quantity,
        stock_previo_origen=before,
        stock_resultante_origen=after,
        scanned_code=scanned_code,
        order_sku=order_sku,
        invoice_number=invoice_number,
        invoice_pdf=pdf_file,
        executed_by=user,
    )

    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Salida / despacho",
        user=user,
        movement=movement,
        detail={"type": movement_type, **extra_audit},
    )
    alert_services.sync_stock_alerts_for_product(product_id)
    movement.refresh_from_db()
    return movement


@transaction.atomic
def register_internal_transfer(
    user,
    product_id: UUID,
    origin_id: UUID,
    destination_id: UUID,
    quantity: int,
    *,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
    related_movement: Movement | None = None,
) -> Movement:
    """RF-007, BR-11 — Traslado interno entre ubicaciones."""
    if origin_id == destination_id:
        raise ValueError("Origen y destino deben ser distintos.")

    product = Product.objects.select_related("category").get(pk=product_id)
    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError("Debe reconocer la alerta de cadena de frío.")
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError("Debe reconocer la alerta de seguridad eléctrica.")

    origin = _lock_stock(product_id, origin_id)
    if origin.current_stock < quantity:
        raise InsufficientStockError(
            detail={"location_id": str(origin_id), "available": origin.current_stock, "requested": quantity}
        )
    dest = _lock_stock(product_id, destination_id)

    obo = origin.current_stock
    oao = obo - quantity
    origin.current_stock = oao
    origin.last_movement_at = timezone.now()
    origin.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    dbd = dest.current_stock
    dad = dbd + quantity
    dest.current_stock = dad
    dest.last_movement_at = timezone.now()
    dest.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    movement = Movement.objects.create(
        movement_type=MovementType.TRASLADO,
        product_id=product_id,
        origin_location_id=origin_id,
        destination_location_id=destination_id,
        quantity=quantity,
        stock_previo_origen=obo,
        stock_resultante_origen=oao,
        stock_previo_destino=dbd,
        stock_resultante_destino=dad,
        executed_by=user,
        related_movement=related_movement,
    )
    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Traslado interno",
        user=user,
        movement=movement,
        detail={"type": MovementType.TRASLADO},
    )
    return movement


@transaction.atomic
def register_return(
    user,
    product_id: UUID,
    serial_number: str,
    reason: str,
    product_condition: str,
) -> Movement:
    """
    RF-008, BR-05 — Devolución registrada en ledger (sin alterar stock hasta aprobación).

    La aprobación crea una ENTRADA vinculada (`related_movement`); el stock se deriva del ledger.
    """
    product = Product.objects.select_related("category").get(pk=product_id)
    if not _product_allows_returns(product):
        raise ProductNotReturnableError()
    movement = Movement.objects.create(
        movement_type=MovementType.DEVOLUCION,
        product_id=product_id,
        quantity=1,
        serial_number=serial_number,
        executed_by=user,
    )
    log_event(
        AuditEventType.RETURN_CREATED,
        description=f"Devolución pendiente de aprobación: {reason}",
        user=user,
        movement=movement,
        detail={"reason": reason, "product_condition": product_condition},
    )
    return movement


def _return_has_approval_entry(ret: Movement) -> bool:
    return Movement.objects.filter(
        related_movement_id=ret.pk,
        movement_type=MovementType.ENTRADA,
    ).exists()


@transaction.atomic
def approve_return(almacenista_user, movement_id: UUID, destination_location_id: UUID) -> Movement:
    """RF-008, BR-02 — Aprueba devolución y genera entrada asociada."""
    if getattr(almacenista_user, "role", None) != "almacenista":
        from shared.exceptions import UnauthorizedCredentialManagementError

        raise UnauthorizedCredentialManagementError()
    ret = Movement.objects.select_for_update().get(pk=movement_id)
    if ret.movement_type != MovementType.DEVOLUCION or _return_has_approval_entry(ret):
        raise ValueError("Movimiento de devolución inválido para aprobación.")

    dest = _lock_stock(ret.product_id, destination_location_id)
    before = dest.current_stock
    after = before + ret.quantity
    dest.current_stock = after
    dest.last_movement_at = timezone.now()
    dest.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    entry = Movement.objects.create(
        movement_type=MovementType.ENTRADA,
        product_id=ret.product_id,
        destination_location_id=destination_location_id,
        quantity=ret.quantity,
        stock_previo_destino=before,
        stock_resultante_destino=after,
        serial_number=ret.serial_number,
        related_movement=ret,
        executed_by=almacenista_user,
    )
    log_event(
        AuditEventType.RETURN_APPROVED,
        description="Devolución aprobada; entrada asociada creada",
        user=almacenista_user,
        movement=entry,
        detail={"return_id": str(ret.id)},
    )
    alert_services.sync_stock_alerts_for_product(ret.product_id)
    return entry


@transaction.atomic
def reject_return(almacenista_user, movement_id: UUID, reason: str) -> None:
    """RF-008 — Rechaza devolución (solo auditoría; el registro DEVOLUCION permanece inmutable)."""
    if getattr(almacenista_user, "role", None) != "almacenista":
        from shared.exceptions import UnauthorizedCredentialManagementError

        raise UnauthorizedCredentialManagementError()
    ret = Movement.objects.select_for_update().get(pk=movement_id)
    if ret.movement_type != MovementType.DEVOLUCION or _return_has_approval_entry(ret):
        raise ValueError("Devolución inválida.")
    log_event(
        AuditEventType.RETURN_REJECTED,
        description=f"Devolución rechazada: {reason}",
        user=almacenista_user,
        movement=ret,
        detail={"reason": reason},
    )


@transaction.atomic
def register_adjustment(
    almacenista_user,
    product_id: UUID,
    location_id: UUID,
    new_quantity: int,
    justification: str,
) -> Movement:
    """RF-009, BR-07 — Ajuste formal con delta explícito."""
    if getattr(almacenista_user, "role", None) != "almacenista":
        from shared.exceptions import UnauthorizedCredentialManagementError

        raise UnauthorizedCredentialManagementError()
    if not (justification or "").strip():
        raise AdjustmentJustificationRequiredError()

    row = _lock_stock(product_id, location_id)
    before = row.current_stock
    delta = int(new_quantity) - before
    if delta == 0:
        raise ValueError("El ajuste no cambia el stock.")
    row.current_stock = int(new_quantity)
    row.last_movement_at = timezone.now()
    row.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    origin_id = location_id if delta < 0 else None
    dest_id = location_id if delta > 0 else None
    movement = Movement.objects.create(
        movement_type=MovementType.AJUSTE,
        product_id=product_id,
        origin_location_id=origin_id,
        destination_location_id=dest_id,
        quantity=abs(delta),
        stock_previo_origen=before if delta < 0 else None,
        stock_resultante_origen=int(new_quantity) if delta < 0 else None,
        stock_previo_destino=before if delta > 0 else None,
        stock_resultante_destino=int(new_quantity) if delta > 0 else None,
        justification=justification.strip(),
        executed_by=almacenista_user,
    )
    log_event(
        AuditEventType.ADJUSTMENT_CREATED,
        description="Ajuste de inventario",
        user=almacenista_user,
        movement=movement,
        detail={},
    )
    alert_services.sync_stock_alerts_for_product(product_id)
    return movement


@transaction.atomic
def correct_movement_within_window(user, movement_id: UUID, corrected_data: dict[str, Any]) -> list[Movement]:
    """
    BR-06 — Autocorrección de traslado dentro de la misma franja horaria.

    Implementación: traslado inverso + traslado corregido; sin mutar el movimiento original (BR-10).
    """
    original = Movement.objects.select_related("product").get(pk=movement_id)
    if original.movement_type != MovementType.TRASLADO:
        raise ValueError("Solo se soporta corrección de traslados en esta versión base.")
    if original.executed_by_id != user.id:
        raise CorrectionWindowClosedError("Solo el autor del movimiento puede corregirlo.")
    if getattr(user, "role", None) == "auxiliar_despacho" and not _same_auxiliar_correction_window(original.created_at):
        raise CorrectionWindowClosedError()
    if getattr(user, "role", None) == "auxiliar_despacho" and not is_within_operating_hours():
        raise CorrectionWindowClosedError("Fuera de horario operativo.")

    new_origin = UUID(str(corrected_data["origin_id"]))
    new_dest = UUID(str(corrected_data["destination_id"]))
    new_qty = int(corrected_data["quantity"])
    if new_origin == new_dest:
        raise ValueError("Origen y destino deben ser distintos.")

    rev = register_internal_transfer(
        user,
        original.product_id,
        UUID(str(original.destination_location_id)),
        UUID(str(original.origin_location_id)),
        int(original.quantity),
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
    )

    fixed = register_internal_transfer(
        user,
        original.product_id,
        new_origin,
        new_dest,
        new_qty,
        cold_chain_acknowledged=True,
        electrical_safety_acknowledged=True,
        related_movement=original,
    )

    log_event(
        AuditEventType.MOVEMENT_CORRECTED,
        description="Corrección de traslado (BR-06)",
        user=user,
        movement=fixed,
        detail={"original_id": str(original.id), "reversal_movement_id": str(rev.id)},
    )
    return [rev, fixed]


def ledger_net_quantity_for_location(*, product_id: UUID, location_id: UUID) -> int:
    """
    Suma algebraica inferida desde el ledger para verificación de consistencia.

    Convención: entradas suman en destino; salidas restan en origen; traslados afectan ambos.
    Las DEVOLUCION no suman hasta que exista ENTRADA vinculada (se cuenta la ENTRADA).
    """
    total = 0
    qs = Movement.objects.filter(product_id=product_id).order_by("created_at")
    for m in qs.iterator():
        if m.movement_type == MovementType.ENTRADA and m.destination_location_id == location_id:
            total += m.quantity
        elif m.movement_type in {
            MovementType.SALIDA_VENTA_MAYOR,
            MovementType.SALIDA_VENTA_MENOR,
            MovementType.SALIDA_DANO,
            MovementType.SALIDA_VENCIMIENTO,
        }:
            if m.origin_location_id == location_id:
                total -= m.quantity
        elif m.movement_type == MovementType.TRASLADO:
            if m.origin_location_id == location_id:
                total -= m.quantity
            if m.destination_location_id == location_id:
                total += m.quantity
        elif m.movement_type == MovementType.AJUSTE:
            if m.destination_location_id == location_id:
                total += m.quantity
            if m.origin_location_id == location_id:
                total -= m.quantity
    return total
