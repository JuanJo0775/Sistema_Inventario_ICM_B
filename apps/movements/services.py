"""Servicios del ledger de movimientos (RF-005–RF-009, BR-04–BR-11, BR-13)."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.alerts import services as alert_services
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.catalog.models import Product
from apps.catalog.services import resolve_identifier
from apps.inventory.models import Location, StockByLocation
from apps.movements.models import InvoiceCounter, Movement, MovementType
from shared.exceptions import (AdjustmentJustificationRequiredError,
                               AlertAcknowledgementRequiredError,
                               CrossValidationFailedError,
                               DiscrepancyNoteRequiredError,
                               ImmutableRecordError, InsufficientStockError,
                               PrivacyConsentRequiredError,
                               ProductNotReturnableError,
                               SerialNumberRequiredError, StockMismatchError,
                               UnauthorizedDomainActionError)

logger = logging.getLogger(__name__)


def _lock_stock(product_id: UUID, location_id: UUID) -> StockByLocation:
    row, _ = StockByLocation.objects.select_for_update().get_or_create(
        product_id=product_id,
        location_id=location_id,
        defaults={"current_stock": 0},
    )
    return row


def _consolidated_stock_total(*, product_id: UUID) -> int:
    agg = StockByLocation.objects.filter(product_id=product_id).aggregate(
        s=Sum("current_stock")
    )
    return int(agg["s"] or 0)


def _next_invoice_number() -> str:
    """BR-13 — Numeración ICM-0001 atómica (singleton id=1)."""
    row, _ = InvoiceCounter.objects.select_for_update().get_or_create(
        pk=1, defaults={"last_number": 0}
    )
    row.last_number = int(row.last_number) + 1
    row.save(update_fields=["last_number"])
    return f"ICM-{row.last_number:04d}"


def generate_invoice_number() -> str:
    """
    BR-13 — Numeración secuencial de factura.

    Debe invocarse dentro de la misma transacción `atomic` que el despacho que persiste el movimiento.
    """
    return _next_invoice_number()


def generate_invoice_pdf(
    movement: Movement,
    *,
    invoice_number: str | None = None,
    product: Product | None = None,
    quantity: int | None = None,
    movement_type: str | None = None,
) -> ContentFile | None:
    """
    BR-13 — Genera PDF del comprobante; si falla solo registra log (no invalida el movimiento).

    Args:
        movement: Movimiento asociado (usa sus FKs si faltan argumentos).
    """
    inv = invoice_number or movement.invoice_number or "BORRADOR"
    prod = product or movement.product
    qty = quantity if quantity is not None else movement.quantity
    mtype = movement_type or movement.movement_type
    return _try_build_invoice_pdf(
        invoice_number=inv, product=prod, quantity=qty, movement_type=mtype
    )


def _try_build_invoice_pdf(
    *,
    invoice_number: str,
    product: Product,
    quantity: int,
    movement_type: str,
) -> ContentFile | None:
    """BR-13 — Genera PDF y lo retorna como ContentFile."""
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


def check_and_create_alerts(product: Product, location: Location | None = None) -> None:
    """
    RF-011 — Verifica umbrales y vencimientos; no debe bloquear la operación principal.

    Args:
        product: Producto afectado.
        location: Si se indica, evalúa además alerta de stock mínimo por ubicación.
    """
    try:
        if location is not None:
            alert_services.check_and_create_minimum_stock_alert(product, location)
        alert_services.sync_stock_alerts_for_product(product.id)
        alert_services.sync_expiry_alerts_for_product(product.id)
    except Exception:
        logger.exception("check_and_create_alerts falló para product_id=%s", product.id)


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

    Raises:
        SerialNumberRequiredError: BR-04.
        DiscrepancyNoteRequiredError: BR-09.
    """
    product = (
        Product.objects.select_for_update()
        .select_related("category")
        .get(pk=product_id)
    )
    if product.category.requires_serial_number and not (serial_number or "").strip():
        raise SerialNumberRequiredError()
    if (
        qty_invoiced is not None
        and qty_invoiced != quantity
        and not (discrepancy_note or "").strip()
    ):
        raise DiscrepancyNoteRequiredError()

    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de cadena de frío."
        )
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de seguridad eléctrica."
        )

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
    loc = Location.objects.get(pk=location_id)
    check_and_create_alerts(product, loc)
    return movement


