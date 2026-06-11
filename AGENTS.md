# AGENTS.md — Sistema Inventario ICM (backend Django)

Instrucciones para asistentes de código (GitHub Copilot, Cursor, Antigravity, Windsurf, etc.).

Propósito: proporcionar una guía rápida y completa en la raíz del repositorio para asistentes de código. Esta versión es un espejo legible de la instrucción canonical en `.github/instructions/Agents.instructions.md`.

## Documentación fuente (obligatoria como referencia)

| Documento | Propósito |
|-----------|-----------|
| `docs/README_ARQUITECTURA.md` | Arquitectura modular, ledger + stock derivado, BR-01…BR-15, SOLID, testing, Docker |
| `docs/requisitos/ERS_ICM_Requisitos.md` | Requisitos funcionales, criterios Gherkin y trazabilidad |
| `docs/api/README_API.md` | Especificación `/api/v1/`, JWT, tags OpenAPI, checklist de publicación |
| `docs/test/README_TEST.md` | Guía oficial de pruebas: suite Gherkin, unit/integration y comandos de regeneración |
| `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` | Matriz viva RF ↔ tests con cobertura y brechas documentadas |
| `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` | Contexto de negocio ICM, alcance y supuestos |
| `docs/GUIA_ONBOARDING.md` | Guía de onboarding para nuevos desarrolladores y configuraciones locales |
| `docs/adr/README_ADR.md` | Decisiones arquitectónicas registradas (ADRs)
| `docs/adr/ADR-001.md` | ADR-001 (ejemplo y antecedentes) — revisar carpeta `docs/adr/` para más ADRs
| `docs/calidad_restricciones/README_ATRIBUTOS_CALIDAD.md` | Atributos de calidad y criterios de aceptación
| `docs/calidad_restricciones/README_RESTRICCIONES.md` | Restricciones y reglas no funcionales importantes
| `docs/CI/README_CICD.md` | Runbook de CI/CD: pipelines, despliegue, promoción, backups, rollback y operación segura |
| `README.md` | Resumen del proyecto y enlaces rápidos
| `AGENTS.md` | Guía rápida para asistentes de código (este archivo)

## Reglas y políticas vinculadas

Revisar las instrucciones internas y políticas del repositorio (canonical): [`.github/instructions/Agents.instructions.md`](.github/instructions/Agents.instructions.md) y [`.github/instructions/Organizar_Cambios.instructions.md`](.github/instructions/Organizar_Cambios.instructions.md). Las antiguas "cursor rules" ya no se usan y se han eliminado de esta guía.

## Recordatorio operativo

Antes de cambiar comportamiento o contratos, alinea el trabajo con la documentación oficial del repo y con estas reglas prácticas:

- Arquitectura: el negocio vive en `services.py`; las lecturas complejas viven en `selectors.py`; `models.py`, `serializers.py` y `views.py` no deben contener reglas de dominio.
- Inventario: `Movement` es la fuente de verdad; `StockByLocation` es derivado y solo se actualiza en la misma transacción del movimiento; no se permite stock negativo.
- API: el contrato REST usa `/api/v1/`, JSON, JWT Bearer y errores uniformes con `{ error, message, detail }`; los endpoints nuevos o modificados deben documentarse con `@extend_schema` y usar solo los tags oficiales definidos en `shared/openapi.py`.
- Negocio crítico: mantener inmutabilidad de movimientos y auditoría, validación cruzada de despacho (`scanned_code` vs `order_sku`), serial obligatorio para Electroterapia, SKU definido por usuario (patrón 1–4 letras, guion, 1–4 dígitos) y la ventana horaria de `auxiliar_despacho` en `America/Bogota`.
- Desarrollo: en local se usa PostgreSQL; no asumir Docker salvo que la tarea o el usuario lo pidan de forma explícita.
- Validación: para cambios de lógica, prioriza tests del dominio afectado y cubre los casos críticos del ERS y la arquitectura antes de ampliar el alcance.
- Pruebas: usa `docs/test/README_TEST.md` como guía operativa; si cambias escenarios Gherkin o tests no Gherkin, regenera la documentación correspondiente y revisa `docs/test/TRAZABILIDAD_ERS_GHERKIN.md`.

