"""Handler centralizado DRF para excepciones de dominio ICM (README_ARQUITECTURA §7.5)."""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.catalog.models import Product
from shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ICMBaseException,
    ImmutableRecordError,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: BaseException, context: dict[str, Any]
) -> Response | None:
    """
    Convierte excepciones ICM en JSON `{ error, message, detail }`.

    - `AuthenticationError` y subtipos → 403.
    - `ImmutableRecordError` y subtipos → 405.
    - Resto de `ICMBaseException` → `exc.status_code` (típico 400).
    - `Product.DoesNotExist` u `ObjectDoesNotExist` del catálogo → 404 uniforme.
    """
    if isinstance(exc, ICMBaseException):
        code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, AuthenticationError):
            code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, AuthorizationError):
            code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ImmutableRecordError):
            code = status.HTTP_405_METHOD_NOT_ALLOWED
        else:
            code = exc.status_code
        body = {
            "error": exc.default_code,
            "message": exc.message,
            "detail": exc.detail_payload,
        }
        if code >= 500:
            logger.exception("Error de negocio ICM con código 5xx inesperado: %s", exc)
        return Response(body, status=code)

    if isinstance(exc, Product.DoesNotExist):
        return Response(
            {
                "error": "PRODUCT_NOT_FOUND",
                "message": "No se encontró un producto activo para el identificador indicado.",
                "detail": {"detail": str(exc)},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    response = drf_exception_handler(exc, context)

    if response is not None:
        # Uniformar las respuestas generadas por DRF (Validación, Autenticación, etc.)
        status_code = response.status_code
        error_code = "CLIENT_ERROR"
        message = "Error en la solicitud del cliente."

        if status_code == status.HTTP_400_BAD_REQUEST:
            error_code = "VALIDATION_ERROR"
            message = "Error de validación en la solicitud."
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = "NOT_AUTHENTICATED"
            message = "Credenciales de autenticación no provistas o inválidas."
        elif status_code == status.HTTP_403_FORBIDDEN:
            error_code = "PERMISSION_DENIED"
            message = "No tiene permiso para realizar esta acción."
        elif status_code == status.HTTP_404_NOT_FOUND:
            error_code = "NOT_FOUND"
            message = "El recurso solicitado no existe."
        elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            error_code = "METHOD_NOT_ALLOWED"
            message = f"El método HTTP no está permitido."
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_code = "THROTTLED"
            message = "Límite de peticiones excedido."

        detail_data = response.data
        if isinstance(detail_data, dict):
            if "detail" in detail_data and len(detail_data) == 1:
                detail_val = detail_data["detail"]
                if isinstance(detail_val, str):
                    message = detail_val
                    detail_data = {}
            elif (
                "detail" in detail_data
                and "code" in detail_data
                and len(detail_data) == 2
            ):
                # Caso simple jwt: {"detail": "...", "code": "..."}
                error_code = detail_data["code"]
                message = detail_data["detail"]
                detail_data = {}
        elif (
            isinstance(detail_data, list)
            and len(detail_data) == 1
            and isinstance(detail_data[0], str)
        ):
            message = detail_data[0]
            detail_data = {}

        error_code_attr = getattr(exc, "default_code", error_code)

        final_code = error_code_attr if isinstance(error_code_attr, str) else error_code
        # Convert SimpleJWT inner codes to UPPER_SNAKE_CASE
        final_code = str(final_code).upper()

        response.data = {
            "error": final_code,
            "message": message,
            "detail": detail_data,
        }
        return response

    if isinstance(exc, Http404):
        msg = str(exc)
        if not msg or msg == "Http404()":
            msg = "Recurso no encontrado."
        return Response(
            {"error": "NOT_FOUND", "message": msg, "detail": {}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, DjangoPermissionDenied):
        msg = str(exc)
        if not msg or msg == "PermissionDenied()":
            msg = "No autorizado."
        return Response(
            {"error": "PERMISSION_DENIED", "message": msg, "detail": {}},
            status=status.HTTP_403_FORBIDDEN,
        )

    logger.exception("Error no manejado en API")
    return Response(
        {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Ha ocurrido un error interno. Intente más tarde.",
            "detail": {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
