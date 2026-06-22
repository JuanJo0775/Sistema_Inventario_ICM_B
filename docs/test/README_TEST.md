# Documentación de pruebas — Sistema Inventario ICM

## Fuentes de verdad

| Prioridad | Archivo | Rol |
|-----------|---------|-----|
| 1 | `docs/requisitos/ERS_ICM_Requisitos.md` | Requisitos funcionales y criterios Gherkin (Given/When/Then) |
| 2 | `docs/README_ARQUITECTURA.md` | Estructura de capas (services/selectors/views) |
| 3 | `docs/api/README_API.md` | Contratos HTTP, códigos de respuesta |

---

## Estructura de documentación generada

| Carpeta / archivo | Contenido |
|-------------------|-----------|
| `docs/test/scenarios/` | Un `.md` por escenario Gherkin del ERS (`RF001-S01.md`, etc.) |
| `docs/test/unit/` | Un `.md` por test unitario (`UNIT-0001.md`, etc.) |
| `docs/test/integration/` | Un `.md` por test de integración (`INT-0001.md`, etc.) |
| `docs/test/auxiliary/` | Un `.md` por test auxiliar (scripts, shared, SLA) — segregado en `scripts/`, `shared/`, `sla/` con prefijos `SCR`, `SHA`, `SLA` |
| `docs/test/gherkin_scenarios.json` | Metadatos parseados del ERS (generado, no editar a mano) |
| `docs/test/gherkin_pending.json` | Escenarios backend aún sin automatizar — registrar aquí para que CI haga skip limpio |
| `docs/test/gherkin_out_of_scope.json` | Escenarios solo verificables por E2E/UI — skip permanente en backend |
| `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` | Matriz RF ↔ tests (referencia viva) |

---

## Cómo añadir un nuevo escenario — guía completa

### Paso 1 — Escribir el escenario en el ERS

Abre `docs/requisitos/ERS_ICM_Requisitos.md` y localiza el requisito funcional (RF) correspondiente.
Bajo la sección **Criterios de Aceptación (Formato Gherkin)** del RF, añade el escenario con la siguiente estructura:

```
### Scenario N: <Título descriptivo>

**Given (Dado que):**
- <precondición 1>
- <precondición 2>

**When (Cuando):**
- <acción del actor>

**Then (Entonces):**
- <resultado esperado 1>
- <resultado esperado 2>
```

Reglas de numeración:
- El identificador se forma como `RFxxx-SNN` donde `xxx` es el número del requisito y `NN` es el número de escenario dentro de ese RF.
- Los escenarios deben ser consecutivos dentro de su RF, sin huecos.
- Si añades un RNF nuevo, usa `RNFxxx-SNN` con la misma convención.

El ERS es la única fuente autorizada para agregar o modificar escenarios. No crear escenarios directamente en los archivos de implementación sin que existan primero en el ERS.

### Paso 2 — Regenerar los metadatos y la documentación

```bash
python -m scripts.generate_docs
```

Este comando:
- Parsea el ERS y actualiza `docs/test/gherkin_scenarios.json`
- Genera o actualiza el `.md` del escenario en `docs/test/scenarios/`
- Regenera `docs/test/all_scenarios.md`

Verifica que el nuevo escenario aparece en la salida:
```bash
python -m scripts.generate_docs --check
```

### Paso 3 — Decidir el tipo de automatización

| Situación | Acción |
|-----------|--------|
| El comportamiento es verificable por API/servicio Django | → Paso 4: implementar en `tests/ers/impl/` |
| El comportamiento requiere UI, navegador o flujo E2E | → Paso 5: declarar en `gherkin_out_of_scope.json` |
| El comportamiento es backend pero la implementación se aplaza | → Paso 6: declarar en `gherkin_pending.json` |

Si no se hace uno de los tres, la suite fallará en tiempo de colección con `[MISSING]` — esto es intencional para evitar escenarios olvidados.

### Paso 4 — Implementar el escenario (backend automatable hoy)

