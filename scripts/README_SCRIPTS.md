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

## Subcarpeta `generate_docs/`

Esta subcarpeta contiene el entrypoint canónico de generación.

### `generate_docs/__main__.py`

Punto de entrada oficial para la generación de documentación de tests.

Uso recomendado:

```bash
python -m scripts.generate_docs
```

### `generate_docs/utils.py`

Contiene el pipeline común de descubrimiento, renderizado, escritura idempotente y concatenación.

## Como usarlo

Ejemplos comunes:

```bash
python scripts/generate_project_structure.py
python -m scripts.generate_docs
python -m scripts.generate_docs --only unit
python -m scripts.generate_docs --check
```

## Criterio de mantenimiento

Si agregas un script nuevo en esta carpeta, documentalo aqui y revisa si debe aparecer tambien en el generador de estructura del proyecto para mantener la documentacion sincronizada.