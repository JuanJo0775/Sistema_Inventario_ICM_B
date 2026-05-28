# Scripts del repositorio

Este archivo documenta los scripts y utilidades incluidos en la carpeta `scripts/`, su propósito, uso habitual y las convenciones para añadir nuevos scripts.

## Objetivo

Agrupar y explicar las automatizaciones reutilizables que facilitan:

- Sincronizar la documentación arquitectónica con la estructura real del proyecto.
- Regenerar la documentación de tests y mantener trazabilidad ERS ↔ Gherkin.
- Generar reportes compactos sobre la estructura del proyecto.
- Proporcionar helpers y pipelines idempotentes para generación de artefactos.

## Requisitos previos

Antes de ejecutar los scripts se recomienda activar el entorno virtual del proyecto y usar las mismas variables de entorno que el proyecto.

Ejemplo (PowerShell):

```powershell
. .venv/Scripts/Activate.ps1
#$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'  # opcional según script
```

## Scripts principales

1) project_structure/generate_project_structure.py

- Propósito: analiza la estructura del proyecto Django (apps, servicios, selectores, urls, comandos, settings, docs relevantes) y actualiza el bloque de arquitectura en `docs/README_ARQUITECTURA.md`. También escribe un reporte compacto en `scripts/project_structure/project_structure_report.md` con altas, bajas y reorganizaciones detectadas.
- Comportamiento clave:
	- Prioriza artefactos de código y documentación relevantes para la arquitectura.
	- Excluye `__pycache__`, migraciones triviales y artefactos temporales por defecto.
	- Permite overrides por archivo JSON para inclusiones/exclusiones y comentarios manuales.
	- Mantiene salida estable para evitar diffs innecesarios.
- Uso:

```bash
python scripts/project_structure/generate_project_structure.py
python scripts/project_structure/generate_project_structure.py --dry-run
python scripts/project_structure/generate_project_structure.py --config architecture-overrides.json
```

2) parse_ers_gherkin.py

- Propósito: extrae escenarios Gherkin desde `docs/requisitos/ERS_ICM_Requisitos.md` y genera artefactos trazables para pruebas.
- Salidas comunes:
	- `docs/test/gherkin_scenarios.json`
	- `docs/test/scenarios/*.md`
- Uso:

```bash
python scripts/parse_ers_gherkin.py
```

3) generate_docs (paquete)

- Contenido: `scripts/generate_docs/__main__.py` (entrypoint) y utilidades en `scripts/generate_docs/utils.py`.
- Propósito: pipeline idempotente para descubrir, renderizar y escribir documentación relacionada con tests y escenarios.
- Uso recomendado:

```bash
python -m scripts.generate_docs
python -m scripts.generate_docs --only unit
python -m scripts.generate_docs --check
```

## Convenciones y buenas prácticas

- Documenta cada script nuevo en este `README_SCRIPTS.md` con: propósito, entradas, salidas, opciones CLI y ejemplos de uso.
- Evita efectos secundarios inesperados: los scripts deben ofrecer `--dry-run` cuando modifiquen archivos en el repo.
- Mantén la salida estable: cuando sea posible, ordena listas y normaliza rutas para reducir diffs.
- Usa un archivo de configuración (JSON/YAML) cuando el comportamiento necesite personalización por proyecto.

## Añadir un nuevo script

1. Crear el script en `scripts/` o en un subdirectorio claro (`scripts/project_structure`, `scripts/generate_docs`, etc.).
2. Añadir documentación mínima en este `README_SCRIPTS.md` (propósito, uso, ejemplos).
3. Añadir opciones `--help`/`--dry-run` en el script.
4. Si aplica al generador de estructura, actualizar `architecture-overrides.json` de ejemplo y documentarlo.

## Ejemplos prácticos

- Regenerar la arquitectura y revisar cambios:

```bash
python scripts/project_structure/generate_project_structure.py --dry-run
python scripts/project_structure/generate_project_structure.py
git add docs/README_ARQUITECTURA.md scripts/project_structure/project_structure_report.md
git commit -m "docs: actualizar arquitectura desde scripts/generate_project_structure"
```

- Extraer escenarios Gherkin y revisar artefactos:

```bash
python scripts/parse_ers_gherkin.py
ls docs/test/scenarios/
```

## Mantenimiento

- Cuando agregues o retires scripts, actualiza este README y —si procede— el generador de estructura para evitar que se pierdan referencias.
- Para cambios que impacten contratos de documentación o trazabilidad, añade tests o una nota en `docs/test/README_TEST.md`.

## Contacto y contribuciones

Si no estás seguro sobre dónde ubicar un script nuevo o cómo documentarlo, abre un issue o PR en el repositorio y referencia este README.

---

Si quieres, puedo ejecutar una corrección ortográfica o aplicar formato adicional al archivo; dime si lo hago ahora.