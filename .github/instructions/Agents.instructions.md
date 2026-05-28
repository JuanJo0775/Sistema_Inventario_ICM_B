---
description: Instrucciones para asistentes de código y reglas operativas para agentes (Copilot, Cursor, etc.)
applyTo: ".*"
---

# Instrucciones para agentes y asistentes de código — Sistema Inventario ICM

Propósito: proporcionar una guía autorizada, centralizada y fácilmente consultable para asistentes de código (GitHub Copilot, Cursor, etc.) que vayan a modificar lógica de negocio, APIs, tests o documentación en este repositorio.

Documentos de referencia (consultar siempre antes de cambiar comportamiento):
- `docs/README_ARQUITECTURA.md` — Arquitectura modular, ledger + stock derivado, BR-01…BR-13, SOLID, testing, Docker
- `docs/requisitos/ERS_ICM_Requisitos.md` — Requisitos funcionales y criterios Gherkin
- `docs/api/README_API.md` — Especificación de la API `/api/v1/`, JWT, tags OpenAPI
- `docs/test/README_TEST.md` — Guía oficial de pruebas y regeneración de documentación
- `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` — Matriz RF ↔ tests
- `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` — Contexto de negocio y alcance
- `docs/GUIA_ONBOARDING.md` — Guía de onboarding y checklist para desarrolladores nuevos
- `docs/adr/README_ADR.md` — Decisiones arquitectónicas registradas (ADRs). Revisar `docs/adr/` para ADRs individuales
- `docs/adr/ADR-001.md` — ADR-001 (referencia de ejemplo)
- `docs/calidad_restricciones/README_ATRIBUTOS_CALIDAD.md` — Atributos de calidad y criterios
- `docs/calidad_restricciones/README_RESTRICCIONES.md` — Restricciones y reglas no funcionales
- `docs/CI-CD/README_CICD.md` — Runbook de CI/CD: pipelines, despliegue, promoción por digest, backups, rollback y operación segura
- `README.md` — Resumen del proyecto y enlaces rápidos
- `AGENTS.md` — Guía rápida para asistentes de código (archivo en la raíz)

Reglas y políticas locales:
- La política canonical y las instrucciones internas se encuentran en `.github/instructions/Agents.instructions.md` y en [AGENTS.md](AGENTS.md) en la raíz.
- Nota: las antiguas "cursor rules" se han eliminado del proceso; no se usan más en este repositorio.

Recordatorio operativo (resumen rápido):
- Arquitectura: la lógica de negocio reside en `services.py`.
- Lecturas complejas: `selectors.py` (sin efectos secundarios).
- Modelos/Serializers/Views: sin reglas de dominio; delegar a `services.py`.
- Stock: `Movement` = ledger (fuente de verdad); `StockByLocation` es derivado y se actualiza en la misma transacción.
- Movimientos: inmutables; nunca usar `PUT`/`PATCH` para alterar movimientos existentes.

Inicio rápido (comandos frecuentes):

```bash
# Activar entorno virtual
. .venv/Scripts/activate    # Windows PowerShell: . .venv/Scripts/Activate.ps1

# Migraciones y seed (local)
python manage.py migrate
python manage.py shell < scripts/seed.py  # opcional

# Desarrollo local
python manage.py runserver 0.0.0.0:8000

# Tests
pytest
pytest apps/movements/tests/
pytest -v -k "test_serial"
pytest --cov=apps

# Formateo
black apps/ shared/ config/
isort apps/ shared/ config/
```

Configuración de entorno:
- Crear `.env` en la raíz usando `.env.example` como plantilla cuando corresponda.
- `python-decouple` usa defaults en `config/settings/base.py` si no se define una variable.

Dominio breve (contexto que siempre debes tener en mente):
- ICM: inventario insumos médicos. SKU definido por usuario con patrón 1–4 letras, guion, 1–4 dígitos (ej: AB-1234).
- Ubicaciones: Vitrina, Bodega 1, Bodega 2. Stock total = suma por ubicación.
- Roles: `almacenista` (24/7), `auxiliar_despacho` (movimientos en franjas horarias), `administrador` (reportes).
- Validaciones críticas: serial obligatorio en Electroterapia, validación cruzada `scanned_code` vs `order_sku`, no stock negativo.

Reglas de implementación backend (obligatorias):
1. Negocio solo en `services.py`.
2. Consultas complejas en `selectors.py` sin efectos secundarios.
3. `Movement` como ledger inmutable; actualizaciones de `StockByLocation` solo dentro de la misma transacción que crea el movimiento.
4. Operaciones que alteren stock deben usar `@transaction.atomic` y `select_for_update()` cuando corresponda.
5. Manejar errores con excepciones tipadas que hereden de `ICMBaseException`.

Patrones de testing y fixtures:
- Fixtures globales en `conftest.py` (ej: `almacenista_user`, `auxiliar_user`, `sample_product`, `sample_locations`).
- Usar `tests/factories.py` y factories específicas (ElectroCategoryFactory, ProductFactory).
- Casos críticos: horario de `auxiliar_despacho`, inmutabilidad de movimientos, validación cruzada, serial obligatorio, consistencia ledger, stock no negativo.