@transaction.atomic
def register_dispatch(
    user,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    movement_type: str,
    *,
    scanned_code: str | None = None,
    order_sku: str | None = None,
    serial_number: str | None = None,
    customer_data: dict[str, Any] | None = None,
    note: str | None = None,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
    privacy_notice_acknowledged: bool = False,
) -> Movement:
    """
    RF-006, BR-04, BR-08, BR-11, BR-13 — Salida con validación cruzada opcional y factura.

    BR-08: si `scanned_code` y `order_sku` se envían, se valida contra `resolve_identifier`.
    Si ninguno se envía, despacho manual sin validación cruzada.

    Raises:
        CrossValidationFailedError: Validación cruzada o datos de venta mayor incompletos.
        PrivacyConsentRequiredError: Ley 1581 sin consentimiento.
        InsufficientStockError: BR-11.
        SerialNumberRequiredError: BR-04.
    """
    if movement_type not in {
        MovementType.SALIDA_VENTA_MAYOR,
        MovementType.SALIDA_VENTA_MENOR,
        MovementType.SALIDA_DANO,
        MovementType.SALIDA_VENCIMIENTO,
    }:
        raise ValueError("Tipo de salida inválido.")

    sc = (scanned_code or "").strip()
    osku = (order_sku or "").strip()
    if bool(sc) ^ bool(osku):
        raise CrossValidationFailedError(
            "Para validación cruzada envíe ambos `scanned_code` y `order_sku`, o ninguno para despacho manual.",
            detail={"scanned_code": sc, "order_sku": osku},
        )

    if sc and osku:
        try:
            scanned_product = resolve_identifier(sc)
        except Product.DoesNotExist as e:
            raise CrossValidationFailedError(
                "No se pudo resolver el código escaneado.",
                detail={"scanned_code": sc},
            ) from e
        if scanned_product.id != product_id:
            raise CrossValidationFailedError(
                detail={"scanned": sc, "expected_product_id": str(product_id)},
            )
        product = Product.objects.select_related("category").get(pk=product_id)
        if product.sku != osku:
            raise CrossValidationFailedError(
                detail={"resolved_sku": product.sku, "order_sku": osku}
            )
    else:
        product = Product.objects.select_related("category").get(pk=product_id)

    if product.category.requires_serial_number and not (serial_number or "").strip():
        raise SerialNumberRequiredError()

    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de cadena de frío."
        )
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de seguridad eléctrica."
        )

    extra_audit: dict[str, Any] = {}
    if movement_type == MovementType.SALIDA_VENTA_MAYOR:
        cd = customer_data or {}
        required = (
            "customer_name",
            "customer_email",
            "customer_phone",
            "customer_address",
        )
        missing = [k for k in required if not (str(cd.get(k) or "")).strip()]
        if missing:
            raise CrossValidationFailedError(
                "La venta mayor requiere datos completos del cliente.",
                detail={"missing": missing},
            )
        ack = bool(cd.get("privacy_notice_acknowledged")) or bool(
            privacy_notice_acknowledged
        )
        if not ack:
            raise PrivacyConsentRequiredError()
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

    invoice_number = generate_invoice_number()
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
        scanned_code=sc or None,
        order_sku=osku or None,
        serial_number=serial_number,
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
    loc = Location.objects.get(pk=location_id)
    check_and_create_alerts(product, loc)
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
    """
    RF-007, BR-11 — Traslado interno entre ubicaciones.

    Raises:
        InsufficientStockError: Stock insuficiente en origen.
        StockMismatchError: Si el total consolidado cambia tras el traslado (bug / inconsistencia).
    """
    if origin_id == destination_id:
        raise ValueError("Origen y destino deben ser distintos.")

    product = Product.objects.select_related("category").get(pk=product_id)
    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de cadena de frío."
        )
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de seguridad eléctrica."
        )

    total_before = _consolidated_stock_total(product_id=product_id)

    first_id, second_id = sorted([origin_id, destination_id], key=lambda u: str(u))
    row_first = _lock_stock(product_id, first_id)
    row_second = _lock_stock(product_id, second_id)
    origin = row_first if row_first.location_id == origin_id else row_second
    dest = row_second if row_first.location_id == origin_id else row_first

    if origin.current_stock < quantity:
        raise InsufficientStockError(
            detail={
                "location_id": str(origin_id),
                "available": origin.current_stock,
                "requested": quantity,
            }
        )

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

    total_after = _consolidated_stock_total(product_id=product_id)
    if total_before != total_after:
        raise StockMismatchError(
            detail={"before": total_before, "after": total_after},
        )

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
    location_id: UUID,
    quantity: int,
    *,
    serial_number: str | None = None,
    related_movement_id: UUID | None = None,
) -> Movement:
    """
    RF-008 — Devolución que incrementa stock en ubicación (BR-04, BR-05, BR-11).

    Raises:
        ReturnNotAllowedError: BR-05.
        SerialNumberRequiredError: BR-04.
    """
    product = (
        Product.objects.select_for_update()
        .select_related("category")
        .get(pk=product_id)
    )
    if not _product_allows_returns(product):
        raise ProductNotReturnableError()
    if product.category.requires_serial_number and not (serial_number or "").strip():
        raise SerialNumberRequiredError()

    related: Movement | None = None
    if related_movement_id:
        related = (
            Movement.objects.select_for_update().filter(pk=related_movement_id).first()
        )
        if related is None:
            raise ValueError("related_movement_id no existe.")

    dest = _lock_stock(product_id, location_id)
    before = dest.current_stock
    after = before + quantity
    dest.current_stock = after
    dest.last_movement_at = timezone.now()
    dest.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    movement = Movement.objects.create(
        movement_type=MovementType.DEVOLUCION,
        product_id=product_id,
        destination_location_id=location_id,
        quantity=quantity,
        stock_previo_destino=before,
        stock_resultante_destino=after,
        serial_number=serial_number,
        related_movement=related,
        executed_by=user,
    )
    log_event(
        AuditEventType.RETURN_CREATED,
        description="Devolución registrada",
        user=user,
        movement=movement,
        detail={"type": MovementType.DEVOLUCION},
    )
    loc = Location.objects.get(pk=location_id)
    check_and_create_alerts(product, loc)
    return movement


