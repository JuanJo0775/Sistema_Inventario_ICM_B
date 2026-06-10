"""Excepciones de dominio del módulo de compras."""

from __future__ import annotations

from rest_framework import status

from shared.exceptions import (
    DomainValidationError,
    ICMBaseException,
    ImmutableRecordError,
)


class SupplierNITDuplicateError(DomainValidationError):
    default_message = "Ya existe un proveedor registrado con este NIT."
    default_code = "SUPPLIER_NIT_DUPLICATE"


class SupplierInactiveError(DomainValidationError):
    default_message = (
        "El proveedor está inactivo y no puede asociarse a nuevas órdenes de compra."
    )
    default_code = "SUPPLIER_INACTIVE"


class PurchaseOrderImmutableError(ImmutableRecordError):
    default_message = "La orden de compra no puede modificarse en su estado actual."
    default_code = "PURCHASE_ORDER_IMMUTABLE"


class InvalidPOStatusTransitionError(DomainValidationError):
    default_message = (
        "La transición de estado solicitada no está permitida para esta orden de compra."
    )
    default_code = "INVALID_PO_STATUS_TRANSITION"


class POCancellationReasonRequiredError(DomainValidationError):
    default_message = "Debe indicar el motivo de cancelación de la orden de compra."
    default_code = "PO_CANCELLATION_REASON_REQUIRED"


class POHasConfirmedReceptionsError(DomainValidationError):
    default_message = (
        "No se puede cancelar la OC porque tiene recepciones confirmadas que ya generaron stock."
    )
    default_code = "PO_HAS_CONFIRMED_RECEPTIONS"


class POItemQuantityExceededError(DomainValidationError):
    default_message = (
        "La cantidad a recibir supera la cantidad pendiente del ítem de la OC."
    )
    default_code = "PO_ITEM_QUANTITY_EXCEEDED"


class ReceptionImmutableError(ImmutableRecordError):
    default_message = "La recepción confirmada es inmutable y no puede modificarse."
    default_code = "RECEPTION_IMMUTABLE"


class ReceptionNotInBorradorError(DomainValidationError):
    default_message = (
        "Solo se pueden confirmar o cancelar recepciones en estado borrador."
    )
    default_code = "RECEPTION_NOT_IN_BORRADOR"


class ReceptionDiscrepancyNoteRequiredError(DomainValidationError):
    default_message = (
        "Debe registrar una nota de discrepancia cuando la cantidad recibida difiere "
        "de la esperada."
    )
    default_code = "RECEPTION_DISCREPANCY_NOTE_REQUIRED"


class ReceptionEmptyError(DomainValidationError):
    default_message = (
        "La recepción no tiene ítems con cantidad mayor a cero para confirmar."
    )
    default_code = "RECEPTION_EMPTY"


class ReceptionAllocationQuantityMismatchError(DomainValidationError):
    default_message = (
        "La suma de las distribuciones de recepción debe coincidir con la cantidad recibida."
    )
    default_code = "RECEPTION_ALLOCATION_QUANTITY_MISMATCH"


class PONotReceivableError(DomainValidationError):
    default_message = (
        "La orden de compra no está en un estado que permita recepciones (debe estar "
        "PENDIENTE o PARCIALMENTE_RECIBIDA)."
    )
    default_code = "PO_NOT_RECEIVABLE"
