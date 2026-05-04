# AGENTS.md — Sistema Inventario ICM (backend Django)

Instrucciones para asistentes de código (GitHub Copilot, Cursor, Antigravity, Windsurf, etc.). Estos asistentes deben consultar este archivo y los cursor rules (`.cursor/rules/*.mdc`) antes de modificar lógica de negocio, APIs o tests.

## Documentación fuente (obligatoria como referencia)

| Documento | Propósito |
|-----------|-----------|
| `docs/README_ARQUITECTURA.md` | Arquitectura modular, ledger + stock derivado, BR-01…BR-13, SOLID, testing, Docker |
| `docs/ERS_ICM_Requisitos.md` | RF-001…RF-012, RNF-001…RNF-006, criterios Gherkin, tabla de trazabilidad |
| `docs/README_API.md` | Especificación `/api/v1/`, JWT, tags OpenAPI, checklist de publicación |
| `docs/ICM_Informe_Elicitacion_v2_plus.docx.md` | Contexto de negocio ICM, marca Can, 3 ubicaciones, clientes mayoristas |

## Cursor rules vinculados

| Regla | Globs | Propósito |
|-------|-------|----------|
| [`.cursor/rules/icm-contexto-requisitos.mdc`](.cursor/rules/icm-contexto-requisitos.mdc) | Global | Trazabilidad RF/BR/RNF, roles, zona horaria America/Bogota |
| [`.cursor/rules/icm-capas-django.mdc`](.cursor/rules/icm-capas-django.mdc) | `apps/**/*.py`, `shared/**/*.py` | Separación de responsabilidades: models, serializers, views, services, selectors, permissions |
| [`.cursor/rules/icm-api-openapi.mdc`](.cursor/rules/icm-api-openapi.mdc) | `**/views.py`, `**/serializers.py`, `config/urls.py` | Contrato REST `/api/v1/`, `@extend_schema`, tags, errores uniformes |

## Inicio rápido (comandos frecuentes)

```bash
# Entorno: activar venv (si no está ya activo)
. .venv/Scripts/activate  # Linux/Mac: source .venv/bin/activate

# Setup inicial: migraciones y seed test
python manage.py migrate
python manage.py shell < scripts/seed.py  # opcional

# Desarrollo local
python manage.py runserver 0.0.0.0:8000  # acceso en http://localhost:8000/

# Tests
pytest                          # Todos los tests
pytest apps/movements/tests/    # Tests de un app
pytest -v -k "test_serial"      # Tests que coincidan con patrón
pytest --cov=apps               # Con cobertura

# Linting y formato
black apps/ shared/ config/
isort apps/ shared/ config/

# Docker (producción local)
docker-compose up -d web db    # Web + PostgreSQL
docker-compose exec web python manage.py migrate
docker-compose logs -f web
```

### Configuración de entorno (.env)

Crear `.env` en raíz con variables clave (o pasarlas al entorno) se puede utilizar el `.env.example` como plantilla:

```



**Nota:** `python-decouple` usa defaults en `config/settings/base.py` si no se define la variable. Ver `config("VAR_NAME", default=...)` en el código.

## Dominio breve

- **ICM**: inventario insumos médicos; marca propia **Can** → SKU con prefijo **CAN-** (BR-12).
- **Ubicaciones**: Vitrina, Bodega 1, Bodega 2; stock total = suma por ubicación; traslados no cambian total global (BR-11).
- **Roles**: `almacenista` (24/7, credenciales, ajustes), `auxiliar_despacho` (movimientos; solo **07:00–12:00** y **14:00–17:00** en **America/Bogota**), `administrador` (reportes/KPI, sin escritura).
- **Crítico**: validación cruzada escaneado vs SKU de orden en despacho (BR-08); movimientos/auditoría **inmutables** (BR-10); serial obligatorio Electroterapia en entradas/salidas según catálogo (BR-04); datos personales cliente mayorista y Ley 1581 (RNF-006).

## Reglas de implementación backend

1. **Negocio solo en `services.py`**. `models.py` / `serializers.py` / `views.py` sin reglas de dominio.
2. **Consultas** complejas en `selectors.py` sin efectos secundarios.
3. **Stock**: ledger (`Movement`) como fuente de verdad; actualizar `StockByLocation` solo en la misma transacción que el movimiento; no stock negativo.
4. **API**: REST JSON bajo `/api/v1/`; errores `{ error, message, detail }`; permisos alineados al ERS; OpenAPI con tags oficiales.
5. **Tests**: casos críticos del README de arquitectura (horario auxiliar, inmutabilidad, validación cruzada, serial, devoluciones, ajustes, consistencia ledger).

## Patrones de testing

### Fixtures globales (`conftest.py`)

Disponibles en todo el proyecto:

```python
almacenista_user(db)           # User con role=ALMACENISTA
auxiliar_user(db)              # User con role=AUXILIAR_DESPACHO
administrador_user(db)         # User con role=ADMINISTRADOR
sample_product(db)             # Product (SKU CAN-00000)
sample_locations(db)           # [VITRINA, BODEGA_1, BODEGA_2] pre-creadas
```

### Factories y convenciones

Usar `tests/factories.py` para crear datos de prueba:

```python
@pytest.mark.django_db
def test_register_entry(almacenista_user, sample_product):
    # Setup
    location = LocationFactory(code="BODEGA_1")
    movement = register_entry(
        product=sample_product,
        destination_location=location,
        quantity=10,
        executed_by=almacenista_user,
    )
    # Validate
    assert movement.quantity_resultante_destino == 10
    assert not movement.is_mutable()  # BR-10: inmutable