@transaction.atomic
def register_adjustment(
    almacenista_user,
    product_id: UUID,
    location_id: UUID,
    new_quantity: int,
    justification: str,
) -> Movement:
    """
    RF-009, BR-07 — Ajuste formal con delta explícito.

    Raises:
        UnauthorizedDomainActionError: Solo almacenista.
        AdjustmentJustificationRequiredError: Justificación vacía.
    """
    if getattr(almacenista_user, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede registrar ajustes de inventario."
        )
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
        detail={"delta": delta, "justification": justification.strip()},
    )
    product = Product.objects.get(pk=product_id)
    check_and_create_alerts(product)
    return movement


@transaction.atomic
def correct_movement_within_window(
    user, movement_id: UUID, corrected_data: dict[str, Any]
) -> list[Movement]:
    """
    BR-06 — Autocorrección de traslado dentro de 5 minutos desde `created_at` (PROMPT FASE LÓGICA).

    Implementación: traslado inverso + traslado corregido; sin mutar el movimiento original (BR-10).

    Raises:
        UnauthorizedDomainActionError: Usuario distinto al autor.
        ImmutableRecordError: Ventana de 5 minutos cerrada.
    """
    original = Movement.objects.select_related("product").get(pk=movement_id)
    if original.movement_type != MovementType.TRASLADO:
        raise ValueError("Solo se soporta corrección de traslados en esta versión.")
    if original.executed_by_id != user.id:
        raise UnauthorizedDomainActionError(
            "Solo el autor del movimiento puede corregirlo."
        )
    if timezone.now() - original.created_at > timedelta(minutes=5):
        raise ImmutableRecordError(
            "La ventana de autocorrección (5 minutos) ya cerró para este movimiento."
        )

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
    Suma algebraica inferida desde el ledger para verificación de consistencia (BR-11).

    Convención: entradas suman en destino; salidas restan en origen; traslados afectan ambos;
    devoluciones con destino suman; ajustes según origen/destino.
    """
    total = 0
    qs = Movement.objects.filter(product_id=product_id).order_by("created_at")
    for m in qs.iterator():
        if (
            m.movement_type == MovementType.ENTRADA
            and m.destination_location_id == location_id
        ):
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
        elif (
            m.movement_type == MovementType.DEVOLUCION
            and m.destination_location_id == location_id
        ):
            total += m.quantity
    return total
