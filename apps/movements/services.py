"""Servicios del ledger de movimientos (RF-005–RF-009, BR-04–BR-11, BR-13, BR-14)."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Case, F, IntegerField, Q, Sum, When
from django.utils import timezone

from apps.alerts import services as alert_services
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.catalog.models import Lot, Product, ProductSerial
from apps.catalog.services import resolve_identifier
from apps.inventory.models import Location, StockByLocation
from apps.movements.models import Invoice, InvoiceCounter, Movement, MovementType
from shared.exceptions import (
    AdjustmentJustificationRequiredError,
    AlertAcknowledgementRequiredError,
    CrossValidationFailedError,
    DiscrepancyNoteRequiredError,
    DomainValidationError,
    ImmutableRecordError,
    InsufficientStockError,
    LotCodeRequiredError,
    LotExpirationDateRequiredError,
    LotMismatchError,
    LotSelectionRequiredError,
    PrivacyConsentRequiredError,
    ProductNotReturnableError,
    SerialNumberRequiredError,
    StockMismatchError,
    UnauthorizedDomainActionError,
)
from shared.location_validators import (
    validate_location_for_destination as _ensure_location_allows_destination,
)
from shared.location_validators import (
    validate_location_for_origin as _ensure_location_allows_origin,
)
from shared.utils.db import get_for_update_or_404

logger = logging.getLogger(__name__)


def _validate_serial_required(product: Product, serial_number: str | None) -> None:
    """BR-04: Valida serial obligatorio si la categoría lo exige."""
    if product.category.requires_serial_number and not (serial_number or "").strip():
        raise SerialNumberRequiredError()


def _normalize_serial(serial_number: str | None) -> str | None:
    """Normaliza serial: limpia espacios externos; retorna None si vacío."""
    if serial_number:
        normalized = serial_number.strip()
        return normalized if normalized else None
    return None


def _resolve_serial_for_dispatch(
    product: Product,
    location_id: UUID,
    serial_id: UUID | None = None,
) -> str | None:
    """
    Resuelve el serial_number para un movimiento de salida/traslado.

    - Si `serial_id` se provee: valida que el ProductSerial exista, esté disponible
      y en la ubicación correcta.
    - Si no se provee y la categoría requiere serial: auto-asigna uno disponible.
    - Si la categoría no requiere serial: retorna None.

    Returns:
        El serial_number en string, o None si no aplica.
    """
    from apps.catalog.models import ProductSerial

    if not product.category.requires_serial_number:
        return None

    if serial_id is not None:
        try:
            ps = ProductSerial.objects.select_for_update().get(
                pk=serial_id,
                product=product,
                status=ProductSerial.Status.AVAILABLE,
                current_location_id=location_id,
            )
        except ProductSerial.DoesNotExist:
            raise DomainValidationError(
                f"Serial {serial_id} no disponible para producto {product.sku} "
                f"en ubicación {location_id}."
            )
        return ps.serial_number

    # Auto-asignar: tomar el primer serial disponible (FIFO por created_at)
    ps_auto: ProductSerial | None = (
        ProductSerial.objects.select_for_update()
        .filter(
            product=product,
            status=ProductSerial.Status.AVAILABLE,
            current_location_id=location_id,
        )
        .order_by("created_at")
        .first()
    )
    if ps_auto is None:
        raise InsufficientStockError(
            detail={
                "product_id": str(product.id),
                "location_id": str(location_id),
                "message": "No hay seriales disponibles para este producto en la ubicación.",
            }
        )
    return ps_auto.serial_number


def _update_serial_status(
    serial_number: str,
    product: Product,
    new_status: str,
    location_id: UUID | None = None,
    movement: Movement | None = None,
) -> ProductSerial | None:
    """
    Actualiza el estado y ubicación de un ProductSerial.

    Retorna la instancia actualizada o None si no se encontró.
    """
    from apps.catalog.models import ProductSerial

    try:
        ps = ProductSerial.objects.select_for_update().get(
            product=product, serial_number=serial_number
        )
        ps.status = new_status
        if location_id is not None:
            ps.current_location_id = location_id
        if movement is not None:
            ps.last_movement = movement
        ps.save(
            update_fields=["status", "current_location", "last_movement", "updated_at"]
        )
        return ps
    except ProductSerial.DoesNotExist:
        return None


def available_serials_at_location(
    *, product_id: UUID, location_id: UUID
) -> list[ProductSerial]:
    """Retorna los seriales disponibles (status=available) de un producto en una ubicación."""
    return list(
        ProductSerial.objects.filter(
            product_id=product_id,
            status=ProductSerial.Status.AVAILABLE,
            current_location_id=location_id,
        ).order_by("created_at")
    )


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


@transaction.atomic
def generate_invoice_number() -> str:
    """
    BR-13 — Numeración secuencial de factura.
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
    """BR-13 — Genera PDF básico (sin precio) como ContentFile."""
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


def _build_invoice_pdf_rich(invoice: Invoice) -> ContentFile | None:
    """Genera PDF enriquecido con datos de precio para un Invoice. Falla silenciosamente."""
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover
        logger.warning("WeasyPrint no disponible: %s", exc)
        return None

    movements = list(invoice.movements.select_related("product").all())
    now = timezone.now().strftime("%Y-%m-%d %H:%M UTC")

    rows_html = ""
    for m in movements:
        unit_price = f"{m.unit_price:,.4f}" if m.unit_price is not None else "—"
        subtotal = f"{m.subtotal:,.4f}" if m.subtotal is not None else "—"
        discount = f"{m.discount_amount:,.4f}" if m.discount_amount else "—"
        rows_html += (
            f"<tr>"
            f"<td>{m.product.sku}</td>"
            f"<td>{m.product.name}</td>"
            f"<td>{m.quantity}</td>"
            f"<td>{unit_price}</td>"
            f"<td>{discount}</td>"
            f"<td>{subtotal}</td>"
            f"</tr>"
        )

    customer_html = ""
    if invoice.customer_name:
        customer_html = (
            f"<p><strong>Cliente:</strong> {invoice.customer_name}</p>"
            f"<p><strong>Email:</strong> {invoice.customer_email}</p>"
            f"<p><strong>Teléfono:</strong> {invoice.customer_phone}</p>"
            f"<p><strong>Dirección:</strong> {invoice.customer_address}</p>"
        )

    html = f"""
    <html><head><meta charset="utf-8"/><style>
      body {{ font-family: Arial, sans-serif; font-size: 12px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
      th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; }}
      th {{ background: #f5f5f5; }}
      .totals {{ text-align: right; margin-top: 12px; }}
    </style></head><body>
      <h1>ICM — Comprobante de Despacho</h1>
      <p><strong>Número:</strong> {invoice.number}</p>
      <p><strong>Fecha:</strong> {now}</p>
      {customer_html}
      <table>
        <tr><th>SKU</th><th>Producto</th><th>Cantidad</th>
            <th>Precio Unit.</th><th>Descuento</th><th>Subtotal</th></tr>
        {rows_html}
      </table>
      <div class="totals">
        <p>Subtotal: {invoice.currency} {invoice.subtotal:,.4f}</p>
        <p>Descuento: {invoice.currency} {invoice.discount_total:,.4f}</p>
        <p>IVA: {invoice.currency} {invoice.tax_total:,.4f}</p>
        <p><strong>TOTAL: {invoice.currency} {invoice.total_amount:,.4f}</strong></p>
      </div>
    </body></html>
    """
    pdf_bytes = HTML(string=html).write_pdf()
    return ContentFile(pdf_bytes, name=f"{invoice.number}.pdf")