**4a. Localiza el archivo de dominio correcto:**

| RF | Archivo |
|----|---------|
| RF001, RF002 | `tests/ers/impl/auth.py` |
| RF003 | `tests/ers/impl/catalog.py` |
| RF004 | `tests/ers/impl/inventory.py` |
| RF005–RF009 | `tests/ers/impl/movements.py` |
| RF010 | `tests/ers/impl/reports.py` |
| RF011 | `tests/ers/impl/alerts.py` |
| RF012 | `tests/ers/impl/audit.py` |
| RF013 | `tests/ers/impl/pricing.py` |
| RF019–RF025 | `tests/ers/impl/purchasing.py` |
| RNF003–RNF006 | `tests/ers/impl/nonfunctional.py` |

Si el escenario pertenece a un RF completamente nuevo, crea un archivo de dominio nuevo (`tests/ers/impl/<dominio>.py`) e importa su `IMPLEMENTATIONS` en `tests/ers/impl/registry.py`.

**4b. Escribe la función de implementación:**

```python
def impl_rf0XX_sNN(authenticated_almacenista_client: APIClient, sample_product, db):
    # El nombre de cada parámetro debe ser exactamente el nombre de una fixture
    # declarada en conftest.py o en el mismo módulo de pruebas.
    from apps.mi_modulo.models import MiModelo

    url = reverse("nombre-del-endpoint")
    r = authenticated_almacenista_client.post(url, {...}, format="json")

    assert r.status_code == status.HTTP_201_CREATED
    assert MiModelo.objects.filter(...).exists()
```

Convenciones:
- Nombre: `impl_rf{NNN}_s{NN}` en minúsculas con underscores.
- Los parámetros se inyectan por nombre desde `conftest.py` — no usar `@pytest.fixture` aquí.
- Fixtures globales disponibles: `api_client`, `almacenista_user`, `auxiliar_user`, `administrador_user`, `sample_product`, `sample_locations`, `authenticated_almacenista_client`, `authenticated_administrador_client`.
- Los imports de Django/DRF pueden ir al nivel de módulo o dentro de la función; preferir dentro de la función para no alargar el encabezado del archivo.

**4c. Registra la función en el dict `IMPLEMENTATIONS` del mismo archivo:**

```python
IMPLEMENTATIONS: dict[str, object] = {
    ...,
    "RF0XX-SNN": impl_rf0XX_sNN,   # añadir esta línea
}
```

La clave debe coincidir exactamente con el ID del escenario en `gherkin_scenarios.json` (mayúsculas, guion, sin espacios).

**4d. Si el escenario estaba en `gherkin_pending.json`, elimina su entrada:**

```json
// Eliminar la entrada correspondiente de docs/test/gherkin_pending.json
```

### Paso 5 — Escenario solo E2E/UI (fuera de alcance backend)

Añade una entrada en `docs/test/gherkin_out_of_scope.json`:

```json
"RF0XX-SNN": {
  "scope": "frontend-or-e2e",
  "reason": "Requiere interacción con navegador — verificar con Playwright/Cypress."
}
```

La suite hará `pytest.skip("[SCOPE] ...")` en lugar de fallar.

### Paso 6 — Escenario backend aplazado

Añade una entrada en `docs/test/gherkin_pending.json`:

```json
"RF0XX-SNN": {
  "reason": "Módulo X pendiente de implementar — sprint Y",
  "since": "YYYY-MM-DD"
}
```

La suite hará `pytest.skip("[PENDING] ...")` en lugar de fallar. Cuando se automatice, eliminar la entrada y seguir el Paso 4.

### Paso 7 — Verificar

```bash
# Colección limpia (no debe haber errores ni [MISSING])
pytest tests/ers --collect-only -q

# Suite Gherkin completa
pytest tests/ers -v --tb=short

# No deben caerse los tests unitarios existentes
pytest -q -k "not integration and not ers"
```

---

## Arquitectura del sistema Gherkin