## Inicio rápido (comandos frecuentes)

```bash
# Activar entorno virtual
. .venv/Scripts/activate    # PowerShell: . .venv/Scripts/Activate.ps1

# Migraciones y seed (local)
python manage.py migrate
python manage.py create_almacenista  # opcional, requerido antes del seed
python scripts/seed_db/run.py  # opcional

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

## Configuración de entorno (.env)

- Crear `.env` en raíz con variables clave (o pasarlas al entorno) usando `.env.example` como plantilla.
- `python-decouple` usa defaults en `config/settings/base.py` si no se define la variable.

## Dominio breve

- **ICM**: inventario insumos médicos; SKU definido por el usuario siguiendo el patrón 1–4 letras, un guion y 1–4 dígitos (ej: AB-1234).
- **Ubicaciones**: Vitrina, Bodega 1, Bodega 2; stock total = suma por ubicación; traslados no cambian total global.
- **Roles**: `almacenista` (24/7), `auxiliar_despacho` (movimientos en franjas horarias), `administrador` (reportes/KPI, sin escritura).
- **Crítico**: validación cruzada escaneado vs SKU de orden en despacho; movimientos/auditoría inmutables; serial obligatorio Electroterapia; protección de datos personales según RNF-006.

## Reglas de implementación backend

1. Negocio solo en `services.py`. `models.py` / `serializers.py` / `views.py` sin reglas de dominio.
2. Consultas complejas en `selectors.py` sin efectos secundarios.
3. Stock: ledger (`Movement`) como fuente de verdad; actualizar `StockByLocation` solo en la misma transacción que el movimiento; no stock negativo.
4. API: REST JSON bajo `/api/v1/`; errores `{ error, message, detail }`; permisos alineados al ERS; OpenAPI con tags oficiales.
5. Tests: casos críticos del README de arquitectura (horario auxiliar, inmutabilidad, validación cruzada, serial, devoluciones, ajustes, consistencia ledger).

## Patrones de testing

### Fixtures globales (`conftest.py`)

Disponibles en todo el proyecto:

```
almacenista_user(db)           # User con role=ALMACENISTA
auxiliar_user(db)              # User con role=AUXILIAR_DESPACHO
administrador_user(db)         # User con role=ADMINISTRADOR
sample_product(db)             # Product (SKU PRD-0001)
sample_locations(db)           # [VITRINA, BODEGA_1, BODEGA_2] pre-creadas
```

### Factories y convenciones

Usar `tests/factories.py` para crear datos de prueba. Ejemplo:

```python
@pytest.mark.django_db
def test_register_entry(almacenista_user, sample_product):
	location = LocationFactory(code="BODEGA_1")
	movement = register_entry(
		product=sample_product,
		destination_location=location,
		quantity=10,
		executed_by=almacenista_user,
	)
	assert movement.quantity_resultante_destino == 10
	assert not movement.is_mutable()