def create_invoice_from_movements(
    movements: list[Movement],
    *,
    user: Any,
    invoice_number: str,
    customer_data: dict[str, Any] | None = None,
) -> Invoice:
    """
    Crea o actualiza el modelo Invoice que agrupa los movements del despacho.

    Calcula los totales consolidando los campos de precio de cada Movement.
    Los movements sin precio (históricos) contribuyen con 0 al total.
    """
    from decimal import Decimal

    subtotal = sum((m.subtotal or Decimal("0")) for m in movements)
    discount_total = sum((m.discount_amount or Decimal("0")) for m in movements)
    tax_total = sum((m.tax_amount or Decimal("0")) for m in movements)
    total_amount = sum((m.total_amount or Decimal("0")) for m in movements)
    currency = next((m.currency for m in movements if m.currency), "COP")

    cd = customer_data or {}
    invoice, _ = Invoice.objects.select_for_update().get_or_create(
        number=invoice_number,
        defaults={
            "customer_name": cd.get("customer_name", ""),
            "customer_email": cd.get("customer_email", ""),
            "customer_phone": cd.get("customer_phone", ""),
            "customer_address": cd.get("customer_address", ""),
            "subtotal": subtotal,
            "discount_total": discount_total,
            "tax_total": tax_total,
            "total_amount": total_amount,
            "currency": currency,
            "issued_by": user,
        },
    )
    for m in movements:
        invoice.movements.add(m)

    # Generar PDF enriquecido si aún no existe
    if not invoice.pdf:
        pdf = _build_invoice_pdf_rich(invoice)
        if pdf:
            invoice.pdf.save(f"{invoice_number}.pdf", pdf, save=True)

    log_event(
        AuditEventType.INVOICE_GENERATED,
        description=f"Factura {invoice_number} generada",
        user=user,
        detail={
            "invoice_number": invoice_number,
            "movement_ids": [str(m.id) for m in movements],
            "total_amount": str(invoice.total_amount),
            "_entity_type": "Invoice",
            "_entity_id": str(invoice.id),
            "_origin": "API",
        },
    )
    return invoice


def _resolve_price_snapshot(
    product: Product,
    quantity: int,
    movement_type: str,
    *,
    discount_pct: Any | None = None,
) -> dict:
    """
    Calcula el snapshot de precio para un Movement de salida.

    Retorna un dict con todos los campos financieros listos para pasar a Movement.objects.create().
    Si el producto no tiene precio configurado, retorna campos None (sin error).

    price_type:
        - "retail"    → SALIDA_VENTA_MENOR
        - "wholesale" → SALIDA_VENTA_MAYOR
        - "cost"      → SALIDA_DANO / SALIDA_VENCIMIENTO (se usa unit_cost como referencia)
    """
    from decimal import ROUND_HALF_UP, Decimal

    type_map: dict[str, tuple[str | None, Any]] = {
        MovementType.SALIDA_VENTA_MENOR: ("retail", product.sale_price_retail),
        MovementType.SALIDA_VENTA_MAYOR: ("wholesale", product.sale_price_wholesale),
        MovementType.SALIDA_DANO: ("cost", product.unit_cost),
        MovementType.SALIDA_VENCIMIENTO: ("cost", product.unit_cost),
    }
    _default: tuple[str | None, Any] = (None, None)
    price_type, raw_price = type_map.get(movement_type, _default)

    if raw_price is None:
        logger.info(
            "Producto %s sin precio configurado para movement_type=%s; snapshot será null.",
            product.sku,
            movement_type,
        )
        return {
            "unit_price": None,
            "unit_cost": product.unit_cost,
            "discount_pct": None,
            "discount_amount": None,
            "subtotal": None,
            "tax_rate_pct": None,
            "tax_amount": None,
            "total_amount": None,
            "currency": product.currency or "COP",
            "price_type": price_type,
        }

    qty = Decimal(str(quantity))
    unit_price = Decimal(str(raw_price))
    subtotal = (unit_price * qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    disc_pct = Decimal(str(discount_pct)) if discount_pct is not None else Decimal("0")
    disc_amount = (subtotal * disc_pct / Decimal("100")).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )

    tax_base = subtotal - disc_amount
    tax_rate = (
        Decimal(str(product.tax_rate_pct))
        if product.tax_rate_pct is not None
        else Decimal("0")
    )
    tax_amount = (tax_base * tax_rate / Decimal("100")).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    total_amount = (tax_base + tax_amount).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )

    return {
        "unit_price": unit_price,
        "unit_cost": product.unit_cost,
        "discount_pct": disc_pct if disc_pct else None,
        "discount_amount": disc_amount if disc_amount else None,
        "subtotal": subtotal,
        "tax_rate_pct": product.tax_rate_pct,
        "tax_amount": tax_amount if tax_amount else None,
        "total_amount": total_amount,
        "currency": product.currency or "COP",
        "price_type": price_type,
    }


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
            alert_services.sync_cold_chain_alerts(product, location)
        alert_services.sync_stock_alerts_for_product(product.id)
        alert_services.sync_stock_zero_alerts(product.id)
        alert_services.sync_expiry_alerts_for_product(product.id)
        alert_services.sync_lot_expired_alerts(product.id)
    except Exception:
        logger.exception("check_and_create_alerts falló para product_id=%s", product.id)


def _product_allows_returns(product: Product) -> bool:
    """BR-05 — Solo categorías marcadas como retornables."""
    return bool(product.category.is_returnable)


def _requires_ack_flags(product: Product) -> tuple[bool, bool]:
    cold = product.requires_cold_chain
    electric = bool(product.category.requires_serial_number)
    return cold, electric


def _log_alert_acknowledgement(
    *,
    user: Any,
    movement: Movement,
    cold_chain_acknowledged: bool,
    electrical_safety_acknowledged: bool,
) -> None:
    acknowledged: list[str] = []
    if cold_chain_acknowledged:
        acknowledged.append("cold_chain")
    if electrical_safety_acknowledged:
        acknowledged.append("electrical_safety")
    if not acknowledged:
        return
    log_event(
        AuditEventType.ALERT_ACKNOWLEDGED,
        description="Reconocimiento de alertas operativas",
        user=user,
        movement=movement,
        detail={"acknowledged": acknowledged, "movement_type": movement.movement_type},
    )