```
docs/requisitos/ERS_ICM_Requisitos.md       ← fuente de verdad de escenarios
        ↓ python -m scripts.generate_docs
docs/test/gherkin_scenarios.json            ← metadatos parseados (no editar)
docs/test/scenarios/RFxxx-Sxx.md           ← ficha por escenario (no editar)
        ↓ import en test_gherkin_dynamic.py
tests/ers/test_gherkin_dynamic.py           ← genera 1 test por escenario dinámicamente
        ↓ llama a
tests/ers/impl/_dispatcher.py              ← lógica 3-estados
    ├── IMPLEMENTATIONS (registry.py)      → corre la función
    ├── gherkin_out_of_scope.json          → pytest.skip("[SCOPE]")
    ├── gherkin_pending.json               → pytest.skip("[PENDING]")
    └── (ninguno de los anteriores)        → pytest.fail("[MISSING]")  ← CI roto
```

### Archivos de implementación (`tests/ers/impl/`)

| Archivo | Propósito |
|---------|-----------|
| `registry.py` | Agrega todos los dicts de dominio en un único `IMPLEMENTATIONS` |
| `_dispatcher.py` | `run_gherkin_scenario()` con la lógica 3-estados |
| `__init__.py` | Re-exporta `IMPLEMENTATIONS` y `run_gherkin_scenario` |
| `auth.py` … `nonfunctional.py` | Implementaciones por dominio (un archivo por grupo RF) |

Para añadir un nuevo grupo de requisitos (e.g. RF026-RF030 de un módulo nuevo):
1. Crear `tests/ers/impl/<dominio>.py` con sus funciones y su `IMPLEMENTATIONS` local.
2. Importar y fusionar en `tests/ers/impl/registry.py`.

---

## Cómo ejecutar la suite de tests

### Suite completa

```powershell
. .venv\Scripts\Activate.ps1
pytest -q
```

### Solo escenarios ERS / Gherkin

```bash
pytest tests/ers -v
```

### Un escenario concreto

```bash
pytest tests/ers -k "RF006_S01" -v
```

### Por módulo

```bash
pytest tests/ers -k "RF005 or RF006 or RF007" -v
```

### Tests por app

```bash
pytest apps/movements/tests/ -v
```

### Tests raíz del repo

```bash
pytest tests/integration tests/scripts tests/shared -q
```

### Tests de seguridad OWASP

```bash
pytest tests/security/ -v
```

### Tests auxiliares (scripts, shared, SLA)

```bash
pytest tests/scripts tests/shared tests/test_service_sla.py -q
```

### Seed completo

```bash
pytest tests/scripts/test_seed_db.py -q
```

Este test está marcado como `slow`: en CI corre solo en `pull_request` para no penalizar los `push` frecuentes.

### Tests de integración

```bash
pytest tests/integration/ -v
```

### Con cobertura

```bash
pytest --cov=apps tests/ers
```

---

## Cómo regenerar la documentación

```bash
# Todo
python -m scripts.generate_docs

# Solo bloque Gherkin
python -m scripts.generate_docs --only gherkin

# Solo tests auxiliares (scripts, shared, SLA)
python -m scripts.generate_docs --only auxiliary

# Validar sin escribir archivos
python -m scripts.generate_docs --check

# Forzar reescritura aunque el contenido sea igual
python -m scripts.generate_docs --force
```

---

## Definition of Done (testing)

- `pytest` completo en verde; skips solo para escenarios con entrada en `gherkin_pending.json` o `gherkin_out_of_scope.json`.
- Nuevo escenario ERS → entrada en el ERS → `generate_docs` → implementación en `impl/<dominio>.py` → registrada en `IMPLEMENTATIONS` → entrada eliminada de `gherkin_pending.json` si existía.
- Nuevo RF sin implementación inmediata → entrada en `gherkin_pending.json` antes del merge.
- Contratos RF/BR nuevos reflejados en la traza `TRAZABILIDAD_ERS_GHERKIN.md`.

---

## Arquitectura de documentación auxiliar

