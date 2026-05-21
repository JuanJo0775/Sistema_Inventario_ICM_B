# Documentación de pruebas — Sistema Inventario ICM

## Fuentes de verdad

1. **`docs/ERS_ICM_Requisitos.md`** — RF/RNF y criterios **Gherkin** (Given / When / Then).
2. **`docs/ICM_Informe_Elicitacion_v2_plus.docx.md`** — contexto de negocio ICM.
3. **`docs/README_ARQUITECTURA.md`**, **`docs/README_API.md`**.

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

1. **Gherkin/ERS**: escenarios derivados de `docs/ERS_ICM_Requisitos.md`.
2. **Unitarios**: tests bajo `apps/*/tests/` y otros tests no clasificados como integración.
3. **Integración**: tests HTTP/API y otros casos marcados como integración por convención.

Cada bloque genera:

- Un archivo `index.md` dentro de su carpeta.
- Un archivo `.md` por cada test o escenario.
- Un archivo agregado `docs/test/all_*.md` cuando se ejecuta la concatenación.

### Opción recomendada: menú interactivo

El menú vive en `scripts/generate_docs/menu.py` y permite regenerar docs sin recordar scripts individuales.

```bash
python scripts/generate_docs/menu.py
```

Al abrirse verás estas opciones:

1. **Unitarias**: regenera `docs/test/unit/`.
2. **Integración**: regenera `docs/test/integration/`.
3. **Escenarios (Gherkin)**: regenera `docs/test/scenarios/`.
4. **Todo**: ejecuta unitarios + integración + Gherkin y después concatena los archivos agregados.
5. **Salir**: cierra el menú.

### Opción por línea de comandos

Si prefieres ejecutar directamente sin menú interactivo, puedes usar:

```bash
python scripts/generate_docs/menu.py --type all
```

Ese comando hace lo mismo que elegir la opción 4 del menú: regenera los tres bloques y deja actualizados:

- `docs/test/unit/`
- `docs/test/integration/`
- `docs/test/scenarios/`
- `docs/test/all_unit.md`
- `docs/test/all_integration.md`
- `docs/test/all_scenarios.md`

También puedes ejecutar un bloque específico:

```bash
python scripts/generate_docs/menu.py --type unit
python scripts/generate_docs/menu.py --type integration
python scripts/generate_docs/menu.py --type gherkin
```

Si quieres regenerar sólo las carpetas, pero sin concatenar los archivos `all_*.md`, usa `--no-concat`:

```bash
python scripts/generate_docs/menu.py --type all --no-concat
```

### Scripts individuales

Si necesitas ejecutar los generadores por separado, estos son los comandos reales del repositorio:

```bash
python scripts/parse_ers_gherkin.py
python scripts/generate_docs/generate_unit_test_docs.py
python scripts/generate_docs/generate_integration_test_docs.py
```

- El primero genera los escenarios Gherkin y su `index.md`.
- El segundo genera la documentación de unitarios.
- El tercero genera la documentación de integración.

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

Para regenerar toda la documentación de tests, usa el menú o el orquestador principal:

```bash
python scripts/generate_all_test_docs.py
```

O usa directamente el menú interactivo:

```bash
python scripts/generate_docs/menu.py
```

Si quieres hacerlo por partes, ejecuta los scripts individuales:

```bash
python scripts/parse_ers_gherkin.py
python scripts/generate_docs/generate_unit_test_docs.py
python scripts/generate_docs/generate_integration_test_docs.py
```

## Cómo ejecutar la suite de tests

### Suite completa

```bash
pytest -q
```
```bash
pytest -v
```

pytest -q : salida concisa (recomendado en docs/CI).
pytest -v : salida detallada por test (útil para depurar y reportar).

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

- Regenerar docs de tests unitarios e integración:  
  `python scripts/generate_docs/generate_unit_test_docs.py`  
  `python scripts/generate_docs/generate_integration_test_docs.py`