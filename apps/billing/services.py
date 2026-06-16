"""
Servicios de facturación comercial multi-producto.

RF-006, BR-13 — Crea facturas con múltiples items en una sola transacción atómica,
gestiona anulaciones con reversión de stock, y expone métricas de ventas.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.billing.models import CompanyInfo
from apps.movements.models import Invoice, Movement, MovementType
from apps.movements.services import (
    create_invoice_from_movements,
    dispatch_combo,
    generate_invoice_number,
    register_dispatch,
)
from shared.exceptions import DomainValidationError, InvoiceAlreadyVoidedError

logger = logging.getLogger(__name__)

_INVOICE_TYPE_TO_MOVEMENT: dict[str, str] = {
    "retail": MovementType.SALIDA_VENTA_MENOR,
    "wholesale": MovementType.SALIDA_VENTA_MAYOR,
}


def get_company_info() -> CompanyInfo:
    """Retorna el singleton CompanyInfo (crea defaults si no existe)."""
    info, _ = CompanyInfo.objects.get_or_create(pk=1)
    return info


def update_company_info(user: Any, data: dict[str, Any]) -> CompanyInfo:
    """
    Actualiza los datos fiscales de la empresa.

    RF-Admin — Solo administrador vía IsAdministrador.
    """
    info = get_company_info()
    allowed_fields = {
        "company_name",
        "nit",
        "address",
        "phone",
        "email",
        "dian_resolution",
        "dian_range_from",
        "dian_range_to",
        "invoice_series",
        "invoice_footer",
    }
    for field, value in data.items():
        if field in allowed_fields:
            setattr(info, field, value)
    info.save()

    log_event(
        AuditEventType.COMPANY_INFO_UPDATED,
        description="Datos de empresa actualizados",
        user=user,
        detail={"updated_fields": list(data.keys())},
    )
    return info


@transaction.atomic
def create_multi_dispatch_invoice(
    user: Any,
    *,
    invoice_type: str,
    location_id: UUID,
    customer_data: dict[str, Any],
    items: list[dict[str, Any]],
    note: str | None = None,
    privacy_notice_acknowledged: bool = False,
    cold_chain_acknowledged: bool = False,
    electrical_safety_acknowledged: bool = False,
) -> Invoice:
    """
    RF-006, RF-003, BR-13 — Crea una factura multi-ítem en una única transacción atómica.

    Reutiliza register_dispatch() para productos individuales y dispatch_combo()
    para combos, ambos con un número de factura compartido, evitando duplicar la
    lógica de stock, FIFO, seriales y validación cruzada. Un mismo carrito puede
    mezclar productos individuales y combos libremente.

    Args:
        invoice_type: "retail" | "wholesale"
        location_id: UUID de la ubicación origen del stock.
        customer_data: Datos del cliente (name, id_number, email, phone, address).
        items: Lista de items, cada uno con `quantity` y exactamente uno de
            `product_id` (producto individual) o `combo_id` (combo). Los
            productos individuales aceptan además `discount_pct` opcional.
        note: Nota libre asociada a la factura.
        privacy_notice_acknowledged: Requerido para wholesale (Ley 1581).
        cold_chain_acknowledged: Requerido si algún producto exige cadena de frío.
        electrical_safety_acknowledged: Requerido si algún producto es de una
            categoría que exige serial (Electroterapia).

    Raises:
        DomainValidationError: Si invoice_type no es válido o items está vacío.
        CrossValidationFailedError: Si wholesale y faltan datos del cliente.
        PrivacyConsentRequiredError: Si wholesale y no hay consentimiento.
        AlertAcknowledgementRequiredError: Si falta reconocer cadena de frío o
            seguridad eléctrica para algún producto que lo exija.
        InsufficientStockError: Si no hay stock suficiente para algún ítem.
        ProductCombo.DoesNotExist: Si algún `combo_id` no existe o está inactivo.
    """
    movement_type = _INVOICE_TYPE_TO_MOVEMENT.get(invoice_type)
    if movement_type is None:
        raise DomainValidationError(
            f"invoice_type inválido: '{invoice_type}'. Use 'retail' o 'wholesale'."
        )
    if not items:
        raise DomainValidationError("La factura debe contener al menos un ítem.")

    # Normalizar customer_data para compatibilidad con register_dispatch
    cd = {
        "customer_name": customer_data.get("name", ""),
        "customer_email": customer_data.get("email", ""),
        "customer_phone": customer_data.get("phone", ""),
        "customer_address": customer_data.get("address", ""),
        "privacy_notice_acknowledged": privacy_notice_acknowledged,
    }

    # Generar número de factura ÚNICO para todos los ítems (productos y combos)
    invoice_number = generate_invoice_number()

    all_movements: list[Movement] = []
    for item in items:
        quantity: int = item["quantity"]
        combo_id: UUID | None = item.get("combo_id")

        if combo_id:
            # Un combo es una unidad indivisible (Opción B: plantilla virtual);
            # `quantity` combos completos se despachan en llamadas independientes
            # que comparten el mismo invoice_number.
            for _ in range(quantity):
                combo_movements = dispatch_combo(
                    user,
                    combo_id,
                    location_id,
                    external_invoice_number=invoice_number,
                    skip_invoice_creation=True,
                )
                all_movements.extend(combo_movements)
            continue

        product_id: UUID = item["product_id"]
        discount_pct = item.get("discount_pct") or item.get("discount")

        movements = register_dispatch(
            user,
            product_id,
            location_id,
            quantity,
            movement_type,
            customer_data=cd
            if movement_type == MovementType.SALIDA_VENTA_MAYOR
            else None,
            note=note,
            privacy_notice_acknowledged=privacy_notice_acknowledged,
            cold_chain_acknowledged=cold_chain_acknowledged,
            electrical_safety_acknowledged=electrical_safety_acknowledged,
            discount_pct=discount_pct,
            external_invoice_number=invoice_number,
            skip_invoice_creation=True,
        )
        all_movements.extend(movements)

    # Crear UN único Invoice agrupando todos los movements
    invoice = create_invoice_from_movements(
        all_movements,
        user=user,
        invoice_number=invoice_number,
        customer_data=cd,
    )

    # Enriquecer campos de billing en el Invoice
    invoice.invoice_type = invoice_type
    invoice.customer_id_number = customer_data.get("id_number", "")
    invoice.save(update_fields=["invoice_type", "customer_id_number"])

    return invoice


@transaction.atomic
def void_invoice(invoice_id: int, *, user: Any, reason: str) -> Invoice:
    """
    Anula una factura y revierte el stock de todos sus movimientos de salida.

    BR-10 — Los movements son inmutables: se crean movements ANULACION compensatorios
    que revierten el stock en la misma ubicación, sin modificar los originales.

    Revierte: SALIDA_VENTA_MENOR, SALIDA_VENTA_MAYOR, SALIDA_COMBO.

    Args:
        invoice_id: PK del Invoice a anular.
        user: Usuario almacenista que anula.
        reason: Motivo de anulación (mínimo 5 caracteres).

    Raises:
        InvoiceAlreadyVoidedError: Si la factura ya fue anulada (409).
        DomainValidationError: Si el motivo está vacío (422).
        Http404: Si la factura no existe.
    """
    from django.shortcuts import get_object_or_404

    from apps.inventory.models import StockByLocation

    invoice = get_object_or_404(
        Invoice.objects.select_for_update().prefetch_related(
            "movements__product__category"
        ),
        pk=invoice_id,
    )

    if invoice.is_voided:
        raise InvoiceAlreadyVoidedError(
            detail={
                "invoice_number": invoice.number,
                "voided_at": str(invoice.voided_at),
            },
        )
    if not reason.strip():
        raise DomainValidationError("El motivo de anulación es obligatorio.")

    # Incluye SALIDA_COMBO para cubrir también facturas generadas vía dispatch_combo
    sale_types = {
        MovementType.SALIDA_VENTA_MENOR,
        MovementType.SALIDA_VENTA_MAYOR,
        MovementType.SALIDA_COMBO,
    }
    voiding_movements: list[Movement] = []

    for m in invoice.movements.all():
        if m.movement_type not in sale_types:
            continue

        location_id = m.origin_location_id
        if location_id is None:
            continue

        stock_row, _ = StockByLocation.objects.select_for_update().get_or_create(
            product_id=m.product_id,
            location_id=location_id,
            defaults={"current_stock": 0},
        )
        before = stock_row.current_stock
        after = before + m.quantity
        stock_row.current_stock = after
        stock_row.last_movement_at = timezone.now()
        stock_row.save(
            update_fields=["current_stock", "last_movement_at", "updated_at"]
        )

        reversal = Movement.objects.create(
            movement_type=MovementType.ANULACION,
            product_id=m.product_id,
            lot=m.lot,
            destination_location_id=location_id,
            quantity=m.quantity,
            stock_previo_destino=before,
            stock_resultante_destino=after,
            invoice_number=invoice.number,
            executed_by=user,
            related_movement=m,
            justification=f"Anulación factura {invoice.number}: {reason}",
        )
        voiding_movements.append(reversal)
        invoice.movements.add(reversal)

    invoice.is_voided = True
    invoice.void_reason = reason
    invoice.voided_at = timezone.now()
    invoice.voided_by = user
    invoice.save(update_fields=["is_voided", "void_reason", "voided_at", "voided_by"])

    log_event(
        AuditEventType.INVOICE_VOIDED,
        description=f"Factura {invoice.number} anulada",
        user=user,
        detail={
            "invoice_id": invoice.pk,
            "invoice_number": invoice.number,
            "reason": reason,
            "reversal_movement_ids": [str(m.id) for m in voiding_movements],
            "_entity_type": "Invoice",
            "_entity_id": str(invoice.pk),
            "_origin": "API",
        },
    )
    return invoice


def get_invoice_stats() -> dict[str, Any]:
    """
    Retorna métricas de ventas para hoy y el mes en curso.

    Solo considera facturas no anuladas y de tipo SALIDA_VENTA_*.
    """
    from django.db.models import Count, Sum
    from django.utils.timezone import localtime

    now = localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    base_qs = Invoice.objects.filter(is_voided=False)

    today_qs = base_qs.filter(issued_at__gte=today_start)
    month_qs = base_qs.filter(issued_at__gte=month_start)

    today_agg = today_qs.aggregate(
        total=Sum("total_amount"),
        count=Count("id"),
    )
    month_agg = month_qs.aggregate(
        total=Sum("total_amount"),
        count=Count("id"),
    )

    return {
        "total_sales_today": today_agg["total"] or Decimal("0"),
        "total_sales_month": month_agg["total"] or Decimal("0"),
        "invoice_count_today": today_agg["count"] or 0,
        "invoice_count_month": month_agg["count"] or 0,
    }