La documentación de tests auxiliares (scripts, shared, SLA) se genera con el mismo sistema que unitarios e integración, pero organizada en subcategorías dentro de `docs/test/auxiliary/`:

```
docs/test/auxiliary/
├── index.md              ← índice global (enlaza a sub-índices)
├── scripts/
│   ├── index.md          ← índice con prefijo SCR
│   ├── SCR-0001.md
│   └── SCR-000N.md
├── shared/
│   ├── index.md          ← índice con prefijo SHA
│   ├── SHA-0001.md
│   └── SHA-000N.md
└── sla/
    ├── index.md          ← índice con prefijo SLA
    ├── SLA-0001.md
    └── SLA-000N.md

docs/test/all_auxiliary.md  ← agregado (concatena todos los .md de las 3 subcarpetas)
```

Cada subcategoría tiene su propia numeración: `SCR-*` para scripts, `SHA-*` para shared utilities, `SLA-*` para tests de Service Level Agreement.

---

## Estado actual de la suite

**~1005 tests · 685 app-level · 138 Gherkin · 45 OWASP · 114 auxiliares · 23 integración/otros** _(2026-06-22, pytest --collect-only)_

| Capa | Tests | Estado |
|------|-------|--------|
| App-level (unit/integration por app) | 685 | Cobertura medida por `--cov=apps` |
| Gherkin/ERS (RF001–RF025, RNF003–RNF006) | 138 run | 131 passed, 7 skipped (6 frontend/E2E + 1 WeasyPrint) |
| Seguridad OWASP (runtime) | **45** | A01/A02/A03/A05/A07 — job `security_tests` en CI (Postgres, bloqueante) |
| Integración cross-domain | 19 | 19 tests en 4 archivos |
| Concurrencia | 4 | Requieren `RUN_CONCURRENCY_TESTS=1` + PostgreSQL |
| Scripts / Shared / SLA | 114 | 40 security scan + 22 perf_locustfile + 21 generate_docs + 10 shared + 9 seed_db + 4 SLA + 3 project_structure + 3 shared_utils + 2 parse_ers_gherkin |
| **Total pytest collect** | **~1005** | |

**Cobertura técnica (medida 2026-06-14):** 91% exacto · 12709 statements · 11606 cubiertos · 1103 perdidos  
**Ejecución validada 2026-06-22:** ~986 passed, ~19 skipped, 0 fallos

| App | Cobertura prod | Tests |
|-----|---------------|-------|
| dashboard | 97% | 17 |
| purchasing | 93% | 103 |
| authentication | 88% | 84 |
| alerts | 87% | 61 |
| audit | 87% | 15 |
| movements | 87% | 99 |
| reports | 85% | 46 |
| catalog | 84% | 125 |
| webhooks | 83% | 25 |
| inventory | 74% | 45 |

| Capa | Archivos | Descripción |
|------|----------|-------------|
| Servicios (unit) | `apps/*/tests/test_services.py` | Lógica de negocio, edge cases, rollback |
| HTTP (views) | `apps/*/tests/test_views.py` | Endpoints reales con `APIClient` |
| Gherkin/ERS | `tests/ers/` | Escenarios RF001–RF025, RNF003–RNF006 — 131 passed, 7 skipped |
| Seguridad OWASP | `tests/security/test_owasp.py` | 45 tests A01/A02/A03/A05/A07 — ejecutados en CI con Postgres |
| Concurrencia | `tests/concurrency/` | Requiere `RUN_CONCURRENCY_TESTS=1` + Postgres (4 skipped en SQLite) |
| Performance (load) | `tests/performance/locustfile.py` | Locust 3 roles — NO parte de pytest, correr aparte |
| Scripts / Auxiliares | `tests/scripts/`, `tests/shared/`, `tests/test_service_sla.py` | 114 tests en 7 archivos |

**Nota:** Los tests de concurrencia y parte de los tests de alertas fallan en SQLite por restricciones de thread-sharing. En CI se ejecutan contra PostgreSQL real con `RUN_CONCURRENCY_TESTS=1`. Los tests de seguridad OWASP se ejecutan con `pytest tests/security/` y necesitan Postgres para máxima fidelidad (el job `security_tests` de CI lo garantiza).

