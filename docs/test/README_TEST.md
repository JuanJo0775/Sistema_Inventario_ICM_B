# Documentación de pruebas — Sistema Inventario ICM

## Fuentes de verdad

1. **`docs/requisitos/ERS_ICM_Requisitos.md`** — RF/RNF y criterios **Gherkin** (Given / When / Then).
2. **`docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md`** — contexto de negocio ICM.
3. **`docs/README_ARQUITECTURA.md`**, **`docs/api/README_API.md`**.

## Estructura de documentación por test

| Ubicación | Contenido |
|-----------|------------|
| `docs/test/scenarios/` | **Un archivo `.md` por cada escenario Gherkin del ERS** (95 archivos) + `index.md` al inicio de la carpeta. Los archivos se generan por código de escenario, por ejemplo `RF001-S01.md`. |
| `docs/test/unit/` | **Un archivo `.md` por cada test** fuera de la suite Gherkin dinámica (p. ej. `apps/*/tests/*.py`, `tests/test_api_integration.py`) + `index.md` al inicio. Los archivos se generan por código, por ejemplo `UNIT-0001.md`. |
| `docs/test/integration/` | **Un archivo `.md` por cada test de integración** + `index.md` al inicio. Los archivos se generan por código, por ejemplo `INT-0001.md`. |
| `docs/test/gherkin_scenarios.json` | Metadatos parseados del ERS (título, cuerpo Gherkin por escenario). |
| `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` | Matriz resumida RF ↔ tests (referencia viva). |

## Cómo se genera la documentación

La documentación de pruebas se construye desde los tests reales del repositorio y se organiza en tres bloques:

1. **Gherkin/ERS**: escenarios derivados de `docs/requisitos/ERS_ICM_Requisitos.md`.
2. **Unitarios**: tests bajo `apps/*/tests/` y otros tests no clasificados como integración.
3. **Integración**: tests HTTP/API y otros casos marcados como integración por convención.

Cada bloque genera:

- Un archivo `index.md` dentro de su carpeta.
- Un archivo `.md` por cada test o escenario.
- Un archivo agregado `docs/test/all_*.md` cuando se ejecuta la concatenación.

### Opción oficial: CLI única

El punto de entrada recomendado es el módulo canónico de Python:

```bash
python -m scripts.generate_docs
```

Ese comando regenera los tres bloques y deja actualizados:

- `docs/test/unit/`
- `docs/test/integration/`
- `docs/test/scenarios/`
- `docs/test/all_unit.md`
- `docs/test/all_integration.md`

- `docs/test/all_scenarios.md`

También puedes ejecutar un bloque específico:

```bash
python -m scripts.generate_docs --only unit
python -m scripts.generate_docs --only integration
python -m scripts.generate_docs --only gherkin
```

Si quieres validar sin escribir archivos, usa `--check`:

```bash
python -m scripts.generate_docs --check
```

Si necesitas forzar reescritura aunque el contenido sea igual, usa `--force`:

```bash
python -m scripts.generate_docs --force
```

### Qué valida la generación

- El índice queda dentro de cada carpeta de destino.
- Los archivos individuales se nombran por código: `UNIT-0001.md`, `INT-0001.md`, `RF001-S01.md`.
- La carpeta queda limpia antes de regenerar para evitar mezclar archivos viejos con los nuevos.

## Suite Gherkin (1 test = 1 escenario ERS)

- **Código:** `tests/ers/test_gherkin_dynamic.py` genera **95** funciones `test_RFxxx_Sxx` / `test_RNFxxx_Sxx`.
- **Implementación:** `tests/ers/gherkin_impl.py` — diccionario `IMPLEMENTATIONS` enlaza escenario → función Python. Si un escenario no está en el diccionario, el test hace **`pytest.skip`** con motivo (UI pura, exportación Excel, concurrencia multi-hilo, aprobación de devoluciones no modelada, etc.).
- **Escenarios fuera de alcance backend:** la lista persistente vive en `docs/test/gherkin_out_of_scope.json`. El generador la incorpora en `docs/test/scenarios/*.md`, `docs/test/gherkin_scenarios.json` y `docs/test/scenarios/index.md`, de modo que el estado sobreviva a cualquier regeneración.
- **Regenerar escenarios y MD** tras cambios en el ERS:

```bash
python scripts/parse_ers_gherkin.py
```

- **Sincronizar lista de escenarios implementados:** editar `_IMPL_IDS` en `scripts/parse_ers_gherkin.py` y el dict `IMPLEMENTATIONS` en `tests/ers/gherkin_impl.py` (deben coincidir).

## Tests unitarios / integración (no Gherkin dinámico)

Para regenerar toda la documentación de tests, usa el comando oficial:

