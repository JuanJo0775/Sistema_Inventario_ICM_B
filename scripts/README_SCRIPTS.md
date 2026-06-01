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

4) import_catalog (management command)

- Propósito: importa el catálogo inicial de productos desde el Excel de ICM (`Clasificacion_Productos.xlsx`) de forma idempotente. Los productos ya existentes se omiten. Las categorías se crean si no existen.
- Soporte de precios: si el Excel contiene columnas de precio a partir de la columna D, el comando las lee y las carga en el producto. Si no existen, los precios quedan en null y el comando sigue funcionando sin error.
  - Columnas reconocidas: `Precio Venta`, `Precio Menor`, `Precio Minorista` → `sale_price_retail`; `Precio Mayorista`, `Precio Mayor` → `sale_price_wholesale`; `Costo`, `Costo Unitario` → `unit_cost`; `IVA`, `IVA%` → `tax_rate_pct`; `Moneda` → `currency`.
- Dependencia: requiere que el usuario almacenista exista primero (`python manage.py create_almacenista`).
- Uso:

```bash
# Importación real
python manage.py import_catalog

# Dry-run (valida sin escribir en BD)
python manage.py import_catalog --dry-run

# Ruta personalizada al Excel
python manage.py import_catalog --excel-path /ruta/al/archivo.xlsx

# Usuario actor distinto al del .env
python manage.py import_catalog --actor-username otro_almacenista
```

5) create_almacenista (management command)

- Propósito: crea el usuario almacenista inicial del sistema con las credenciales definidas en las variables de entorno `ALMACENISTA_USERNAME`, `ALMACENISTA_EMAIL`, `ALMACENISTA_PASSWORD` del archivo `.env`. Es idempotente: si el usuario ya existe, no hace nada.
- Dependencia: requiere que `ALMACENISTA_PASSWORD` esté configurada en `.env` (no puede estar vacía).
- Uso:

```bash
python manage.py create_almacenista
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