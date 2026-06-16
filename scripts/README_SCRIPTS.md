# Scripts del repositorio

Este archivo documenta los scripts y utilidades incluidos en la carpeta `scripts/`, su propósito, uso habitual y las convenciones para añadir nuevos scripts.

## Objetivo

Agrupar y explicar las automatizaciones reutilizables que facilitan:

- Sincronizar la documentación arquitectónica con la estructura real del proyecto.
- Regenerar la documentación de tests y mantener trazabilidad ERS ↔ Gherkin.
- Generar reportes compactos sobre la estructura del proyecto.
- Ejecutar escaneos integrales de calidad y seguridad (ruff, semgrep, bandit, pip-audit, mypy).
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

4) seed_db (script independiente — seed unificado)

- Ubicación: `scripts/seed_db/` — completamente independiente de las apps Django.
  - `config.py`: todos los datos estáticos basados en `Clasificacion_Productos.xlsx` — 11 categorías, 26 marcas/subcategorías, 214 productos con precios completos, 3 combos, 5 proveedores, 5 clientes, ubicaciones adicionales.
  - `seeder.py`: clase `Seeder` con 14 fases ordenadas — desde catálogo hasta movimientos.
  - `run.py`: punto de entrada ejecutable directamente con Python.
  - `env.py`: credenciales del usuario inicial leídas desde `.env`.
- Guía de uso detallada: [`docs/guias/SEED_DB.md`](../docs/guias/SEED_DB.md)
- **Fuente de verdad**: todos los productos y categorías provienen de `Clasificacion_Productos.xlsx`. No depende del Excel en tiempo de ejecución — los datos están embebidos en `config.py`.
- Prerequisito único: `python manage.py create_almacenista`.
- Fases del seed:
  1. Usuarios adicionales (2 auxiliares_despacho, 1 administrador)
  2. Ubicaciones (Bodega Norte, Vitrina 2 adicionales)
  3. Categorías (11 categorías con atributos correctos)
  4. Subcategorías / Marcas (33 marcas distribuidas por categoría)
  5. Productos (214 productos con precios, reorder_point, marca, IVA)
  6. Proveedores (5 proveedores)
  7–8. Stock via flujo OC completo (bodega principal + bodega norte)
  9. Traslados internos a vitrina y vitrina-2
  10. Ventas al por menor (vaciado parcial vitrina)
  11. Ventas al por mayor con datos completos de cliente (BR-08, RNF-006)
  12. Ajustes positivos y negativos con justificación (BR-07)
  13. Escenario de agotamiento en vitrina
  14. Combos de productos (KIT-1, KBND-1, KPIT-1)
- **Idempotente**: fases 1–6 (catálogo) siempre corren y hacen get-or-create. Fases 7–14 (movimientos) se omiten si ya existen; usa `--force` para regenerar.
- Respeta BR-04 (serial obligatorio en electroterapia si aplica), BR-07 (justificación en ajustes), BR-11 (no stock negativo), BR-14 (estado de ubicaciones).
- Uso:

```bash
# Primera vez (solo necesita create_almacenista primero)
python manage.py create_almacenista
python scripts/seed_db/run.py

# Regenerar movimientos completos
python scripts/seed_db/run.py --force
```

- Salida: resumen con conteo de categorías, marcas, productos, OC, movimientos por tipo, stock por ubicación y escenarios disponibles.

5) run_security_scan.py (calidad y seguridad integral)

- Propósito: ejecuta de forma secuencial las herramientas de calidad del proyecto: **ruff** (lint + format), **semgrep** (SAST), **bandit** (SAST), **pip-audit** (supply-chain) y **mypy** (tipado estático). Genera un reporte consolidado en `scripts/security/reports/`.
- Requisito: tener instaladas las herramientas (`pip install -r requirements/base.txt`).
- Soporta selección granular con `--only`, `--skip`, `--ci`, `--list` y `--dry-run`.
- Uso:

```bash
python scripts/security/run_security_scan.py                  # todas las herramientas
python scripts/security/run_security_scan.py --only ruff      # solo ruff (lint + format)
python scripts/security/run_security_scan.py --only semgrep   # solo semgrep
python scripts/security/run_security_scan.py --skip mypy      # todas menos mypy
python scripts/security/run_security_scan.py --list           # listar herramientas disponibles
python scripts/security/run_security_scan.py --ci             # modo CI (compacto)
python scripts/security/run_security_scan.py --dry-run        # modo simulación
```

6) create_almacenista (management command)

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
git commit -m "docs: actualizar arquitectura desde scripts/project_structure/generate_project_structure"
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
