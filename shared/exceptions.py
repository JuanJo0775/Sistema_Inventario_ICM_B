"""Jerarquía de excepciones de dominio ICM (README_ARQUITECTURA §7.5, RNF-002)."""

from __future__ import annotations

from rest_framework import status


class ICMBaseException(Exception):
    """Raíz de errores de negocio ICM."""

    default_message = "Error del sistema ICM"
    default_code = "icm_error"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None, *, detail: dict | None = None) -> None:
        self.message = message or self.default_message
        self.detail_payload = detail or {}
        super().__init__(self.message)


class AuthenticationError(ICMBaseException):
    """Errores de autenticación / autorización de contexto (403)."""

    default_message = "No autorizado."
    default_code = "authentication_error"
    status_code = status.HTTP_403_FORBIDDEN


class OutsideOperatingHoursError(AuthenticationError):
    """BR-03: Auxiliar intenta operar o autenticarse fuera de su franja horaria."""

    default_message = "Acceso no permitido fuera del horario operativo del auxiliar de despacho."
    default_code = "outside_operating_hours"


class UnauthorizedCredentialManagementError(AuthenticationError):
    """BR-02: Usuario no almacenista intenta gestionar credenciales."""

    default_message = "Solo el almacenista puede gestionar credenciales de usuario."
    default_code = "unauthorized_credential_management"


class UnauthorizedDomainActionError(AuthenticationError):
    """Acción de dominio no permitida para el rol del usuario (p. ej. BR-07 fuera de almacenista)."""

    default_message = "No tiene permiso para realizar esta acción."
    default_code = "unauthorized_domain_action"


class DomainValidationError(ICMBaseException):
    """Validación de reglas de negocio (formato correcto pero dominio rechaza)."""

    default_message = "Los datos no cumplen las reglas de negocio."
    default_code = "domain_validation_error"


class SerialNumberRequiredError(DomainValidationError):
    """BR-04: Producto de Electroterapia sin número de serie."""

    default_message = "El número de serie es obligatorio para este producto."
    default_code = "serial_number_required"


class DiscrepancyNoteRequiredError(DomainValidationError):
    """BR-09: Diferencia en cantidades sin nota de discrepancia."""

    default_message = (
        "Debe registrar una nota de discrepancia cuando la cantidad recibida difiere de la facturada."
    )
    default_code = "discrepancy_note_required"


class AdjustmentJustificationRequiredError(DomainValidationError):
    """BR-07: Ajuste sin justificación obligatoria."""

    default_message = "La justificación es obligatoria para registrar un ajuste."
    default_code = "adjustment_justification_required"


class CrossValidationFailedError(DomainValidationError):
    """BR-08: El código escaneado no coincide con el SKU de la orden."""

    default_message = "El identificador escaneado no coincide con el SKU de la orden."
    default_code = "cross_validation_failed"


class ReturnNotAllowedError(DomainValidationError):
    """BR-05: Producto no admite devoluciones."""

    default_message = "Este producto no admite devoluciones según la política de ICM."
    default_code = "return_not_allowed"


class ProductNotReturnableError(ReturnNotAllowedError):
    """Alias retrocompatible (BR-05)."""

    default_code = "product_not_returnable"


class InvalidSKUFormatError(DomainValidationError):
    """BR-12: SKU inválido para marca Can (prefijo CAN-)."""

    default_message = "El SKU debe usar el prefijo CAN- para productos de marca Can."
    default_code = "invalid_sku_format"


class PrivacyConsentRequiredError(DomainValidationError):
    """Ley 1581 / RNF-006: Falta reconocimiento del aviso de privacidad para datos personales."""

    default_message = "Debe confirmar el aviso de privacidad antes de registrar datos del cliente."
    default_code = "privacy_consent_required"


class AlertAcknowledgementRequiredError(DomainValidationError):
    """RF-011 — Falta reconocimiento de alerta operativa obligatoria."""

    default_message = "Debe reconocer las alertas operativas antes de confirmar el movimiento."
    default_code = "alert_acknowledgement_required"


class InventoryError(ICMBaseException):
    """Errores de inventario y consistencia de stock."""

    default_message = "Error de inventario."
    default_code = "inventory_error"


class InsufficientStockError(InventoryError):
    """BR-11: Stock insuficiente para ejecutar el movimiento."""

    default_message = "Stock insuficiente para la operación solicitada."
    default_code = "insufficient_stock"


class StockMismatchError(InventoryError):
    """BR-11: Discrepancia entre ledger reconstruido y stock derivado."""

    default_message = "El stock derivado no coincide con la reconstrucción desde el ledger."
    default_code = "stock_mismatch"


class ImmutableRecordError(ICMBaseException):
    """BR-10: Intento de modificar un registro inmutable o ventana de corrección cerrada."""

    default_message = "El registro es inmutable y no puede modificarse ni eliminarse."
    default_code = "immutable_record"
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED


class CorrectionWindowClosedError(ImmutableRecordError):
    """BR-06: Intento de corrección fuera de la ventana permitida (mensaje específico)."""

    default_message = "La ventana de autocorrección para este movimiento ya no está activa."
    default_code = "correction_window_closed"