```

Factories especiales:
- `ElectroCategoryFactory` → `requires_serial_number=True`, `is_returnable=True`
- `ProductFactory` → SKU generado siguiendo el patrón `PRD-0001`

### Casos críticos a testear

- Horario auxiliar: `_same_auxiliar_correction_window()` debe validar 07:00–12:00 y 14:00–17:00 (America/Bogota).
- Inmutabilidad: movimientos no deben ser editables via `PUT`/`PATCH`.
- Validación cruzada: `scanned_code` vs `order_sku` en despacho.
- Serial obligatorio para categorías de Electroterapia.
- Consistencia ledger: `Movement` como fuente de verdad y `StockByLocation` derivado.
- Stock no negativo: lanzar `InsufficientStockError` cuando aplique.

## Convenciones de código

- Servicios: funciones, no clases; helpers privados con prefijo `_`.
- Excepciones: heredar de `ICMBaseException` y nombrarse de forma específica (`SerialNumberRequiredError`).
- Docstrings: incluir referencias a RF/BR/RNF cuando modifiquen lógica de negocio.
- Tipos: usar `from __future__ import annotations` y type hints en `services.py` y `selectors.py`.

## Flujo típico de cambio en backend

Request → URL dispatcher → View (auth/perm) → Serializer (I/O validation) → Service (@transaction.atomic) → Models (persistencia, select_for_update si aplica) → Response JSON `{ error, message, detail }`

## Antipatrones y buenas prácticas

- Evitar lógica de negocio en `views.py` o `serializers.py`.
- No usar excepciones genéricas; preferir excepciones tipadas.
- Usar `select_for_update()` siempre dentro de `@transaction.atomic`.
- No modificar movimientos existentes; crear movimientos de corrección relacionados.

## Uso práctico para asistentes

- Antes de tocar archivos en `apps/` o `shared/`, leer los documentos listados en la sección "Documentación fuente".
- Si cambias reglas de negocio, añade/actualiza tests del dominio y referencia RF/BR/RNF en la docstring y PR.
- Para endpoints nuevos o cambios de contrato, documenta con `@extend_schema` y usa los tags de `shared/openapi.py`.

## Anexo: regeneración de documentación antes de commit/push

Regla: cada vez que se modifica código de pruebas o los escenarios Gherkin (`tests/`, `tests/ers/`, `apps/*/tests/`), el autor del cambio debe regenerar la documentación de pruebas antes de hacer `commit` y `push`.

- Comando principal (regenera TODA la documentación de tests: unit, integration, gherkin y auxiliary):

```bash
python -m scripts.generate_docs
```

- También disponible (legacy alias, mismo efecto):

```bash
python scripts/parse_ers_gherkin.py
```

- Para regenerar solo una categoría específica:

```bash
python -m scripts.generate_docs --only auxiliary
python -m scripts.generate_docs --only unit
python -m scripts.generate_docs --only integration
python -m scripts.generate_docs --only gherkin
```

- Incluir los archivos generados en el mismo commit que introduce los cambios en los tests (no separar en commits independientes).

Regla: cada vez que cambia la estructura del proyecto (añadir/quitar carpetas top-level, mover apps, o cambios que afectan la vista del árbol del proyecto), el autor debe regenerar la sección de estructura del proyecto en la documentación de arquitectura antes de `commit`/`push`.

- Comando recomendado (genera/actualiza `docs/README_ARQUITECTURA.md`):

```bash
python scripts/generate_project_structure.py
```

- Incluir los cambios generados por este script en el mismo commit que modifica la estructura del proyecto.

Checklist rápido antes de `git push` cuando tocas tests o estructura:

- Ejecutaste `python -m scripts.generate_docs` (o `python scripts/parse_ers_gherkin.py`) si cambiaste tests/gherkin
- Ejecutaste `python scripts/generate_project_structure.py` si cambiaste la estructura del repo
- Añadiste los archivos generados al `git add` y están incluidos en el mismo commit
- En la descripción del PR listaste explícitamente los comandos usados para regenerar la documentación

Nota operativa: se recomienda añadir hooks locales (`pre-commit` o `pre-push`) que ejecuten estos scripts o, como mínimo, comprobar en CI que los artefactos generados estén actualizados. Si se detecta que la documentación generada no está sincronizada con los cambios, el PR debe marcarse para corrección.

## Sincronización y mantenimiento

- La instrucción canonical está en [`.github/instructions/Agents.instructions.md`](.github/instructions/Agents.instructions.md). Mantén ambos archivos sincronizados.
- Si actualizas políticas que afectan flujo de trabajo (commits, ramas, tests), actualiza también [`.github/instructions/Organizar_Cambios.instructions.md`](.github/instructions/Organizar_Cambios.instructions.md) y menciona los RF/BR/RNF en el PR.

## Contacto y notas finales


Mantén estas guías actualizadas; son la referencia obligatoria para asistentes automáticos y humanos que modifiquen lógica de negocio, contratos de API o tests.

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

Estas reglas forman parte de la documentación canonical para asistentes y revisores humanos.


