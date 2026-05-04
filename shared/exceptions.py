"""Excepciones de dominio y manejador centralizado de errores API (RNF-002, RNF-003)."""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class ICMBaseException(Exception):
    """Raíz de errores de negocio ICM."""

    default_message = "Error del sistema ICM"
    default_code = "icm_error"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None, *, detail: dict | None = None) -> None:
        self.message = message or self.default_message
        self.detail_payload = detail or {}
        super().__init__(self.message)


class OutsideOperatingHoursError(ICMBaseException):
    """BR-03: Auxiliar intenta operar fuera de su franja horaria."""

    default_message = "Acceso no permitido fuera del horario operativo del auxiliar de despacho."
    default_code = "outside_operating_hours"
    status_code = status.HTTP_403_FORBIDDEN


class InsufficientStockError(ICMBaseException):
    """Stock insuficiente para ejecutar el movimiento."""

    default_message = "Stock insuficiente para la operación solicitada."
    default_code = "insufficient_stock"


class ProductNotReturnableError(ICMBaseException):
    """BR-05: Producto no admite devoluciones."""

    default_message = "Este producto no admite devoluciones según la política de ICM."
    default_code = "product_not_returnable"


class SerialNumberRequiredError(ICMBaseException):
    """BR-04: Producto de Electroterapia sin número de serie."""

    default_message = "El número de serie es obligatorio para este producto."
    default_code = "serial_number_required"


class CrossValidationFailedError(ICMBaseException):
    """BR-08: El código escaneado no coincide con el SKU de la orden."""

    default_message = "El identificador escaneado no coincide con el SKU de la orden."
    default_code = "cross_validation_failed"


class AlertAcknowledgementRequiredError(ICMBaseException):
    """RF-011 — Falta reconocimiento de alerta operativa obligatoria."""

    default_message = "Debe reconocer las alertas operativas antes de confirmar el movimiento."
    default_code = "alert_acknowledgement_required"


class DiscrepancyNoteRequiredError(ICMBaseException):
    """BR-09: Diferencia en cantidades sin nota de discrepancia."""

    default_message = "Debe registrar una nota de discrepancia cuando la cantidad recibida difiere de la facturada."
    default_code = "discrepancy_note_required"


class AdjustmentJustificationRequiredError(ICMBaseException):
    """BR-07: Ajuste sin justificación obligatoria."""

    default_message = "La justificación es obligatoria para registrar un ajuste."
    default_code = "adjustment_justification_required"


class ImmutableRecordError(ICMBaseException):
    """BR-10: Intento de modificar un registro inmutable."""

    default_message = "El registro es inmutable y no puede modificarse ni eliminarse."
    default_code = "immutable_record"
    status_code = status.HTTP_409_CONFLICT


class CorrectionWindowClosedError(ICMBaseException):
    """BR-06: Intento de corrección fuera de la ventana activa."""

    default_message = "La ventana de autocorrección para este movimiento ya no está activa."
    default_code = "correction_window_closed"


class UnauthorizedCredentialManagementError(ICMBaseException):
    """BR-02: Usuario no almacenista intenta gestionar credenciales."""

    default_message = "Solo el almacenista puede gestionar credenciales de usuario."
    default_code = "unauthorized_credential_management"
    status_code = status.HTTP_403_FORBIDDEN


def custom_exception_handler(exc: BaseException, context: dict[str, Any]) -> Response | None:
    """
    Transforma excepciones de dominio ICM en respuestas HTTP uniformes.

    RF-012 / RNF-002: no exponer trazas internas al cliente.
    """
    if isinstance(exc, ICMBaseException):
        body = {
            "error": exc.default_code,
            "message": exc.message,
            "detail": exc.detail_payload,
        }
        if exc.status_code >= 500:
            logger.exception("Error de negocio ICM con código 5xx inesperado: %s", exc)
        return Response(body, status=exc.status_code)

    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, Http404):
        return Response(
            {"error": "not_found", "message": "Recurso no encontrado.", "detail": {}},
            status=status.HTTP_404_NOT_FOUND,
        )
    if isinstance(exc, DjangoPermissionDenied):
        return Response(
            {"error": "permission_denied", "message": str(exc) or "No autorizado.", "detail": {}},
            status=status.HTTP_403_FORBIDDEN,
        )

    logger.exception("Error no manejado en API")
    return Response(
        {
            "error": "server_error",
            "message": "Ha ocurrido un error interno. Intente más tarde.",
            "detail": {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
