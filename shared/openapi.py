"""
Configuración OpenAPI 3 para drf-spectacular (Swagger UI y ReDoc).

RNF-005 — Documentación explícita; autenticación JWT para probar endpoints desde Swagger.
"""

from __future__ import annotations

# Nombres de tags (deben coincidir con los usados en @extend_schema / extend_schema_view)
TAG_AUTH = "auth"
TAG_SYSTEM = "system"
TAG_CATALOG = "catalog"
TAG_INVENTORY = "inventory"
TAG_MOVEMENTS = "movements"
TAG_PURCHASING = "purchasing"
TAG_DASHBOARD = "dashboard"
TAG_REPORTS = "reports"
TAG_ALERTS = "alerts"
TAG_AUDIT = "audit"
TAG_WEBHOOKS = "webhooks"
TAG_BILLING = "billing"

from typing import Any  # noqa: E402

from drf_spectacular.utils import OpenApiResponse  # noqa: E402


def standardize_errors_hook(
    result: dict[str, Any], generator: Any, request: Any, public: bool
) -> dict[str, Any]:
    """
    Hook de post-procesamiento para estandarizar las respuestas de error en Swagger UI.
    Reemplaza los esquemas generados por defecto por DRF con el componente `ErrorResponse`.
    """
    for _path, path_data in result.get("paths", {}).items():
        for _method, method_data in path_data.items():
            if "responses" not in method_data:
                continue
            responses = method_data["responses"]
            error_content = {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
            # Sobrescribir el contenido de todos los errores (4xx y 5xx) que el generador haya detectado
            for code in list(responses.keys()):
                if code.startswith("4") or code.startswith("5"):
                    # Conservamos la descripción si DRF/Spectacular generó una, sino ponemos genérica
                    desc = responses[code].get("description", f"Error {code}")
                    responses[code] = {
                        "description": desc,
                        "content": error_content,
                    }
    return result


def standard_error_responses(
    *,
    include_400: bool = True,
    include_401: bool = True,
    include_403: bool = False,
    include_404: bool = False,
    include_405: bool = False,
    include_409: bool = False,
    include_422: bool = True,
    include_429: bool = False,
    include_500: bool = False,
) -> dict[int, OpenApiResponse]:
    """Respuesta estándar para documentar errores uniformes en Swagger.

    Devuelve un mapa de códigos HTTP a `OpenApiResponse` con la misma estructura
    JSON que produce `config.exception_handler.custom_exception_handler`.
    """
    responses: dict[int, OpenApiResponse] = {}
    if include_400:
        responses[400] = OpenApiResponse(
            description="Solicitud inválida o con errores de validación."
        )
    if include_401:
        responses[401] = OpenApiResponse(
            description="No autenticado o token inválido/expirado."
        )
    if include_403:
        responses[403] = OpenApiResponse(
            description="Permiso denegado para ejecutar la acción."
        )
    if include_404:
        responses[404] = OpenApiResponse(description="Recurso no encontrado.")
    if include_405:
        responses[405] = OpenApiResponse(
            description="Método no permitido o registro inmutable."
        )
    if include_409:
        responses[409] = OpenApiResponse(
            description="Conflicto de estado (ej. stock insuficiente, o regla de negocio restrictiva)."
        )
    if include_422:
        responses[422] = OpenApiResponse(
            description="Entidad no procesable (errores lógicos o de dominio ICM)."
        )
    if include_429:
        responses[429] = OpenApiResponse(description="Límite de peticiones excedido.")
    if include_500:
        responses[500] = OpenApiResponse(description="Error interno del servidor.")
    return responses


SPECTACULAR_SETTINGS: dict = {
    "TITLE": "ICM — API de Gestión de Inventario y Operaciones",
    "DESCRIPTION": """
API REST del sistema **ICM (Import Corporal Medical)**.

**Schema:** [/api/schema/](/api/schema/)

---
### **Guía de Autenticación**
Para probar los endpoints, haga clic en el botón **Authorize**, use el esquema *BearerAuth* e ingrese el token con el prefijo literal:
`Bearer <access_token>`

> *Token obtenido vía `POST /api/v1/auth/login/`*

---
### **Control de Acceso (RBAC)**
- **Roles:** Almacenista, Auxiliar de Despacho, Administrador.
- **Restricción Horaria:** El rol `auxiliar_despacho` está sujeto a la regla **BR-03** (07:00-12:00 / 14:00-17:00).

---
### **Documentación Adicional**
- **API (referencia detallada):** `docs/api/README_API.md`
- **Requisitos:** `docs/requisitos/ERS_ICM_Requisitos.md`
- **Arquitectura:** `docs/README_ARQUITECTURA.md`
- **Precios:** `docs/pricing/README_PRECIOS_FACTURACION.md`
- **Nota:** el stock se maneja como un ledger inmutable con stock derivado.
    """.strip(),
    "VERSION": "1.0.0",
    "CONTACT": {
        "name": "ICM / Proyecto Nuclear 3 — Universidad Alexander von Humboldt",
    },
    "LICENSE": {
        "name": "Proyecto Formativo / Uso académico — Ley 1581",
    },
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_COERCE_PATH_PK_SUFFIX": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+/",
    # Agrupa operaciones y descripciones en Swagger UI
    "TAGS": [
        {"name": TAG_AUTH, "description": "JWT authentication and user management."},
        {"name": TAG_SYSTEM, "description": "System availability checks."},
        {
            "name": TAG_CATALOG,
            "description": "Categories, products, combos and SKU management.",
        },
        {"name": TAG_INVENTORY, "description": "Locations and stock tracking."},
        {
            "name": TAG_MOVEMENTS,
            "description": "Ledger: entries, dispatches, transfers, returns, adjustments and invoices.",
        },
        {
            "name": TAG_DASHBOARD,
            "description": "Operational read model for executive UI and KPIs.",
        },
        {"name": TAG_REPORTS, "description": "Read-only reports and KPIs."},
        {
            "name": TAG_ALERTS,
            "description": "Operational alerts and real-time polling.",
        },
        {"name": TAG_AUDIT, "description": "Audit logs (read-only, immutable)."},
        {
            "name": TAG_WEBHOOKS,
            "description": "Webhook endpoints and delivery management (almacenista only — IsAlmacenista).",
        },
        {
            "name": TAG_BILLING,
            "description": "Commercial billing: multi-product invoices, void, stats and company config.",
        },
    ],
    # Botón "Authorize" en Swagger UI y componente de Error Uniforme
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Prefijo literal: Bearer + espacio + access_token (login o refresh).",
            }
        },
        "schemas": {
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Código de error del sistema o cliente (ej. 'VALIDATION_ERROR', 'NOT_FOUND', 'INSUFFICIENT_STOCK').",
                    },
                    "message": {
                        "type": "string",
                        "description": "Mensaje legible para el usuario que describe el error.",
                    },
                    "detail": {
                        "type": "object",
                        "description": "Detalles adicionales, comúnmente un diccionario con errores específicos por campo o reglas.",
                        "additionalProperties": True,
                    },
                },
                "required": ["error", "message", "detail"],
            }
        },
    },
    # Ejemplo de respuesta de error uniforme para que Swagger muestre ejemplos concretos
    "examples": {
        "ErrorResponseExample": {
            "summary": "Ejemplo de error uniforme",
            "value": {
                "error": "INVALID_CREDENTIALS",
                "message": "El usuario o la contraseña son incorrectos.",
                "detail": {},
            },
        }
    },
    "SECURITY": [{"BearerAuth": []}],
    "ENUM_NAME_OVERRIDES": {
        # Unifica el enum price_strategy de ProductCombo bajo un nombre canónico
        "PriceStrategyEnum": ["derived", "fixed"],
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "shared.openapi.standardize_errors_hook",
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": False,
        "filter": True,
        "persistAuthorization": True,
        "tryItOutEnabled": True,
    },
}