@transaction.atomic
def register_entry(
    user: Any,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    *,
    lot_code: str | None = None,
    lot_expiration_date: date | None = None,
    serial_number: str | None = None,
    qty_invoiced: int | None = None,
    discrepancy_note: str | None = None,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
    unit_cost: Any | None = None,
) -> Movement:
    """
    RF-005 — Entrada de mercancía.

    Valida BR-04 (serial en categorías que lo exigen) y BR-09 (nota si hay discrepancia).

    Raises:
        SerialNumberRequiredError: BR-04.
        DiscrepancyNoteRequiredError: BR-09.
    """
    product = get_for_update_or_404(
        Product.objects.select_related("category"), pk=product_id
    )
    location = get_for_update_or_404(Location.objects, pk=location_id)
    _ensure_location_allows_destination(location, "entry")
    _validate_serial_required(product, serial_number)
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

    lot = None
    if product.requires_expiration:
        if not (lot_code or "").strip():
            raise LotCodeRequiredError()
        if lot_expiration_date is None:
            raise LotExpirationDateRequiredError()
        lot, created = Lot.objects.select_for_update().get_or_create(
            product=product,
            code=(lot_code or "").strip(),
            defaults={"expiration_date": lot_expiration_date},
        )
        if not created and lot.expiration_date != lot_expiration_date:
            raise LotMismatchError()

    dest = _lock_stock(product_id, location_id)
    before = dest.current_stock
    after = before + quantity
    dest.current_stock = after
    dest.last_movement_at = timezone.now()
    dest.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    normalized_serial = _normalize_serial(serial_number)
    movement = Movement.objects.create(
        movement_type=MovementType.ENTRADA,
        product_id=product_id,
        lot=lot,
        destination_location_id=location_id,
        quantity=quantity,
        stock_previo_destino=before,
        stock_resultante_destino=after,
        serial_number=normalized_serial,
        quantity_invoiced=qty_invoiced,
        discrepancy_note=discrepancy_note,
        executed_by=user,
        unit_cost=unit_cost,
    )

    # Crear ProductSerial × quantity con batch prefix + sufijo auto-incremental
    # Formato: <serial_base>-<batch_prefix>-<NNN> (ej: SN-CEL-001-a7-001)
    # batch_prefix = primeros 2 hex chars del UUID del movimiento (agrupa seriales de la misma entrada)
    if normalized_serial:
        batch_prefix = movement.pk.hex[:2]
        serials = [
            ProductSerial(
                product=product,
                serial_number=f"{normalized_serial}-{batch_prefix}-{i:03d}",
                status=ProductSerial.Status.AVAILABLE,
                current_location_id=location_id,
                last_movement=movement,
            )
            for i in range(1, quantity + 1)
        ]
        ProductSerial.objects.bulk_create(serials, ignore_conflicts=True)

    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Entrada de mercancía",
        user=user,
        movement=movement,
        detail={"type": MovementType.ENTRADA},
    )
    _log_alert_acknowledgement(
        user=user,
        movement=movement,
        cold_chain_acknowledged=cold_chain_acknowledged,
        electrical_safety_acknowledged=electrical_safety_acknowledged,
    )
    check_and_create_alerts(product, location)
    return movement


