# Scripts del repositorio

Esta carpeta agrupa automatizaciones reutilizables para documentacion, trazabilidad y mantenimiento del proyecto.

## Proposito

Los scripts aqui reunidos se usan para:

- sincronizar la documentacion arquitectonica con la estructura real del proyecto,
- regenerar la documentacion de tests,
- convertir escenarios ERS/Gherkin en artefactos trazables,
- concatenar salidas generadas para lectura rapida,
- mantener helpers compartidos para los generadores.

## Scripts principales

### `generate_project_structure.py`

Analiza la estructura actual del proyecto Django y actualiza el bloque de arquitectura en `docs/README_ARQUITECTURA.md`.

Se usa cuando cambia la organizacion de carpetas, aparecen nuevas apps, se agregan docs relevantes o se quiere refrescar el arbol documentado.

### `parse_ers_gherkin.py`

Lee `docs/requisitos/ERS_ICM_Requisitos.md`, extrae los escenarios Gherkin y genera:

- `docs/test/gherkin_scenarios.json`
- `docs/test/scenarios/*.md`

Sirve para mantener sincronizada la trazabilidad entre requisitos y escenarios automatizados.

### `generate_all_test_docs.py`

Orquesta la regeneracion completa de la documentacion de tests.

Ejecuta los generadores de escenarios Gherkin, tests unitarios y tests de integracion en una sola pasada.

### `concat_md.ps1`

Concatena los archivos Markdown generados en salidas agregadas como `docs/test/all_unit.md`, `docs/test/all_integration.md` y `docs/test/all_scenarios.md`.

Se usa para tener una vista compacta de toda la documentacion generada sin abrir archivo por archivo.

## Subcarpeta `generate_docs/`

Esta subcarpeta contiene wrappers y utilidades comunes para la generacion de documentacion de pruebas.

### `generate_docs/menu.py`

Menú interactivo para regenerar la documentacion de tests por tipo: unit, integration, gherkin o todo.

### `generate_docs/generate_unit_test_docs.py`

Genera la documentacion de tests unitarios dentro de `docs/test/unit/`.

### `generate_docs/generate_integration_test_docs.py`

Genera la documentacion de tests de integracion dentro de `docs/test/integration/`.

### `generate_docs/generate_gherkin_test_docs.py`

Wrapper que invoca `parse_ers_gherkin.py` para regenerar la documentacion de escenarios Gherkin.

### `generate_docs/utils.py`

Contiene utilidades compartidas para leer tests, clasificar nodos, asignar codigos y escribir Markdown consistente.

## Como usarlo

Ejemplos comunes:

```bash
python scripts/generate_project_structure.py
python scripts/parse_ers_gherkin.py
python scripts/generate_all_test_docs.py
python scripts/generate_docs/menu.py
```

## Criterio de mantenimiento

Si agregas un script nuevo en esta carpeta, documentalo aqui y revisa si debe aparecer tambien en el generador de estructura del proyecto para mantener la documentacion sincronizada.