Para el historial completo de cambios ver [`CHANGELOG_TESTING.md`](CHANGELOG_TESTING.md).

---

## Cómo verificar cobertura

```powershell
# Cobertura con reporte HTML (abre htmlcov/index.html)
pytest --cov=apps --cov-report=html --cov-report=term-missing -q
```

---

## Tests de seguridad OWASP

La suite `tests/security/` verifica controles de seguridad en tiempo de ejecución (complementan el SAST estático de semgrep/bandit):

```bash
# Ejecutar todos los tests de seguridad
pytest tests/security/ -v

# Con cobertura
pytest tests/security/ -v --cov=apps --cov-report=term-missing
```

| Categoría OWASP | Tests | Qué verifica |
|----------------|-------|--------------|
| A01 — Broken Access Control | 14 | 401 sin token, IDOR por UUID, RBAC por rol (auxiliar→403, admin→403 en escrituras) |
| A02 — Cryptographic Failures | 4 | `password` ausente en respuestas; claim `exp` en JWT |
| A03 — Injection | 13 | SQL payloads × 3 vectores → nunca 500; XSS en búsqueda → JSON sin `<script>` |
| A05 — Security Misconfiguration | 5 | 404 para rutas desconocidas; errores con Content-Type JSON; health público |
| A07 — Auth Failures | 9 | Contraseña incorrecta, JWT alterado, refresh como access, usuario inactivo → 401 |

En CI estos tests se ejecutan en el job `security_tests` (Postgres 18, paralelo a `concurrency_tests`, bloqueante para el merge).

---

## Load testing con Locust (opcional)

Locust simula usuarios concurrentes contra un servidor vivo. **No reemplaza pytest** — úsalo antes de releases o para detectar regresiones N+1 bajo carga.

El locustfile modela **tres roles** con pesos proporcionales a la carga real del sistema:

| User class | Rol | `weight` | Tareas | Tipo de acceso |
|-----------|-----|---------|--------|----------------|
| `ICMUser` | almacenista | 5 | 28 (21 lectura + 7 escritura) | Lectura completa + todos los tipos de movimiento |
| `AuxiliarUser` | auxiliar_despacho | 3 | 8 | Solo lectura (inventory, movements, alerts) |
| `AdminUser` | administrador | 2 | 6 | Solo lectura (KPI, reports, audit, billing/stats) |

```bash
# Instalar (solo para performance, no va en requirements.txt principal)
pip install -r requirements-perf.txt

# Correr (requiere servidor en localhost:8000) — 12 usuarios, 3 roles
locust -f tests/performance/locustfile.py \
       --headless -H http://localhost:8000 \
       -u 12 -r 3 --run-time 45s --only-summary

# Health check básico (locustfile de scripts/)
locust -f scripts/perf/locustfile.py \
       --headless -H http://localhost:8000 \
       -u 5 -r 1 --run-time 20s --only-summary
```

En CI, el job `load_test` crea los tres usuarios (`almacenista`, `auxiliar`, `administrador`) con `get_or_create` y un `TemporaryAccessPermit` para el auxiliar (ventana horaria) antes de lanzar Locust.

---

## Notas sobre entorno de pruebas

- `config.settings.test` usa **SQLite in-memory** — la semántica de PostgreSQL no se reproduce (transacciones advisory, `SELECT FOR UPDATE`, etc.).
- `DEFAULT_THROTTLE_CLASSES` está desactivado en test.
- Tests de concurrencia real: `tests/concurrency/` requiere Postgres y `RUN_CONCURRENCY_TESTS=1`.
- Tests E2E UI: `tests/e2e/` — ver `docs/test/FRONTEND_E2E_PLAN.md` para plan de handoff a frontend.
- `tests/performance/` está excluido de la recolección de pytest (`norecursedirs` en `pytest.ini`) para evitar errores de importación de `locust`.