```

**Factories especiales:**
- `ElectroCategoryFactory` → `requires_serial_number=True`, `is_returnable=True`
- `ProductFactory` → SKU con prefijo `CAN-{n:05d}` automático

### Casos críticos a testear

- **Horario auxiliar** (BR-06): `_same_auxiliar_correction_window()` en franja 07:00–12:00 o 14:00–17:00 America/Bogota
- **Inmutabilidad** (BR-10): Movimientos no tienen `PUT`/`PATCH` en API
- **Validación cruzada** (BR-08): `scanned_code` vs `order_sku` en despacho
- **Serial obligatorio** (BR-04): Electroterapia requiere `serial_number` en entrada/salida
- **Ledger consistencia** (BR-11): `Movement` es fuente de verdad; `StockByLocation` derivado
- **Stock no negativo**: Excepciones `InsufficientStockError` en lógica

## Convenciones de código

### Naming

- **Servicios:** funciones (no clases). Helpers internos con prefijo `_` → `_lock_stock()`.
- **Excepciones:** heredan de `ICMBaseException`; nombres: `{Domain}RequiredError`, `{Validation}Error`.
- **Docstrings:** incluyen RF/BR/RNF impactados:
  ```python
  def register_entry(...) -> Movement:
      """RF-005, RF-006 — Entrada de inventario (BR-04, BR-10, BR-11)."""
  ```
- **Tipos:** `from __future__ import annotations` + type hints en `services.py` y `selectors.py`.

### Flujo típico de API

```
Request → URL dispatcher
       → View (validar autenticación/permisos)
       → Serializer (validar entrada I/O)
       → Service (regla de negocio, @transaction.atomic)
       → Models (persistencia, select_for_update si concurrencia)
       → Response JSON {error, message, detail}
```

### Stock: ledger → derivado

```
Movement (ledger, inmutable)
    ↓
StockByLocation (calculado, actualizado en transacción)
    ↓
API: GET /api/v1/inventory/stock/ (read-only selector)
```

**Principio:** Nunca actualizar stock directamente. Siempre vía movimiento + transacción atómica.

## Antipatrones y pitfalls comunes

| ❌ Evitar | ✅ Hacer | Razón |
|-----------|----------|-------|
| Lógica de negocio en `views.py` | Mover a `services.py` | Reutilización, testabilidad, SOLID |
| Excepciones genéricas (Exception) | Excepciones tipadas (`SerialNumberRequiredError`) | Manejo específico, API limpia |
| N+1 queries en selectors | `select_related()`, `prefetch_related()` | Rendimiento, DB queries optimizadas |
| `select_for_update()` sin `@transaction.atomic` | Envolver con `@transaction.atomic` | Integridad en concurrencia |
| Modificar movimientos vía `PUT`/`PATCH` | Crear corrección con `related_movement` | BR-10: inmutabilidad auditoria |
| Despachar sin validar SKU escaneado | Validación cruzada `scanned_code` vs `order_sku` | BR-08: precisión en salidas |
| Confiar en timestamps del cliente | Usar `timezone.now()` en backend | Consistencia de horarios (America/Bogota) |

## Referencias rápidas por especialidad

### API / OpenAPI

Ver [`.cursor/rules/icm-api-openapi.mdc`](.cursor/rules/icm-api-openapi.mdc) para:
- Prefijo API: `/api/v1/`. Cambios incompatibles → nueva versión `/api/v2/`.
- Documentar endpoints con `@extend_schema`: `summary`, `description`, `tags`, `request`, `responses`, `parameters`.
- Usar únicamente los tags en `shared/openapi.py` para consistencia en Swagger.
- Rutas públicas deben declarar `auth=[]` cuando corresponda.
- Forma uniforme de errores: `{ error, message, detail }`.

### Capas Django

Ver [`.cursor/rules/icm-capas-django.mdc`](.cursor/rules/icm-capas-django.mdc) para:
- `models.py`: entidades y restricciones (sin lógica de negocio).
- `serializers.py`: validación/transformación I/O (sin reglas de dominio).
- `views.py`: validar entrada y delegar (sin lógica de negocio).
- `services.py`: toda la lógica de negocio y transacciones.
- `selectors.py`: lecturas complejas, sin efectos secundarios.
- `permissions.py`: RBAC y restricciones (p. ej. horario auxiliar).

**Principios clave:** operaciones que alteren stock deben usar `@transaction.atomic` y `select_for_update()` donde aplique; movimientos/auditoría inmutables.

### Contexto y trazabilidad

Ver [`.cursor/rules/icm-contexto-requisitos.mdc`](.cursor/rules/icm-contexto-requisitos.mdc) para:
- Antes de cambiar comportamiento o contratos, alinear con `docs/README_ARQUITECTURA.md`, `docs/ERS_ICM_Requisitos.md` y `docs/README_API.md`.
- En cambios de lógica de dominio, referenciar RF/BR/RNF impactados en docstrings/PRs.
- Recordar horario y roles del negocio (`auxiliar_despacho` en America/Bogota: 07:00–12:00 y 14:00–17:00).