```bash
python -m scripts.generate_docs
```

Si quieres hacerlo por partes:

```bash
python -m scripts.generate_docs --only unit
python -m scripts.generate_docs --only integration
python -m scripts.generate_docs --only gherkin
```

## Cómo ejecutar la suite de tests

### Suite completa

En Windows, usa una de estas dos formas. La primera es la recomendada porque deja claro que se está usando el entorno del proyecto.

1. Activar el entorno virtual y ejecutar la suite:

```powershell
. .venv\Scripts\Activate.ps1
pytest -q
```

2. Ejecutar directamente con el Python del entorno virtual, sin activarlo:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
```

Si quieres ver más detalle por test, cambia `-q` por `-v` en cualquiera de las dos opciones.

`pytest -q` muestra salida concisa y es la opción recomendada para uso diario y CI.
`pytest -v` muestra salida detallada y sirve mejor para depurar.

Este comando ejecuta toda la suite del proyecto: unitarios, integración y Gherkin.

Nota de fidelidad del entorno de pruebas:

- `config.settings.test` usa SQLite in-memory.
- `config.settings.test` desactiva `DEFAULT_THROTTLE_CLASSES`.
- La suite valida contratos y reglas de dominio, pero no reproduce la semantica exacta de PostgreSQL ni el throttling de produccion.

### Sólo escenarios ERS / Gherkin

```bash
pytest tests/ers/test_gherkin_dynamic.py -v
```

### Un escenario ERS concreto

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S01 -v
```

### Filtrar por requisito o prefijo

```bash
pytest tests/ers/test_gherkin_dynamic.py -k "RF001" -v
```

### Tests por app

```bash
pytest apps/movements/tests/ -v
```

### Tests de integración

```bash
pytest tests/integration/ -v
```

### Tests unitarios de una app concreta

```bash
pytest apps/catalog/tests/ -v
```

### Si necesitas cobertura

```bash
pytest --cov=apps
```

## Definition of Done (testing)

- `pytest` completo en verde; skips solo en escenarios Gherkin **explícitamente pendientes** de backend.
- Nuevas automatizaciones Gherkin: añadir función en `gherkin_impl.py`, registrar en `IMPLEMENTATIONS`, actualizar `_IMPL_IDS` en `parse_ers_gherkin.py` y regenerar MD.
- Contratos RF/BR nuevos reflejados en docstrings y, si aplica, en `TRAZABILIDAD_ERS_GHERKIN.md`.

## Mantenimiento

- Añadir implementación: función en `tests/ers/gherkin_impl.py` + clave en `IMPLEMENTATIONS` + id en `_IMPL_IDS` en `scripts/parse_ers_gherkin.py`
  → `python scripts/parse_ers_gherkin.py`

- Regenerar docs de tests:
  `python -m scripts.generate_docs`

## Nuevas suites añadidas (concurrency / e2e)

Se han añadido nuevas áreas de prueba previstas en el plan de cierre de brechas:

- `tests/concurrency/`: pruebas de concurrencia/consistencia pensadas para ejecutarse contra PostgreSQL real (no SQLite). Estas pruebas están deshabilitadas por defecto y requieren una DB Postgres accesible y la variable de entorno `RUN_CONCURRENCY_TESTS=1` para ejecutarse.

- `tests/e2e/`: carpeta objetivo para tests E2E UI (Playwright/Cypress). El repositorio incluye un plan de handoff para frontend en `docs/test/FRONTEND_E2E_PLAN.md` con escenarios, payloads y criterios de aceptación que el equipo frontend puede implementar.

Nota: el generador de documentación ahora clasifica `tests/concurrency/` como parte de la familia `integration`. Al regenerar la documentación de integración (`python -m scripts.generate_docs --only integration`) se crearán las páginas markdown correspondientes dentro de `docs/test/integration/` y se añadirán al agregador `docs/test/all_integration.md`.

Comandos recomendados para ejecutar las nuevas suites (localmente con Postgres):

```powershell
# Run concurrency tests (requires Postgres and RUN_CONCURRENCY_TESTS=1)
$env:RUN_CONCURRENCY_TESTS = "1"
& .\.venv\Scripts\python.exe -m pytest tests/concurrency -q

# Run E2E tests (example for Playwright runner)
pwsh -c "npx playwright test tests/e2e --project=chromium"
```

Notas:
- Las pruebas de concurrencia deben correr en un entorno que reproduzca la semántica de PostgreSQL; la configuración por defecto de `config.settings.test` usa SQLite en memoria.
- Añadir estas pruebas al pipeline de CI requiere exponer un servicio `postgres` en el job y establecer la variable `RUN_CONCURRENCY_TESTS=1`.