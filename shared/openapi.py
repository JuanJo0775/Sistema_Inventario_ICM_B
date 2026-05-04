"""
Configuración OpenAPI 3 para drf-spectacular (Swagger UI y ReDoc).

RNF-005 — Documentación explícita; autenticación JWT para probar endpoints desde Swagger.
"""

from __future__ import annotations

# Nombres de tags (deben coincidir con los usados en @extend_schema / extend_schema_view)
TAG_AUTH = "Autenticación"
TAG_SYSTEM = "Sistema"
TAG_CATALOG = "Catálogo"
TAG_INVENTORY = "Inventario"
TAG_MOVEMENTS = "Movimientos"
TAG_REPORTS = "Reportes"
TAG_ALERTS = "Alertas"
TAG_AUDIT = "Auditoría"

SPECTACULAR_SETTINGS: dict = {
    "TITLE": "ICM — API de Gestión de Inventario y Operaciones",
    "DESCRIPTION": """
API REST del sistema ICM (Import Corporal Medical).

**Autenticación:** en Swagger use **Authorize**, esquema *BearerAuth*, y pegue: `Bearer <access_token>`  
(obtenido en `POST /api/v1/auth/login/`).

**Roles:** `almacenista`, `auxiliar_despacho`, `administrador` (RBAC). Los auxiliares tienen restricción horaria (BR-03).

**Referencia:** ERS_ICM_Requisitos.md v1.0; arquitectura ledger + stock derivado.
    """.strip(),
    "VERSION": "1.0.0",
    "CONTACT": {
        "name": "ICM / Proyecto Nuclear 3 — Univ. Alexander von Humboldt",
    },
    "LICENSE": {
        "name": "Uso académico / proyecto formativo",
    },
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_COERCE_PATH_PK_SUFFIX": True,
    # Agrupa operaciones y descripciones en Swagger UI
    "TAGS": [
        {"name": TAG_AUTH, "description": "RF-001, RF-002 — JWT, sesión y gestión de usuarios."},
        {"name": TAG_SYSTEM, "description": "Comprobaciones de disponibilidad."},
        {"name": TAG_CATALOG, "description": "RF-003 — Categorías, productos, combos y resolución de identificadores."},
        {"name": TAG_INVENTORY, "description": "RF-004 — Ubicaciones, stock por producto/ubicación y búsqueda."},
        {"name": TAG_MOVEMENTS, "description": "RF-005 a RF-009 — Ledger: entradas, salidas, traslados, devoluciones, ajustes."},
        {"name": TAG_REPORTS, "description": "RF-010 — Reportes y KPIs (solo lectura)."},
        {"name": TAG_ALERTS, "description": "RF-011 — Alertas operativas."},
        {"name": TAG_AUDIT, "description": "RF-012 — Log de auditoría (solo almacenista)."},
    ],
    # Botón "Authorize" en Swagger UI
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Prefijo literal: Bearer + espacio + access_token (login o refresh).",
            }
        }
    },
    "SECURITY": [{"BearerAuth": []}],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": False,
        "filter": True,
        "persistAuthorization": True,
        "tryItOutEnabled": True,
    },
    "REDOC_DIST": "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
}