@transaction.atomic
def register_dispatch(
    user: Any,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    movement_type: str,
    *,
    lot_id: UUID | None = None,
    scanned_code: str | None = None,
    order_sku: str | None = None,
    serial_id: UUID | None = None,
    customer_data: dict[str, Any] | None = None,
    note: str | None = None,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
    privacy_notice_acknowledged: bool = False,
    discount_pct: Any | None = None,
    external_invoice_number: str | None = None,
    skip_invoice_creation: bool = False,
) -> list[Movement]:
    """
    RF-006, BR-04, BR-08, BR-11, BR-13, BR-14 — Salida con validación cruzada opcional y factura.

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
        raise DomainValidationError("Tipo de salida inválido.")

    sc = (scanned_code or "").strip()
    osku = (order_sku or "").strip()
    location = get_for_update_or_404(Location.objects, pk=location_id)
    _ensure_location_allows_origin(location, "dispatch")
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
        product = get_for_update_or_404(
            Product.objects.select_related("category"), pk=product_id
        )
        if product.sku != osku:
            raise CrossValidationFailedError(
                detail={"resolved_sku": product.sku, "order_sku": osku}
            )
    else:
        product = get_for_update_or_404(
            Product.objects.select_related("category"), pk=product_id
        )

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
    customer_snapshot: dict[str, Any] | None = None
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
        customer_snapshot = cd
    if note:
        extra_audit["note"] = note

    # Resolver serial desde ProductSerial (BR-04)
    resolved_serial = _resolve_serial_for_dispatch(product, location_id, serial_id)

    # Calcular snapshot de precio al momento del despacho (R-05)
    price_snapshot = _resolve_price_snapshot(
        product, quantity, movement_type, discount_pct=discount_pct
    )

    selected_lot: Lot | None = None
    if getattr(product, "requires_expiration", False) and lot_id is not None:
        selected_lot = get_for_update_or_404(
            Lot.objects.filter(product_id=product_id), pk=lot_id
        )
        assert selected_lot is not None
        available = ledger_net_quantity_for_lot_location(
            product_id=product_id, lot_id=selected_lot.id, location_id=location_id
        )
        if available < quantity:
            raise InsufficientStockError(
                detail={
                    "product_id": str(product_id),
                    "lot_id": str(selected_lot.id),
                    "location_id": str(location_id),
                    "available": available,
                    "requested": quantity,
                }
            )

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

    # Prepare invoice and PDF once for the whole dispatch
    invoice_number = (
        external_invoice_number
        if external_invoice_number
        else generate_invoice_number()
    )
    # Skip per-movement PDF in bulk mode (caller generates enriched Invoice PDF at the end)
    pdf_file = (
        None
        if skip_invoice_creation
        else _try_build_invoice_pdf(
            invoice_number=invoice_number,
            product=product,
            quantity=quantity,
            movement_type=movement_type,
        )
    )

    movements_created: list[Movement] = []

    if product.requires_expiration and selected_lot is None:
        # Evaluar lotes disponibles para preferir lote único cuando alcance.
        # No se rechaza aquí por falta de lotes trackeados: el stock total
        # ya fue validado contra StockByLocation.current_stock (línea ~775).
        # Hay productos con requires_expiration cuyo stock llegó por
        # TRASLADO/AJUSTE sin lot_id asociado (lot_id es opcional incluso
        # si el producto trackea vencimiento), y available_lots_at_location()
        # solo contempla movimientos con lot_id asignado, lo que antes
        # producía un falso INSUFFICIENT_STOCK con available=0.
        candidates = available_lots_at_location(
            product_id=product_id, location_id=location_id
        )
        single_candidate = next(
            (c for c in candidates if c["available"] >= quantity), None
        )
        if single_candidate is not None:
            selected_lot = single_candidate["lot"]

    if product.requires_expiration and selected_lot is None:
        # Multi-lot consumption: take from earliest-expiring lots
        remaining = int(quantity)
        candidates = available_lots_at_location(
            product_id=product_id, location_id=location_id
        )
        for candidate in candidates:
            if remaining <= 0:
                break
            lot = candidate["lot"]
            take = min(candidate["available"], remaining)
            prev = origin.current_stock
            after = prev - take
            origin.current_stock = after
            origin.last_movement_at = timezone.now()
            origin.save(
                update_fields=["current_stock", "last_movement_at", "updated_at"]
            )

            lot_price = _resolve_price_snapshot(
                product, take, movement_type, discount_pct=discount_pct
            )
            movement = Movement.objects.create(
                movement_type=movement_type,
                product_id=product_id,
                lot=lot,
                origin_location_id=location_id,
                quantity=take,
                stock_previo_origen=prev,
                stock_resultante_origen=after,
                scanned_code=sc or None,
                order_sku=osku or None,
                serial_number=resolved_serial,
                invoice_number=invoice_number,
                invoice_pdf=pdf_file,
                executed_by=user,
                customer_snapshot=customer_snapshot,
                **lot_price,
            )
            movements_created.append(movement)
            _log_alert_acknowledgement(
                user=user,
                movement=movement,
                cold_chain_acknowledged=cold_chain_acknowledged,
                electrical_safety_acknowledged=electrical_safety_acknowledged,
            )
            remaining -= take

        if remaining > 0:
            # Remanente sin lote trackeado: origin.current_stock ya validado
            # arriba (línea ~775) cubre la diferencia, así que se despacha
            # sin asociar lote en vez de rechazar la operación asumiendo
            # stock=0 para el faltante (ver comentario en el bloque anterior).
            prev = origin.current_stock
            after = prev - remaining
            origin.current_stock = after
            origin.last_movement_at = timezone.now()
            origin.save(
                update_fields=["current_stock", "last_movement_at", "updated_at"]
            )

            untracked_price = _resolve_price_snapshot(
                product, remaining, movement_type, discount_pct=discount_pct
            )
            movement = Movement.objects.create(
                movement_type=movement_type,
                product_id=product_id,
                lot=None,
                origin_location_id=location_id,
                quantity=remaining,
                stock_previo_origen=prev,
                stock_resultante_origen=after,
                scanned_code=sc or None,
                order_sku=osku or None,
                serial_number=resolved_serial,
                invoice_number=invoice_number,
                invoice_pdf=pdf_file,
                executed_by=user,
                customer_snapshot=customer_snapshot,
                **untracked_price,
            )
            movements_created.append(movement)
            _log_alert_acknowledgement(
                user=user,
                movement=movement,
                cold_chain_acknowledged=cold_chain_acknowledged,
                electrical_safety_acknowledged=electrical_safety_acknowledged,
            )
            remaining = 0

    else:
        # Single movement (either non-expiring product or selected_lot provided)
        before = origin.current_stock
        after = before - quantity
        origin.current_stock = after
        origin.last_movement_at = timezone.now()
        origin.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

        movement = Movement.objects.create(
            movement_type=movement_type,
            product_id=product_id,
            lot=selected_lot,
            origin_location_id=location_id,
            quantity=quantity,
            stock_previo_origen=before,
            stock_resultante_origen=after,
            scanned_code=sc or None,
            order_sku=osku or None,
            serial_number=resolved_serial,
            invoice_number=invoice_number,
            invoice_pdf=pdf_file,
            executed_by=user,
            customer_snapshot=customer_snapshot,
            **price_snapshot,
        )
        movements_created.append(movement)

    check_and_create_alerts(product, location)
    for m in movements_created:
        m.refresh_from_db()

    # Marcar ProductSerial como despachado
    for m in movements_created:
        if m.serial_number and product.category.requires_serial_number:
            _update_serial_status(
                serial_number=m.serial_number,
                product=product,
                new_status=ProductSerial.Status.DISPATCHED,
                movement=m,
            )

    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Despacho registrado",
        user=user,
        detail={
            "movements": [str(m.id) for m in movements_created],
            "type": movement_type,
        },
    )

    # Crear el modelo Invoice consolidado con precio (BR-13: parte de la transacción atómica)
    if not skip_invoice_creation and invoice_number is not None:
        create_invoice_from_movements(
            movements_created,
            user=user,
            invoice_number=invoice_number,
            customer_data=customer_snapshot,
        )

    # Emitir webhook dispatch.completed (falla silenciosamente — no bloquea el despacho)
    try:
        from apps.webhooks.services import queue_webhook_event

        first_m = movements_created[0] if movements_created else None
        if first_m:
            queue_webhook_event(
                "dispatch.completed",
                {
                    "invoice_number": invoice_number,
                    "movement_ids": [str(m.id) for m in movements_created],
                    "product_sku": product.sku,
                    "quantity": quantity,
                    "movement_type": movement_type,
                    "unit_price": (
                        str(first_m.unit_price)
                        if first_m.unit_price is not None
                        else None
                    ),
                    "total_amount": (
                        str(first_m.total_amount)
                        if first_m.total_amount is not None
                        else None
                    ),
                    "currency": first_m.currency,
                    # RNF-006: no incluir PII del cliente en payloads de webhooks externos
                },
            )
    except Exception:
        logger.exception(
            "queue_webhook_event dispatch.completed falló para invoice=%s; despacho ya registrado.",
            invoice_number,
        )

    if all(m.unit_price is not None for m in movements_created):
        log_event(
            AuditEventType.DISPATCH_WITH_PRICE_COMPLETED,
            description=f"Despacho con precio completado — factura {invoice_number}",
            user=user,
            detail={
                "invoice_number": invoice_number,
                "movement_ids": [str(m.id) for m in movements_created],
                "movement_type": movement_type,
                "_entity_type": "Dispatch",
                "_entity_id": invoice_number,
                "_origin": "API",
            },
        )

    return movements_created


@transaction.atomic
def register_internal_transfer(
    user: Any,
    product_id: UUID,
    origin_id: UUID,
    destination_id: UUID,
    quantity: int,
    *,
    lot_id: UUID | None = None,
    serial_id: UUID | None = None,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
    related_movement: Movement | None = None,
) -> Movement:
    """
    RF-007, BR-04, BR-11, BR-14 — Traslado interno entre ubicaciones.

    BR-04 (lote): si el producto tiene `requires_expiration=True`, `lot_id` es
    obligatorio. Sin esta validación, el traslado podía dejar stock en la
    ubicación destino sin lote asociado en el ledger (movimiento con
    `lot_id=NULL`), rompiendo la trazabilidad de vencimiento aunque
    `StockByLocation` siguiera contando el stock correctamente.

    Raises:
        InsufficientStockError: Stock insuficiente en origen.
        SerialNumberRequiredError: BR-04.
        LotSelectionRequiredError: Falta `lot_id` para producto con vencimiento.
        StockMismatchError: Si el total consolidado cambia tras el traslado (bug / inconsistencia).
    """
    if origin_id == destination_id:
        raise DomainValidationError("Origen y destino deben ser distintos.")

    product = Product.objects.select_related("category").get(pk=product_id)
    resolved_serial = _resolve_serial_for_dispatch(product, origin_id, serial_id)
    locations = {
        loc.id: loc
        for loc in Location.objects.select_for_update().filter(
            pk__in=[origin_id, destination_id]
        )
    }
    origin_location = locations.get(origin_id)
    destination_location = locations.get(destination_id)
    if origin_location is None or destination_location is None:
        raise DomainValidationError("Ubicación de origen o destino no existe.")
    _ensure_location_allows_origin(origin_location, "internal_transfer")
    _ensure_location_allows_destination(destination_location, "internal_transfer")
    cold, electric = _requires_ack_flags(product)
    if cold and not cold_chain_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de cadena de frío."
        )
    if electric and not electrical_safety_acknowledged:
        raise AlertAcknowledgementRequiredError(
            "Debe reconocer la alerta de seguridad eléctrica."
        )

    selected_lot: Lot | None = None
    if getattr(product, "requires_expiration", False):
        if lot_id is None:
            raise LotSelectionRequiredError(
                detail={"product_id": str(product_id)}
            )
        selected_lot = get_for_update_or_404(
            Lot.objects.filter(product_id=product_id), pk=lot_id
        )
        assert selected_lot is not None
        available = ledger_net_quantity_for_lot_location(
            product_id=product_id, lot_id=selected_lot.id, location_id=origin_id
        )
        if available < quantity:
            raise InsufficientStockError(
                detail={
                    "product_id": str(product_id),
                    "lot_id": str(selected_lot.id),
                    "location_id": str(origin_id),
                    "available": available,
                    "requested": quantity,
                }
            )

    first_id, second_id = sorted([origin_id, destination_id], key=lambda u: str(u))
    row_first = _lock_stock(product_id, first_id)
    row_second = _lock_stock(product_id, second_id)
    # Compute total AFTER acquiring locks to get a consistent snapshot (ALTA-08)
    total_before = _consolidated_stock_total(product_id=product_id)
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
        lot=selected_lot,
        product_id=product_id,
        origin_location_id=origin_id,
        destination_location_id=destination_id,
        quantity=quantity,
        stock_previo_origen=obo,
        stock_resultante_origen=oao,
        stock_previo_destino=dbd,
        stock_resultante_destino=dad,
        serial_number=resolved_serial,
        executed_by=user,
        related_movement=related_movement,
    )

    # Actualizar ubicación del ProductSerial
    if resolved_serial and product.category.requires_serial_number:
        _update_serial_status(
            serial_number=resolved_serial,
            product=product,
            new_status=ProductSerial.Status.AVAILABLE,
            location_id=destination_id,
            movement=movement,
        )

    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description="Traslado interno",
        user=user,
        movement=movement,
        detail={"type": MovementType.TRASLADO},
    )
    _log_alert_acknowledgement(
        user=user,
        movement=movement,
        cold_chain_acknowledged=cold_chain_acknowledged,
        electrical_safety_acknowledged=electrical_safety_acknowledged,
    )
    return movement


@transaction.atomic
def register_return(
    user: Any,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    *,
    lot_id: UUID | None = None,
    serial_id: UUID | None = None,
    related_movement_id: UUID | None = None,
) -> Movement:
    """
    RF-008 — Devolución que incrementa stock en ubicación (BR-04, BR-05, BR-11, BR-14).

    BR-04 (lote): si el producto tiene `requires_expiration=True`, se exige un
    lote para no dejar stock sin trazabilidad de vencimiento en destino. Si no
    se envía `lot_id` explícito pero la devolución referencia un movimiento
    original (`related_movement_id`), se hereda el lote de ese movimiento.

    Raises:
        ReturnNotAllowedError: BR-05.
        SerialNumberRequiredError: BR-04.
        LotSelectionRequiredError: Falta `lot_id` (y no hay movimiento
            relacionado del cual heredarlo) para producto con vencimiento.
    """
    product = get_for_update_or_404(
        Product.objects.select_related("category"), pk=product_id
    )
    location = get_for_update_or_404(Location.objects, pk=location_id)
    _ensure_location_allows_destination(location, "return")
    if not _product_allows_returns(product):
        raise ProductNotReturnableError()

    resolved_serial: str | None = None
    if serial_id is not None:
        try:
            ps = ProductSerial.objects.select_for_update().get(
                pk=serial_id, product=product
            )
            resolved_serial = ps.serial_number
        except ProductSerial.DoesNotExist:
            raise DomainValidationError(
                f"Serial {serial_id} no existe para producto {product.sku}."
            )
    elif product.category.requires_serial_number:
        raise SerialNumberRequiredError()

    related: Movement | None = None
    if related_movement_id:
        related = (
            Movement.objects.select_for_update().filter(pk=related_movement_id).first()
        )
        if related is None:
            raise DomainValidationError("related_movement_id no existe.")

    selected_lot: Lot | None = None
    if getattr(product, "requires_expiration", False):
        effective_lot_id = lot_id if lot_id is not None else (
            related.lot_id if related is not None else None
        )
        if effective_lot_id is None:
            raise LotSelectionRequiredError(detail={"product_id": str(product_id)})
        selected_lot = get_for_update_or_404(
            Lot.objects.filter(product_id=product_id), pk=effective_lot_id
        )

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
        lot=selected_lot,
        quantity=quantity,
        stock_previo_destino=before,
        stock_resultante_destino=after,
        serial_number=resolved_serial,
        related_movement=related,
        executed_by=user,
    )

    # Reactivar o crear ProductSerial
    if resolved_serial:
        _update_serial_status(
            serial_number=resolved_serial,
            product=product,
            new_status=ProductSerial.Status.AVAILABLE,
            location_id=location_id,
            movement=movement,
        )

    log_event(
        AuditEventType.RETURN_CREATED,
        description="Devolución registrada",
        user=user,
        movement=movement,
        detail={"type": MovementType.DEVOLUCION},
    )
    check_and_create_alerts(product, location)
    return movement


@transaction.atomic
def register_adjustment(
    almacenista_user: Any,
    product_id: UUID,
    location_id: UUID,
    new_quantity: int,
    justification: str,
    *,
    serial_id: UUID | None = None,
    lot_id: UUID | None = None,
) -> Movement:
    """
    RF-009, BR-04, BR-07, BR-14 — Ajuste formal con delta explícito.

    BR-04 (lote): para productos con `requires_expiration=True`, un ajuste que
    incrementa stock (delta > 0) representa unidades "aparecidas" que deben
    asignarse a un lote existente, así que `lot_id` es obligatorio en ese caso.
    Un ajuste que reduce stock (delta < 0) acepta `lot_id` opcional: si no se
    envía, se intenta inferir un único lote con stock suficiente (FEFO); si
    ninguno cubre la cantidad completa, el ajuste se registra sin lote (mismo
    comportamiento histórico, no se bloquea una corrección de inventario).

    Raises:
        UnauthorizedDomainActionError: Solo almacenista.
        AdjustmentJustificationRequiredError: Justificación vacía.
        SerialNumberRequiredError: BR-04.
        LotSelectionRequiredError: Incremento de stock sin `lot_id` en
            producto con vencimiento.
    """
    if getattr(almacenista_user, "role", None) != "almacenista":
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede registrar ajustes de inventario."
        )
    if not (justification or "").strip():
        raise AdjustmentJustificationRequiredError()

    row = _lock_stock(product_id, location_id)
    product = Product.objects.select_related("category").get(pk=product_id)
    location = get_for_update_or_404(Location.objects, pk=location_id)

    if int(new_quantity) < 0:
        raise DomainValidationError(
            "La cantidad objetivo del ajuste no puede ser negativa."
        )

    resolved_serial: str | None = None
    if serial_id is not None:
        try:
            ps = ProductSerial.objects.select_for_update().get(
                pk=serial_id, product=product
            )
            resolved_serial = ps.serial_number
        except ProductSerial.DoesNotExist:
            raise DomainValidationError(
                f"Serial {serial_id} no existe para producto {product.sku}."
            )
    elif product.category.requires_serial_number:
        raise SerialNumberRequiredError()

    before = row.current_stock
    delta = int(new_quantity) - before
    if delta == 0:
        raise DomainValidationError("El ajuste no cambia el stock actual.")
    if delta < 0:
        _ensure_location_allows_origin(location, "adjustment")
    else:
        _ensure_location_allows_destination(location, "adjustment")

    selected_lot: Lot | None = None
    if getattr(product, "requires_expiration", False):
        if delta > 0:
            # Stock "aparecido" en el conteo: debe asignarse a un lote
            # existente, igual que una entrada normal.
            if lot_id is None:
                raise LotSelectionRequiredError(
                    detail={"product_id": str(product_id)}
                )
            selected_lot = get_for_update_or_404(
                Lot.objects.filter(product_id=product_id), pk=lot_id
            )
        elif lot_id is not None:
            selected_lot = get_for_update_or_404(
                Lot.objects.filter(product_id=product_id), pk=lot_id
            )
        else:
            # Reducción sin lote explícito: preferir un único lote con stock
            # suficiente (FEFO) para conservar trazabilidad; si ninguno
            # alcanza, se registra sin lote (no se bloquea la corrección).
            candidates = available_lots_at_location(
                product_id=product_id, location_id=location_id
            )
            single_candidate = next(
                (c for c in candidates if c["available"] >= abs(delta)), None
            )
            if single_candidate is not None:
                selected_lot = single_candidate["lot"]

    row.current_stock = int(new_quantity)
    row.last_movement_at = timezone.now()
    row.save(update_fields=["current_stock", "last_movement_at", "updated_at"])

    origin_id = location_id if delta < 0 else None
    dest_id = location_id if delta > 0 else None
    movement = Movement.objects.create(
        movement_type=MovementType.AJUSTE,
        product_id=product_id,
        lot=selected_lot,
        origin_location_id=origin_id,
        destination_location_id=dest_id,
        quantity=abs(delta),
        stock_previo_origen=before if delta < 0 else None,
        stock_resultante_origen=int(new_quantity) if delta < 0 else None,
        stock_previo_destino=before if delta > 0 else None,
        stock_resultante_destino=int(new_quantity) if delta > 0 else None,
        serial_number=resolved_serial,
        justification=justification.strip(),
        executed_by=almacenista_user,
    )

    # Marcar ProductSerial como ajustado
    if resolved_serial:
        _update_serial_status(
            serial_number=resolved_serial,
            product=product,
            new_status=ProductSerial.Status.ADJUSTED,
            movement=movement,
        )

    log_event(
        AuditEventType.ADJUSTMENT_CREATED,
        description="Ajuste de inventario",
        user=almacenista_user,
        movement=movement,
        detail={"delta": delta, "justification": justification.strip()},
    )
    check_and_create_alerts(product)
    return movement


_CORRECTABLE_TYPES = (
    MovementType.TRASLADO,
    MovementType.ENTRADA,
    MovementType.SALIDA_VENTA_MAYOR,
    MovementType.SALIDA_VENTA_MENOR,
)


def _reverse_entrada_stock(user: Any, original: Movement) -> Movement:
    """Reversa el efecto de stock de una ENTRADA creando una SALIDA_DANO interna."""
    origin = _lock_stock(original.product_id, original.destination_location_id)
    before = origin.current_stock
    after = before - original.quantity
    if after < 0:
        raise InsufficientStockError(
            detail={
                "location_id": str(original.destination_location_id),
                "available": before,
                "requested": original.quantity,
            }
        )
    origin.current_stock = after
    origin.last_movement_at = timezone.now()
    origin.save(update_fields=["current_stock", "last_movement_at", "updated_at"])
    return Movement.objects.create(
        movement_type=MovementType.SALIDA_DANO,
        product_id=original.product_id,
        lot=original.lot,
        origin_location_id=original.destination_location_id,
        quantity=original.quantity,
        stock_previo_origen=before,
        stock_resultante_origen=after,
        executed_by=user,
        related_movement=original,
    )


def _reverse_salida_stock(user: Any, original: Movement) -> Movement:
    """Reversa el efecto de stock de una SALIDA creando una ENTRADA interna."""
    dest = _lock_stock(original.product_id, original.origin_location_id)
    before = dest.current_stock
    after = before + original.quantity
    dest.current_stock = after
    dest.last_movement_at = timezone.now()
    dest.save(update_fields=["current_stock", "last_movement_at", "updated_at"])
    return Movement.objects.create(
        movement_type=MovementType.ENTRADA,
        product_id=original.product_id,
        lot=original.lot,
        destination_location_id=original.origin_location_id,
        quantity=original.quantity,
        stock_previo_destino=before,
        stock_resultante_destino=after,
        executed_by=user,
        related_movement=original,
    )


@transaction.atomic
def correct_movement_within_window(
    user: Any, movement_id: UUID, corrected_data: dict[str, Any]
) -> list[Movement]:
    """
    BR-06 — Autocorrección dentro de 5 minutos para TRASLADO, ENTRADA y SALIDA_VENTA_*.

    Implementación: reversal interno (sin mutar el original, BR-10) + movimiento corregido.

    corrected_data keys:
      - TRASLADO: origin_id, destination_id, quantity
      - ENTRADA:  location_id, quantity  (+ lot_code, serial_number, etc. opcionales)
      - SALIDA:   location_id, quantity, movement_type

    Raises:
        UnauthorizedDomainActionError: Usuario distinto al autor.
        ImmutableRecordError: Ventana de 5 minutos cerrada.
        DomainValidationError: Tipo de movimiento no corregible.
    """
    from shared.exceptions import DomainValidationError

    original = (
        Movement.objects.select_related("product")
        .select_for_update()
        .get(pk=movement_id)
    )

    if original.movement_type not in _CORRECTABLE_TYPES:
        raise DomainValidationError(
            f"Las correcciones dentro de ventana aplican solo para: "
            f"{', '.join(_CORRECTABLE_TYPES)}. Tipo recibido: {original.movement_type}."
        )
    if original.executed_by_id != user.id:
        raise UnauthorizedDomainActionError(
            "Solo el autor del movimiento puede corregirlo."
        )
    if timezone.now() - original.created_at > timedelta(minutes=5):
        raise ImmutableRecordError(
            "La ventana de autocorrección (5 minutos) ya cerró para este movimiento."
        )

    orig_serial = original.serial_number

    def _serial_id_from_corrected(
        corrected_data: dict, orig_serial: str | None
    ) -> UUID | None:
        """Helper: retorna serial_id si se envió, o None para auto-asignar, o el original."""
        if "serial_id" in corrected_data:
            return corrected_data["serial_id"]
        if orig_serial and "serial_id" not in corrected_data:
            return None  # auto-asignar
        return None

    if original.movement_type == MovementType.TRASLADO:
        new_origin = UUID(str(corrected_data["origin_id"]))
        new_dest = UUID(str(corrected_data["destination_id"]))
        new_qty = int(corrected_data["quantity"])
        if new_origin == new_dest:
            raise DomainValidationError("Origen y destino deben ser distintos.")

        rev_serial_id = _serial_id_from_corrected(corrected_data, orig_serial)
        fixed_serial_id = _serial_id_from_corrected(corrected_data, orig_serial)
        # Propagar el lote del TRASLADO original (lot_id ahora es obligatorio
        # en register_internal_transfer para productos con requires_expiration;
        # sin esto, corregir un traslado con lote se rompería con
        # LotSelectionRequiredError). corrected_data permite override explícito.
        fixed_lot_id = corrected_data.get("lot_id", original.lot_id)

        # Los ACKs se propagan del original: el usuario ya los reconoció (BR-06).
        rev = register_internal_transfer(
            user,
            original.product_id,
            UUID(str(original.destination_location_id)),
            UUID(str(original.origin_location_id)),
            int(original.quantity),
            lot_id=original.lot_id,
            serial_id=rev_serial_id,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )
        fixed = register_internal_transfer(
            user,
            original.product_id,
            new_origin,
            new_dest,
            new_qty,
            lot_id=fixed_lot_id,
            serial_id=fixed_serial_id,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
            related_movement=original,
        )

    elif original.movement_type == MovementType.ENTRADA:
        rev = _reverse_entrada_stock(user, original)
        fixed = register_entry(
            user,
            product_id=original.product_id,
            location_id=UUID(str(corrected_data["location_id"])),
            quantity=int(corrected_data["quantity"]),
            lot_code=corrected_data.get("lot_code"),
            lot_expiration_date=corrected_data.get("lot_expiration_date"),
            serial_number=corrected_data.get("serial_number", orig_serial),
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )

    else:
        # SALIDA_VENTA_MAYOR / SALIDA_VENTA_MENOR
        rev = _reverse_salida_stock(user, original)
        fixed_list = register_dispatch(
            user,
            product_id=original.product_id,
            location_id=UUID(str(corrected_data["location_id"])),
            quantity=int(corrected_data["quantity"]),
            movement_type=corrected_data.get("movement_type", original.movement_type),
            serial_id=_serial_id_from_corrected(corrected_data, orig_serial),
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
            privacy_notice_acknowledged=True,
        )
        fixed = fixed_list[0] if isinstance(fixed_list, list) else fixed_list

    log_event(
        AuditEventType.MOVEMENT_CORRECTED,
        description=f"Corrección de {original.movement_type} (BR-06)",
        user=user,
        movement=fixed,
        detail={"original_id": str(original.id), "reversal_movement_id": str(rev.id)},
    )
    return [rev, fixed]


_SALIDA_TYPES = [
    MovementType.SALIDA_VENTA_MAYOR,
    MovementType.SALIDA_VENTA_MENOR,
    MovementType.SALIDA_DANO,
    MovementType.SALIDA_VENCIMIENTO,
    MovementType.SALIDA_COMBO,
]


def _ledger_net_qty(
    *, product_id: UUID, location_id: UUID, lot_id: UUID | None = None
) -> int:
    """
    Calcula el stock neto de un producto en una ubicación mediante SQL agregado (O(1) query).

    Convención: entradas suman en destino; salidas restan en origen; traslados afectan ambos;
    devoluciones con destino suman; ajustes según origen/destino.
    """
    qs = Movement.objects.filter(product_id=product_id)
    if lot_id is not None:
        qs = qs.filter(lot_id=lot_id)

    result = qs.aggregate(
        net=Sum(
            Case(
                When(
                    movement_type=MovementType.ENTRADA,
                    destination_location_id=location_id,
                    then=F("quantity"),
                ),
                When(
                    movement_type__in=_SALIDA_TYPES,
                    origin_location_id=location_id,
                    then=-F("quantity"),
                ),
                # TRASLADO resta en origen
                When(
                    movement_type=MovementType.TRASLADO,
                    origin_location_id=location_id,
                    then=-F("quantity"),
                ),
                # TRASLADO suma en destino
                When(
                    movement_type=MovementType.TRASLADO,
                    destination_location_id=location_id,
                    then=F("quantity"),
                ),
                When(
                    movement_type=MovementType.AJUSTE,
                    destination_location_id=location_id,
                    then=F("quantity"),
                ),
                When(
                    movement_type=MovementType.AJUSTE,
                    origin_location_id=location_id,
                    then=-F("quantity"),
                ),
                When(
                    movement_type=MovementType.DEVOLUCION,
                    destination_location_id=location_id,
                    then=F("quantity"),
                ),
                default=0,
                output_field=IntegerField(),
            )
        )
    )
    return result["net"] or 0


def ledger_net_quantity_for_location(*, product_id: UUID, location_id: UUID) -> int:
    """Suma algebraica inferida desde el ledger para verificación de consistencia (BR-11)."""
    return _ledger_net_qty(product_id=product_id, location_id=location_id)


def ledger_net_quantity_for_lot_location(
    *, product_id: UUID, lot_id: UUID, location_id: UUID
) -> int:
    """Suma algebraica del ledger para un lote específico en una ubicación."""
    return _ledger_net_qty(
        product_id=product_id, location_id=location_id, lot_id=lot_id
    )


def available_lots_at_location(
    *, product_id: UUID, location_id: UUID
) -> list[dict[str, Any]]:
    """Retorna lotes con stock positivo en una ubicación, ordenados por vencimiento.

    Usa SQL agregado (O(1) query) en lugar de iterar el ledger completo.
    """
    rows = (
        Movement.objects.filter(product_id=product_id)
        .filter(
            Q(origin_location_id=location_id) | Q(destination_location_id=location_id)
        )
        .exclude(lot_id=None)
        .values("lot_id")
        .annotate(
            available=Sum(
                Case(
                    When(
                        movement_type=MovementType.ENTRADA,
                        destination_location_id=location_id,
                        then=F("quantity"),
                    ),
                    When(
                        movement_type__in=_SALIDA_TYPES,
                        origin_location_id=location_id,
                        then=-F("quantity"),
                    ),
                    When(
                        movement_type=MovementType.TRASLADO,
                        origin_location_id=location_id,
                        then=-F("quantity"),
                    ),
                    When(
                        movement_type=MovementType.TRASLADO,
                        destination_location_id=location_id,
                        then=F("quantity"),
                    ),
                    When(
                        movement_type=MovementType.AJUSTE,
                        destination_location_id=location_id,
                        then=F("quantity"),
                    ),
                    When(
                        movement_type=MovementType.AJUSTE,
                        origin_location_id=location_id,
                        then=-F("quantity"),
                    ),
                    When(
                        movement_type=MovementType.DEVOLUCION,
                        destination_location_id=location_id,
                        then=F("quantity"),
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        )
        .filter(available__gt=0)
    )

    lot_ids = [r["lot_id"] for r in rows]
    if not lot_ids:
        return []

    lot_map = {
        lot.id: lot
        for lot in Lot.objects.filter(id__in=lot_ids).select_related("product")
    }

    return sorted(
        [
            {"lot": lot_map[r["lot_id"]], "available": r["available"]}
            for r in rows
            if r["lot_id"] in lot_map
        ],
        key=lambda x: (x["lot"].expiration_date, x["lot"].code),
    )


@transaction.atomic
def dispatch_combo(
    user: Any,
    combo_id: UUID,
    location_id: UUID,
    *,
    serial_id: UUID | None = None,
    request: Any = None,
    external_invoice_number: str | None = None,
    skip_invoice_creation: bool = False,
) -> list[Movement]:
    """
    RF-003, BR-04, BR-11, BR-13 — Despacha un combo (Opción B: plantilla virtual).

    Lee la receta del combo y por cada ítem genera un movimiento SALIDA_COMBO
    descontando el stock del producto en la ubicación indicada.

    Args:
        user: Ejecutor (almacenista o auxiliar).
        combo_id: UUID del combo a despachar.
        location_id: UUID de la ubicación desde donde se sacan los productos.
        serial_id: UUID del serial (obligatorio si algún componente lo exige).
        external_invoice_number: Número de factura compartido. Si se provee
            (ver `create_multi_dispatch_invoice`), el combo se agrupa en esa
            factura en vez de generar la suya propia.
        skip_invoice_creation: Si True, no crea/actualiza el Invoice — el
            llamador es responsable de consolidarlo con `create_invoice_from_movements`.

    Returns:
        Lista de Movements creados (uno por ítem del combo).

    Raises:
        InsufficientStockError: Si no hay stock suficiente de algún ítem.
        SerialNumberRequiredError: BR-04 si algún componente requiere serial.
        ProductCombo.DoesNotExist: Si el combo no existe o está inactivo.
    """
    from apps.catalog.models import ProductCombo

    combo = ProductCombo.objects.prefetch_related("combo_items__product__category").get(
        pk=combo_id, deleted_at__isnull=True
    )
    items = list(combo.combo_items.all())
    if not items:
        raise DomainValidationError(f"El combo {combo.sku} no tiene ítems registrados.")

    # Ordenar ítems por product.id para consistencia de locks (previene deadlock).
    items = sorted(items, key=lambda i: str(i.product.id))

    location = get_for_update_or_404(Location.objects, pk=location_id)
    _ensure_location_allows_origin(location, "combo_dispatch")
    movements_created: list[Movement] = []

    # Generar un número de factura para el combo completo (o reutilizar el compartido)
    combo_invoice_number = external_invoice_number or generate_invoice_number()
    # Solo el primer Movement del combo recibirá invoice_number (por restricción UNIQUE).
    # Los demás quedan sin ese campo; el modelo Invoice los agrupa todos vía M2M.
    first_movement = True
    from decimal import Decimal

    # Si precio fijo, distribuir proporcionalmente por costo de cada componente
    use_fixed_price = (
        combo.price_strategy == "fixed" and combo.fixed_price_retail is not None
    )
    fixed_total = (
        Decimal(str(combo.fixed_price_retail or 0)) if use_fixed_price else None
    )

    # Calcular costo total de componentes para distribución proporcional
    if use_fixed_price:
        total_derived = sum(
            (item.product.unit_cost or Decimal("0")) * item.quantity for item in items
        )

    for item in items:
        product = item.product
        qty_needed = item.quantity

        # BR-04: resolver serial por ítem para marcar correctamente como DISPATCHED.
        resolved_serial: str | None = None
        if product.category.requires_serial_number:
            resolved_serial = _resolve_serial_for_dispatch(
                product, location_id, serial_id
            )

        stock_row = _lock_stock(product.id, location_id)
        if stock_row.current_stock < qty_needed:
            raise InsufficientStockError(
                f"Stock insuficiente para '{product.sku}' en '{location.name}'. "
                f"Solicitado: {qty_needed}, Disponible: {stock_row.current_stock}.",
                detail={
                    "product_id": str(product.id),
                    "sku": product.sku,
                    "location_id": str(location_id),
                    "available": stock_row.current_stock,
                    "requested": qty_needed,
                },
            )

        before = stock_row.current_stock
        after = before - qty_needed
        stock_row.current_stock = after
        stock_row.last_movement_at = timezone.now()
        stock_row.save(
            update_fields=["current_stock", "last_movement_at", "updated_at"]
        )

        # Calcular precio del componente
        if use_fixed_price and fixed_total is not None:
            # Distribuir precio fijo proporcionalmente por costo
            from decimal import ROUND_HALF_UP

            item_cost = (product.unit_cost or Decimal("0")) * qty_needed
            if total_derived > 0:
                ratio = item_cost / total_derived
                item_unit_price = (fixed_total * ratio / qty_needed).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
            else:
                item_unit_price = None
            price_snap = {
                "unit_price": item_unit_price,
                "unit_cost": product.unit_cost,
                "subtotal": (
                    (item_unit_price * qty_needed).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )
                    if item_unit_price
                    else None
                ),
                "discount_pct": None,
                "discount_amount": None,
                "tax_rate_pct": product.tax_rate_pct,
                "tax_amount": None,
                "total_amount": (
                    (item_unit_price * qty_needed).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )
                    if item_unit_price
                    else None
                ),
                "currency": product.currency or "COP",
                "price_type": "combo",
            }
        else:
            price_snap = _resolve_price_snapshot(
                product, qty_needed, MovementType.SALIDA_COMBO
            )
            price_snap["price_type"] = "combo"

        movement = Movement.objects.create(
            movement_type=MovementType.SALIDA_COMBO,
            product=product,
            origin_location_id=location_id,
            quantity=qty_needed,
            stock_previo_origen=before,
            stock_resultante_origen=after,
            serial_number=resolved_serial,
            justification=f"Salida por combo: {combo.sku} ({combo.name})",
            executed_by=user,
            # Solo el primer movement lleva invoice_number (restricción UNIQUE del ledger).
            invoice_number=combo_invoice_number if first_movement else None,
            **price_snap,
        )
        first_movement = False
        movements_created.append(movement)
        if resolved_serial:
            _update_serial_status(
                resolved_serial,
                product,
                new_status=ProductSerial.Status.DISPATCHED,
                movement=movement,
            )
        check_and_create_alerts(product, location)

    log_event(
        AuditEventType.MOVEMENT_CREATED,
        description=f"Despacho de combo: {combo.sku}",
        user=user,
        detail={
            "combo_id": str(combo_id),
            "combo_sku": combo.sku,
            "location_id": str(location_id),
            "movements": [str(m.id) for m in movements_created],
        },
    )

    if not skip_invoice_creation:
        create_invoice_from_movements(
            movements_created,
            user=user,
            invoice_number=combo_invoice_number,
        )

    return movements_created