Convenciones de código y nomenclatura:
- Servicios: funciones (no clases); helpers internos con prefijo `_`.
- Commits y PRs: claros, agrupados por funcionalidad; seguir convenciones del repo.
- Docstrings: incluir referencias RF/BR/RNF cuando se modifique lógica de negocio.

Flujo típico de cambio en backend:

Request → View (auth/perm) → Serializer (I/O validation) → Service (@transaction.atomic) → Models (persistencia) → Response JSON `{ error, message, detail }`

Stock: ledger → derivado:

Movement (ledger, inmutable)
    ↓
StockByLocation (actualizado en transacción)
    ↓
API read-only para stock (`/api/v1/inventory/stock/`)

Antipatrones a evitar:
- Lógica de negocio en `views.py` o `serializers.py`.
- Excepciones genéricas; preferir excepciones tipadas.
- `select_for_update()` sin `@transaction.atomic`.
- Modificar movimientos existentes vía `PUT`/`PATCH`.

Referencias rápidas por especialidad:
- API / OpenAPI: usar `@extend_schema`, tags en `shared/openapi.py`, errores uniformes.
- Capas Django: `models.py`, `serializers.py`, `views.py` sin lógica; `services.py` = negocio.
- Contexto y trazabilidad: antes de cambiar, alinear con `docs/README_ARQUITECTURA.md` y `docs/requisitos/ERS_ICM_Requisitos.md`.

Uso práctico para asistentes:
- Antes de tocar cualquier archivo en `apps/` o `shared/`, leer los documentos listados arriba.
- Si cambias reglas de negocio: añadir/actualizar tests del dominio y referenciar RF/BR/RNF en docstrings y PR.
- Al crear endpoints nuevos o modificar contratos, documentar con `@extend_schema` y usar tags oficiales.

Contacto y notas finales:
- Este archivo actúa como la versión canonical para reglas de agentes. Manténlo sincronizado con `AGENTS.md` en la raíz del repo.

## Reglas heredadas (resumen revisado)

He revisado las reglas que antes residían en `.cursor/rules/` y las he consolidado aquí. He eliminado duplicados y contenido no alineado; a continuación queda la versión pulida con las obligaciones, checklists y ejemplos esenciales.

### 1) Contexto y trazabilidad (obligatorio)

- Antes de cambiar comportamiento o contratos, alinear siempre con:
  - `docs/README_ARQUITECTURA.md`, `docs/requisitos/ERS_ICM_Requisitos.md`, `docs/api/README_API.md`, `docs/ICM_Informe_Elicitacion_v2_plus.docx.md`.
- Documentar en docstrings y en la descripción del PR los RF/BR/RNF impactados (ej: "RF-005, BR-10").
- Roles y horario crítico: `almacenista`, `auxiliar_despacho`, `administrador`. Ventana auxiliar: America/Bogota 07:00–12:00 y 14:00–17:00.

### 2) Capas Django — responsabilidades (obligatorio)

- Regla central: negocio en `services.py`; `selectors.py` para lecturas; `models.py`/`serializers.py`/`views.py` sin lógica de dominio.
- Validaciones transaccionales y locks en `services.py`; permisos de tiempo en `permissions.py`.

Checklist rápido:
- `views.py`: orquestación HTTP, auth/perm, delega a servicios.
- `serializers.py`: validación I/O, sin lógica de dominio que requiera BD o transacción.
- `services.py`: `@transaction.atomic`, `select_for_update()` cuando aplique, creación de `Movement`.

### 3) API / OpenAPI (contrato)

- Prefijo: `/api/v1/`. Documentar con `@extend_schema` y usar solo `tags` oficiales de `shared/openapi.py`.

Checklist `@extend_schema`:
- `summary` claro
- `description` (incluir RF cuando aplique)
- `tags` oficiales
- `request` y `responses` definidos
- rutas públicas: `auth=[]`

### 4) Transacciones y concurrencia (clave para stock)

- Toda operación que escriba `StockByLocation` o cree `Movement` debe usar `@transaction.atomic` y, cuando haya riesgo de carrera, `select_for_update()` sobre las filas afectadas.

Ejemplo mínimo:

```python
from django.db import transaction

@transaction.atomic
def register_entry(...):
    stock_row = StockByLocation.objects.select_for_update().get_or_create(...)[0]
    # validar invariantes (seriales, suficiente stock)
    # actualizar stock y crear Movement (ledger inmutable)
```

### 5) Trazabilidad en código (docstrings)

- Todo cambio que afecte invariantes del dominio debe incluir docstring que cite RF/BR/RNF implementados.

Ejemplo de docstring:

```python
"""
RF-005 — Registrar entrada de inventario.

Implementa:
- BR-04: Serial obligatorio en Electroterapia.
- BR-10: Movimiento inmutable.
"""
```

### 6) Buenas prácticas de entrega

- Si cambias contratos: actualizar `docs/api/README_API.md`, OpenAPI y tests de integración.
- Añadir tests de concurrencia al cambiar operaciones de stock.
- Documentar en PR los RF/BR/RNF afectados y el plan de pruebas.

Estas reglas sustituyen la dependencia de Cursor y forman parte de la documentación canonical para asistentes y revisores humanos.
