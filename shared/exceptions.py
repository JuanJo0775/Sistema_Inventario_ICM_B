"""Jerarquía de excepciones de dominio ICM (README_ARQUITECTURA §7.5, RNF-002)."""

from __future__ import annotations

from rest_framework import status


class ICMBaseException(Exception):
    """Raíz de errores de negocio ICM."""

    default_message = "Error del sistema ICM"
    default_code = "ICM_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(
        self, message: str | None = None, *, detail: dict | None = None
    ) -> None:
        self.message = message or self.default_message
        self.detail_payload = detail or {}
        super().__init__(self.message)


class AuthenticationError(ICMBaseException):
    """Errores de autenticación fallida (401)."""

    default_message = "No autenticado o token inválido."
    default_code = "AUTHENTICATION_ERROR"
    status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationError(ICMBaseException):
    """Errores de autorización de contexto (403)."""

    default_message = "No autorizado."
    default_code = "AUTHORIZATION_ERROR"
    status_code = status.HTTP_403_FORBIDDEN


class OutsideOperatingHoursError(AuthorizationError):
    """BR-03: Auxiliar intenta operar o autenticarse fuera de su franja horaria."""

    default_message = (
        "Acceso no permitido fuera del horario operativo del auxiliar de despacho."
    )
    default_code = "OUTSIDE_OPERATING_HOURS"


class UnauthorizedCredentialManagementError(AuthorizationError):
    """BR-02: Usuario no almacenista intenta gestionar credenciales."""

    default_message = "Solo el almacenista puede gestionar credenciales de usuario."
    default_code = "UNAUTHORIZED_CREDENTIAL_MANAGEMENT"


class UnauthorizedDomainActionError(AuthorizationError):
    """Acción de dominio no permitida para el rol del usuario (p. ej. BR-07 fuera de almacenista)."""

    default_message = "No tiene permiso para realizar esta acción."
    default_code = "UNAUTHORIZED_DOMAIN_ACTION"


class DomainValidationError(ICMBaseException):
    """Validación de reglas de negocio (formato correcto pero dominio rechaza)."""

    default_message = "Los datos no cumplen las reglas de negocio."
    default_code = "DOMAIN_VALIDATION_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class SerialNumberRequiredError(DomainValidationError):
    """BR-04: Producto de Electroterapia sin número de serie."""

    default_message = "El número de serie es obligatorio para este producto."
    default_code = "SERIAL_NUMBER_REQUIRED"


class DiscrepancyNoteRequiredError(DomainValidationError):
    """BR-09: Diferencia en cantidades sin nota de discrepancia."""

    default_message = "Debe registrar una nota de discrepancia cuando la cantidad recibida difiere de la facturada."
    default_code = "DISCREPANCY_NOTE_REQUIRED"


class AdjustmentJustificationRequiredError(DomainValidationError):
    """BR-07: Ajuste sin justificación obligatoria."""

    default_message = "La justificación es obligatoria para registrar un ajuste."
    default_code = "ADJUSTMENT_JUSTIFICATION_REQUIRED"


class CrossValidationFailedError(DomainValidationError):
    """BR-08: El código escaneado no coincide con el SKU de la orden."""

    default_message = "El identificador escaneado no coincide con el SKU de la orden."
    default_code = "CROSS_VALIDATION_FAILED"


class ReturnNotAllowedError(DomainValidationError):
    """BR-05: Producto no admite devoluciones."""

    default_message = "Este producto no admite devoluciones según la política de ICM."
    default_code = "RETURN_NOT_ALLOWED"


class ProductNotReturnableError(ReturnNotAllowedError):
    """Alias retrocompatible (BR-05)."""

    default_code = "PRODUCT_NOT_RETURNABLE"


class InvalidSKUFormatError(DomainValidationError):
    """BR-12: Formato de SKU inválido según la nueva política (usuario definido)."""

    default_message = "Formato SKU inválido. Debe ser 1-4 letras, guion, 1-4 dígitos."
    default_code = "INVALID_SKU_FORMAT"


class PrivacyConsentRequiredError(DomainValidationError):
    """Ley 1581 / RNF-006: Falta reconocimiento del aviso de privacidad para datos personales."""

    default_message = (
        "Debe confirmar el aviso de privacidad antes de registrar datos del cliente."
    )
    default_code = "PRIVACY_CONSENT_REQUIRED"


class AlertAcknowledgementRequiredError(DomainValidationError):
    """RF-011 — Falta reconocimiento de alerta operativa obligatoria."""

    default_message = (
        "Debe reconocer las alertas operativas antes de confirmar el movimiento."
    )
    default_code = "ALERT_ACKNOWLEDGEMENT_REQUIRED"


class LotCodeRequiredError(DomainValidationError):
    """RF-011 / lote: falta código de lote en un producto que lo requiere."""

    default_message = "El producto requiere código de lote."
    default_code = "LOT_CODE_REQUIRED"


class LotExpirationDateRequiredError(DomainValidationError):
    """RF-011 / lote: falta fecha de vencimiento para un producto que lo requiere."""

    default_message = "El producto requiere fecha de vencimiento por lote."
    default_code = "LOT_EXPIRATION_DATE_REQUIRED"


class LotMismatchError(DomainValidationError):
    """RF-011 / lote: la fecha ingresada no coincide con el lote existente."""

    default_message = "La fecha de vencimiento no coincide con un lote existente."
    default_code = "LOT_MISMATCH"


class InventoryError(ICMBaseException):
    """Errores de inventario y consistencia de stock."""

    default_message = "Error de inventario."
    default_code = "INVENTORY_ERROR"
    status_code = status.HTTP_409_CONFLICT


class InsufficientStockError(InventoryError):
    """BR-11: Stock insuficiente para ejecutar el movimiento."""

    default_message = "Stock insuficiente para la operación solicitada."
    default_code = "INSUFFICIENT_STOCK"


class StockMismatchError(InventoryError):
    """BR-11: Discrepancia entre ledger reconstruido y stock derivado."""

    default_message = (
        "El stock derivado no coincide con la reconstrucción desde el ledger."
    )
    default_code = "STOCK_MISMATCH"


class LocationStateNotAllowedError(DomainValidationError):
    """BR-14: Ubicación en estado operativo no elegible para el movimiento solicitado."""

    default_message = (
        "La ubicación no está habilitada por su estado operativo para esta operación."
    )
    default_code = "LOCATION_STATE_NOT_ALLOWED"


class ResourceNotFoundError(ICMBaseException):
    """Recurso solicitado no encontrado (404)."""

    default_message = "El recurso solicitado no existe."
    default_code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ImmutableRecordError(ICMBaseException):
    """BR-10: Intento de modificar un registro inmutable o ventana de corrección cerrada."""

    default_message = "El registro es inmutable y no puede modificarse ni eliminarse."
    default_code = "IMMUTABLE_RECORD"
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED


class CorrectionWindowClosedError(ImmutableRecordError):
    """BR-06: Intento de corrección fuera de la ventana permitida (mensaje específico)."""

    default_message = (
        "La ventana de autocorrección para este movimiento ya no está activa."
    )
    default_code = "CORRECTION_WINDOW_CLOSED"
    status_code = status.HTTP_409_CONFLICT


class InvoiceAlreadyVoidedError(ICMBaseException):
    """Intento de anular una factura que ya fue anulada (409 Conflict)."""

    default_message = "La factura ya fue anulada y no puede anularse de nuevo."
    default_code = "INVOICE_ALREADY_VOIDED"
    status_code = status.HTTP_409_CONFLICT
