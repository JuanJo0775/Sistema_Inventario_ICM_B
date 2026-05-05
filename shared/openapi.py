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
TAG_REPORTS = "reports"
TAG_ALERTS = "alerts"
TAG_AUDIT = "audit"

from typing import Any

def standardize_errors_hook(result: dict[str, Any], generator: Any, request: Any, public: bool) -> dict[str, Any]:
    """
    Hook de post-procesamiento para estandarizar las respuestas de error en Swagger UI.
    Reemplaza los esquemas generados por defecto por DRF con el componente `ErrorResponse`.
    """
    for path, path_data in result.get("paths", {}).items():
        for method, method_data in path_data.items():
            if "responses" not in method_data:
                continue
            responses = method_data["responses"]
            error_content = {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    }
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

SPECTACULAR_SETTINGS: dict = {
    "TITLE": "ICM — API de Gestión de Inventario y Operaciones",
    "DESCRIPTION": """
# ICM — API de Gestión de Inventario y Operaciones
**Version:** `1.0.0` | **OAS:** `3.0` | **Schema:** [/api/schema/](/api/schema/)

API REST del sistema **ICM (Import Corporal Medical)**.

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
- **Referencia:** `ERS_ICM_Requisitos.md v1.0`
- **Arquitectura:** Ledger inmutable + Stock derivado.
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
        {"name": TAG_CATALOG, "description": "Categories, products, and combos."},
        {"name": TAG_INVENTORY, "description": "Locations and stock tracking."},
        {"name": TAG_MOVEMENTS, "description": "Ledger: entries, dispatches, transfers, returns, adjustments."},
        {"name": TAG_REPORTS, "description": "Read-only reports and KPIs."},
        {"name": TAG_ALERTS, "description": "Operational alerts."},
        {"name": TAG_AUDIT, "description": "Audit logs (read-only)."},
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
                        "description": "Código de error del sistema o cliente (ej. 'validation_error', 'not_found', 'insufficient_stock').",
                    },
                    "message": {
                        "type": "string",
                        "description": "Mensaje legible para el usuario que describe el error.",
                    },
                    "detail": {
                        "type": "object",
                        "description": "Detalles adicionales, comúnmente un diccionario con errores específicos por campo o reglas.",
                        "additionalProperties": True,
                    }
                },
                "required": ["error", "message", "detail"]
            }
        }
    },
    "SECURITY": [{"BearerAuth": []}],
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
