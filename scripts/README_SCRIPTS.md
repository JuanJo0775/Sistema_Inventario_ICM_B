# Scripts del Repositorio — Guía Completa

Documentación de todas las automatizaciones del proyecto **Sistema Inventario ICM**. Cada subcarpeta en `scripts/` es un paquete Python independiente con un propósito único. Esta guía cubre qué hace cada script, cómo usarlo y cuándo ejecutarlo.

---

## Tabla de contenidos

1. [Estructura del directorio](#1-estructura-del-directorio)
2. [Guía rápida — qué ejecutar según la tarea](#2-guía-rápida--qué-ejecutar-según-la-tarea)
3. [Pipeline CI local (`ci_local/`)](#3-pipeline-ci-local-ci_local)
4. [Seed unificado de base de datos (`seed_db/`)](#4-seed-unificado-de-base-de-datos-seed_db)
5. [Generación de documentación de tests (`generate_docs/`)](#5-generación-de-documentación-de-tests-generate_docs)
6. [Escaneo de calidad y seguridad (`security/`)](#6-escaneo-de-calidad-y-seguridad-security)
7. [Árbol de arquitectura (`project_structure/`)](#7-árbol-de-arquitectura-project_structure)
8. [Verificación de base de datos Neon (`db_neo/`)](#8-verificación-de-base-de-datos-neon-db_neo)
9. [Pruebas de carga Locust (`perf/`)](#9-pruebas-de-carga-locust-perf)
10. [Alias legacy (`docs/`)](#10-alias-legacy-docs)
11. [Checklist antes de `git push`](#11-checklist-antes-de-git-push)
12. [Convenciones para nuevos scripts](#12-convenciones-para-nuevos-scripts)
13. [Solución de problemas](#13-solución-de-problemas)

---

## 1. Estructura del directorio

```
scripts/
│
├── __init__.py                          # Hace de scripts/ un paquete Python importable
├── README_SCRIPTS.md                    # Este archivo
│
├── ci_local/                            # ── Pipeline CI local con Docker ──
│   ├── __init__.py
│   └── ci_local.py                      # Orquestador principal (732 líneas)
│
├── seed_db/                             # ── Seed unificado de base de datos ──
│   ├── __init__.py
│   ├── run.py                           # Entry point CLI con argparse
│   ├── seeder.py                        # Lógica core del seed (24 fases)
│   ├── config.py                        # Datos estáticos del seed (214 productos)
│   ├── env.py                           # Carga de variables de entorno
│   └── clean.py                         # Limpieza segura de datos del seed
│
├── generate_docs/                       # ── Generación de documentación de tests ──
│   ├── __init__.py                      # Exporta main()
│   ├── __main__.py                      # Habilita `python -m scripts.generate_docs`
│   └── utils.py                         # Lógica de descubrimiento, clasificación y renderizado
│
├── security/                            # ── Escaneo de calidad y seguridad ──
│   ├── run_security_scan.py             # Orquestador de herramientas de calidad
│   └── reports/                         # Reportes generados (texto plano)
│
├── project_structure/                   # ── Generador de árbol de arquitectura ──
│   ├── __init__.py
│   ├── generate_project_structure.py    # Analiza repo y actualiza árbol en docs/
│   └── project_structure_report.md      # Reporte de delta (altas/bajas)
│
├── db_neo/                              # ── Verificación Neon ──
│   ├── __init__.py
│   └── _verify_neon.py                  # Health-check de conexión y seed en Neon
│
├── perf/                                # ── Pruebas de carga ──
│   └── locustfile.py                    # Definición de usuarios Locust
│
└── docs/                                # ── Alias legacy ──
    ├── __init__.py
    └── parse_ers_gherkin.py             # Wrapper delgado → generate_docs
```

---

## 2. Guía rápida — qué ejecutar según la tarea

| Si estás haciendo… | Ejecuta | Notas |
|---------------------|---------|-------|
| Clonaste el repo y necesitas datos | `python scripts/seed_db/run.py` | Requiere `create_almacenista` antes |
| Modificaste tests o Gherkin | `python -m scripts.generate_docs` | Obligatorio antes de `git push` |
| Cambiaste estructura del proyecto | `python scripts/project_structure/generate_project_structure.py` | Actualiza `docs/README_ARQUITECTURA.md` |
| Quieres verificar calidad/seguridad | `python scripts/security/run_security_scan.py` | Genera reporte en `reports/` |
| Vas a abrir un PR | `python scripts/ci_local/ci_local.py --no-load` | Replica el pipeline de CI completo |
| Verificar base de datos Neon | `python scripts/db_neo/_verify_neon.py` | Requiere `DATABASE_URL` configurado |
| Probar rendimiento de endpoints | `locust -f scripts/perf/locustfile.py --host http://localhost:8000` | Requiere Django corriendo |

---

## 3. Pipeline CI local (`ci_local/`)

### ¿Qué hace?

Replica el workflow de GitHub Actions (`.github/workflows/ci.yml`) en tu máquina con un solo comando. Utiliza Docker para levantar un contenedor PostgreSQL 18 temporal en el puerto **15432** (evita colisión con el Postgres de desarrollo en 5432), ejecuta los 8 stages en secuencia y genera un reporte consolidado al final.

### Cuándo usarlo

- **Antes de abrir un PR** para verificar que todo el pipeline pasa localmente.
- **Para reproducir fallos de CI** sin esperar la cola de GitHub Actions.
- **Para correr solo un subconjunto de stages** (por ejemplo, solo quality + unit tests).

### Requisitos

- Docker Desktop corriendo.
- Entorno virtual activo con `requirements/development.txt` instalado.

### Argumentos

| Argumento | Tipo | Descripción |
|-----------|------|-------------|
| `--no-load` | flag | Omite el stage `load_test` (Locust). Más rápido. |
| `--from STAGE` | choice | Inicia el pipeline desde el stage indicado. |
| `--only STAGE [STAGE ...]` | choice+ | Ejecuta **solo** los stages especificados. |
| `--skip STAGE [STAGE ...]` | choice+ | Omite los stages especificados. |
| `--keep-container` | flag | No elimina el contenedor Postgres al terminar (acelera re-runs). |
| `--no-color` | flag | Deshabilita colores ANSI (útil para redirigir a archivo). |

### Stages disponibles (en orden)

| # | Stage | Qué ejecuta | Usa Postgres |
|---|-------|-------------|:---:|
| 1 | `quality` | lint (ruff), format, SAST (semgrep/bandit), mypy, pip-audit, docs check | No |
| 2 | `unit_tests` | `pytest apps/ shared/ tests/unit/` con SQLite :memory: | No |
| 3 | `integration_tests` | `pytest tests/integration/ tests/scripts/ tests/test_service_sla.py` | No |
| 4 | `scenarios` | `pytest tests/ers/` — escenarios Gherkin | Sí |
| 5 | `seed_db` | `pytest tests/scripts/test_seed_db.py` con Postgres | Sí |
| 6 | `security_tests` | `pytest tests/security/` — OWASP Top 10 | Sí |
| 7 | `concurrency_tests` | `pytest tests/concurrency/` — SELECT FOR UPDATE, stock | Sí |
| 8 | `load_test` | Locust 12 usuarios / 3 spawns por segundo / 45 segundos | Sí |

### Nota sobre `runserver` y `--settings`

`manage.py runserver` **siempre** fuerza `config.settings.development` (PostgreSQL local), ignorando `DJANGO_SETTINGS_MODULE` del entorno. Esto evita que un entorno residual de pytest deje SQLite como DB por accidente.

El stage `load_test` de `ci_local` invoca `runserver` con `--settings=config.settings.loadtest` explícitamente para usar la DB Docker del contenedor (puerto 15432). **Cualquier script o orquestador que necesite un settings distinto al de desarrollo debe pasar `--settings=` al llamar `runserver`.**

### Ejemplos de uso

```bash
# Pipeline completo (todos los stages)
python scripts/ci_local/ci_local.py

# Sin Locust — más rápido, omite load_test
python scripts/ci_local/ci_local.py --no-load

# Desde un stage en adelante (re-runs parciales)
python scripts/ci_local/ci_local.py --from scenarios

# Solo stages específicos
python scripts/ci_local/ci_local.py --only quality unit_tests integration_tests

# Omitir uno o más stages
python scripts/ci_local/ci_local.py --skip seed_db --no-load

# No eliminar el contenedor al terminar (acelera re-runs)
python scripts/ci_local/ci_local.py --keep-container

# Sin colores ANSI (redirigir salida a archivo)
python scripts/ci_local/ci_local.py --no-color 2>&1 | Tee-Object ci-run.log
```

### Salidas generadas

Los resultados se guardan en `ci-local-out/<stage>/`:

| Archivo | Contenido |
|---------|-----------|
| `output.log` | Log completo del stage |
| `junit.xml` | Resultados pytest (parseable por IDE) |
| `coverage.xml` | Cobertura de código (solo stages que la miden) |
| `locust_*.csv` | Estadísticas de carga (solo `load_test`) |

### Reporte final (ejemplo)

```
  ✓  Quality — lint · format · SAST · docs        12.3s
  ✓  Unit tests (SQLite)                           45.2s  [685✓ 0✗ 0–]
  ✓  Integration tests (scripts + root)             8.1s  [95✓ 0✗ 1–]
  ✓  Scenarios / Gherkin (Postgres)                23.4s  [138✓ 0✗ 7–]
  ✓  Seed DB tests (Postgres)                       5.2s  [9✓ 0✗ 0–]
  ✓  Security tests — OWASP (Postgres)              9.8s  [45✓ 0✗ 0–]
  ✓  Concurrency tests (Postgres)                  15.3s  [4✓ 0✗ 0–]
  ⚠  Load test — Locust (Postgres)                55.0s   ⚠ SLA violations
  ────────────────────────────────────────────────────────────────
  ✓ PASÓ — 1 aviso(s) no bloqueantes   7/8 stages OK   174s total
  Pruebas: 976 total · 976 pasaron · 0 fallaron · 8 saltadas
```

### Indicador de progreso

Durante la ejecución, cada stage muestra una línea de progreso antes del banner:

```
  ── Progreso: [3/8] 37% ──
  ───────────────────────────────────────────────────────────────
  [SCENARIOS]  Scenarios / Gherkin (Postgres)
  ───────────────────────────────────────────────────────────────
```

Esto permite ver rápidamente en qué stage va el pipeline y cuánto falta.

### Abortar con Ctrl+C

Presionar **Ctrl+C** en cualquier momento detiene el pipeline y **elimina automáticamente el contenedor Docker** de Postgres. La limpieza funciona en 3 niveles:

1. **Handler SIGINT** — Detecta Ctrl+C, elimina el contenedor y sale.
2. **atexit** — Si el proceso termina normalmente, el contenedor se limpia igualmente.
3. **Subprocessos** — Si Ctrl+C cae durante un subprocess (pytest, locust, etc.), se termina primero el subprocess antes de limpiar.

Mensajes de salida al presionar Ctrl+C:

```
  CTRL+C detectado — limpiando contenedor Postgres…
  Contenedor Postgres eliminado.
```

Si se usó `--keep-container`, el contenedor **no** se elimina al interrumpir.

---

## 4. Seed unificado de base de datos (`seed_db/`)

### ¿Qué hace?

Puebla la base de datos con datos representativos para desarrollo y demos. El seed ejecuta **24 fases** en orden:

| Fases | Qué crean | Idempotente |
|-------|-----------|:---:|
| 1–6 | Catálogo: usuarios, ubicaciones, categorías, marcas, productos, proveedores | Sí (get_or_create) |
| 7–14 | Movimientos: entradas, traslados, ventas, ajustes, agotados, combos | No (omitidos si existen; `--force` regenera) |
| 15–16 | Configuración de almacenamiento y horarios de usuario | Sí |
| 17–21 | Movimientos adicionales: lotes, devoluciones, daños, vencimiento, combos, OC, precios, facturas | No |
| 22–24 | Escaneo de alertas, webhooks, información de empresa | Sí |

### Datos que genera

- **11 categorías** y **33 marcas** de productos médicos.
- **214 productos** con precios completos (fuente: `Clasificacion_Productos.xlsx`).
- **5 proveedores** y **5 clientes** de ventas al por mayor.
- **3 combos** (KIT-1, KBND-1, KPIT-1).
- Flujo completo: OC → entradas → traslados → ventas → ajustes → combos.
- Stock en 4 ubicaciones: Bodega 1, Vitrina, Bodega Norte, Vitrina 2.

### Archivos del paquete

| Archivo | Responsabilidad |
|---------|-----------------|
| `run.py` | Entry point CLI, configuración de Django, impresión de resumen |
| `seeder.py` | Lógica core del seed (clase `Seeder`, 24 fases, `SeedResult`) |
| `config.py` | Datos estáticos: categorías, productos, proveedores, clientes, combos |
| `env.py` | Carga variables de entorno (`ALMACENISTA_USERNAME`, `EMAIL`, `PASSWORD`) |
| `clean.py` | Limpieza segura de datos del seed en orden FK-safe |

### Argumentos

#### `run.py` (seed)

| Argumento | Descripción |
|-----------|-------------|
| `--force` | Regenera movimientos aunque ya existan. |
| `--production` | Ejecuta seed contra la base de datos de producción (Neon). **Requiere confirmación explícita.** |

#### `clean.py` (limpieza)

| Argumento | Descripción |
|-----------|-------------|
| `--confirm` | Omite el prompt interactivo y ejecuta directamente. |
| `--production` | Ejecuta limpieza contra producción. **Requiere confirmación explícita.** |

### Ejemplos de uso

```bash
# Primera vez — crear almacenista y luego sembrar datos
python manage.py create_almacenista
python scripts/seed_db/run.py

# Regenerar movimientos completos
python scripts/seed_db/run.py --force

# Limpiar datos del seed (preserva almacenista, superusers, ubicaciones base)
python scripts/seed_db/clean.py

# Limpiar sin prompt interactivo
python scripts/seed_db/clean.py --confirm

# Seed contra producción (¡cuidado!)
python scripts/seed_db/run.py --production
```

### Seguridad

- Se niega a ejecutar con settings de producción a menos que se pase `--production` explícitamente.
- `clean.py` preserva: usuario almacenista, superusers de Django, ubicaciones base (bodega/vitrina) y tablas del framework.
- El orden de limpieza respeta las foreign keys: JWT → Sessions → Invoices → PO/Receptions → Movements → Alerts → Catálogo → Ubicaciones extras → Config → Usuarios extras → Webhooks/Audit.

### Guía completa

Para más detalles, consultar [`docs/guias/SEED_DB.md`](../docs/guias/SEED_DB.md).

---

## 5. Generación de documentación de tests (`generate_docs/`)

### ¿Qué hace?

Pipeline idempotente que descubre, clasifica, renderiza y escribe la documentación de **todos** los tests del proyecto. Clasifica cada test en una de 4 familias:

| Familia | Prefijo | Ubicación de tests | Archivos generados |
|---------|---------|-------------------|-------------------|
| `unit` | `UNIT` | `tests/unit/`, `apps/*/tests/` | `all_unit.md` + `unit/*.md` |
| `integration` | `INT` | `tests/integration/`, `tests/concurrency/` | `all_integration.md` + `integration/*.md` |
| `gherkin` | `GEN` | `tests/ers/` | `all_scenarios.md` + `scenarios/*.md` + `gherkin_scenarios.json` |
| `auxiliary` | `AUX` | `tests/scripts/`, `tests/shared/`, `test_service_sla.py` | `all_auxiliary.md` + `auxiliary/*.md` |

### Cuándo usarlo

**Obligatorio antes de `git push`** si modificaste tests o escenarios Gherkin. Esta regla está documentada en `AGENTS.md`.

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `--only {unit,integration,gherkin,auxiliary}` | Genera solo una familia específica. |
| `--force` | Reescribe los archivos aunque no haya cambios detectados. |
| `--check` | Reporta si la regeneración es necesaria (no escribe archivos). Útil en CI. |

### Ejemplos de uso

```bash
# Pipeline completo (recomendado — genera todas las familias)
python -m scripts.generate_docs

# Solo una categoría específica
python -m scripts.generate_docs --only gherkin
python -m scripts.generate_docs --only unit
python -m scripts.generate_docs --only integration
python -m scripts.generate_docs --only auxiliary

# Verificar que la documentación está sincronizada (sin escribir)
python -m scripts.generate_docs --check
```

### Archivos generados

```
docs/test/
├── all_unit.md                 # Índice consolidado de tests unitarios
├── all_integration.md          # Índice consolidado de tests de integración
├── all_scenarios.md            # Índice consolidado de escenarios Gherkin
├── all_auxiliary.md            # Índice consolidado de tests auxiliares
├── gherkin_scenarios.json      # Metadatos JSON de escenarios ERS/Gherkin
├── unit/                       # Ficha individual por test unitario
├── integration/                # Ficha individual por test de integración
├── scenarios/                  # Ficha individual por escenario Gherkin
└── auxiliary/                  # Ficha individual por test auxiliar
```

### Alias legacy

El script `scripts/docs/parse_ers_gherkin.py` es un wrapper delgado que ejecuta `--only gherkin`. **Se recomienda usar `python -m scripts.generate_docs --only gherkin`** en su lugar.

---

## 6. Escaneo de calidad y seguridad (`security/`)

### ¿Qué hace?

Ejecuta secuencialmente las herramientas de calidad del proyecto y genera un **reporte consolidado** en texto plano dentro de `scripts/security/reports/`.

### Herramientas integradas

| Herramienta | Qué verifica | Comando interno |
|-------------|-------------|-----------------|
| `ruff lint` | Linting Python (reglas de estilo y errores) | `ruff check apps/ shared/ config/` |
| `ruff format` | Formato Python (consistent style) | `ruff format --check apps/ shared/ config/` |
| `semgrep` | SAST — patrones de seguridad (Static Application Security Testing) | `semgrep scan --config .semgrep.yml` |
| `bandit` | SAST Python — vulnerabilidades comunes (SQL injection, crypto, etc.) | `bandit -r apps/ shared/` |
| `pip-audit` | Dependencias con CVEs conocidos | `pip-audit` |
| `mypy` | Tipado estático (type checking) | `mypy apps/ shared/` |

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `--output PATH` | Ruta del reporte de salida (default: `reporte_calidad_YYYY-MM-DD_HH-MM.txt`). |
| `--only TOOLS` | Lista separada por comas de herramientas a ejecutar (ej: `--only ruff,semgrep`). |
| `--skip TOOLS` | Lista separada por comas de herramientas a omitir (ej: `--skip mypy`). |
| `--ci` | Modo CI: salida compacta, sin colores, exit code 0 si todo pasa. |
| `--dry-run` | Muestra los comandos sin ejecutarlos. |
| `--list` | Lista las herramientas disponibles y sale. |

### Ejemplos de uso

```bash
# Todas las herramientas
python scripts/security/run_security_scan.py

# Solo ruff (lint + format)
python scripts/security/run_security_scan.py --only ruff

# Solo semgrep (SAST)
python scripts/security/run_security_scan.py --only semgrep

# Solo bandit (vulnerabilidades Python)
python scripts/security/run_security_scan.py --only bandit

# Solo mypy (tipado estático)
python scripts/security/run_security_scan.py --only mypy

# Todas menos mypy
python scripts/security/run_security_scan.py --skip mypy

# Listar herramientas disponibles
python scripts/security/run_security_scan.py --list

# Modo CI (salida compacta)
python scripts/security/run_security_scan.py --ci

# Modo simulación (no ejecuta nada)
python scripts/security/run_security_scan.py --dry-run
```

### Reportes generados

Los reportes se guardan en `scripts/security/reports/` con el formato `reporte_calidad_YYYY-MM-DD_HH-MM.txt`. Cada reporte contiene el resultado de cada herramienta (pass/fail/warn) y un resumen consolidado.

### Semgrep — configuración

Si existe `.semgrep.yml` en la raíz del proyecto, se usa como configuración. Si no, cae a `auto` (requiere red para descargar reglas predefinidas). Timeout por herramienta: 300 segundos.

---

## 7. Árbol de arquitectura (`project_structure/`)

### ¿Qué hace?

Analiza la estructura real del repositorio, filtra solo los nodos relevantes para la arquitectura, los anota con comentarios semánticos y actualiza el bloque del árbol en `docs/README_ARQUITECTURA.md`. También genera `scripts/project_structure/project_structure_report.md` con el delta (altas, bajas, reorganizaciones).

### Cuándo usarlo

**Obligatorio antes de `git push`** si añadiste/quitaste carpetas top-level, moviste apps o cambiaste la estructura del proyecto.

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `--dry-run` | Vista previa sin escribir archivos. |
| `--config PATH` | Archivo JSON con overrides de inclusión/exclusión. |

### Ejemplos de uso

```bash
# Regenerar y escribir docs/README_ARQUITECTURA.md
python scripts/project_structure/generate_project_structure.py

# Vista previa sin escribir
python scripts/project_structure/generate_project_structure.py --dry-run

# Con overrides JSON
python scripts/project_structure/generate_project_structure.py --config architecture-overrides.json
```

### Archivos generados

| Archivo | Contenido |
|---------|-----------|
| `docs/README_ARQUITECTURA.md` | Sección del árbol actualizada (reemplaza el bloque `<!-- tree -->`) |
| `scripts/project_structure/project_structure_report.md` | Reporte de delta: archivos añadidos, eliminados, movidos |

---

## 8. Verificación de base de datos Neon (`db_neo/`)

### ¿Qué hace?

Script de verificación que conecta a la base de datos configurada en `DJANGO_SETTINGS_MODULE=config.settings.development` (normalmente Neon/Postgres) y ejecuta 4 tipos de verificación:

| Verificación | Qué comprueba |
|--------------|---------------|
| Conexión | Versión de PostgreSQL, nombre de la base, host |
| Estado del seed | Conteo de productos, categorías, movimientos, usuarios, alertas |
| Integridad | Seriales, cadena de frío, tipos de movimiento requeridos |
| Alertas de producción | `SECRET_KEY` débil, `DEBUG=True`, CORS demasiado abierto |

### Cuándo usarlo

- Después de correr el seed en Neon para confirmar que los datos llegaron correctamente.
- Antes de un despliegue para hacer un health-check rápido.
- Para diagnosticar discrepancias entre entornos (local vs Neon).

### Requisitos

- Variable `DATABASE_URL` o configuración en `.env.development` apuntando a Neon.
- Entorno virtual activo.

### Ejemplo de uso

```bash
python scripts/db_neo/_verify_neon.py
```

### Salida típica

```
============================================================
  VERIFICACIÓN NEON — ICM
============================================================

[OK] CONEXION EXITOSA
  PG version : PostgreSQL 16.1
  Base de datos : icm_prod

--- Estado del seed ---
  [OK   ] Categorias           : 11
  [OK   ] Productos            : 214
  [OK   ] Movimientos          : 87
  ...

--- Integridad ---
  [OK] Seriales creados                          : 12
  [FAIL] Tipo SALIDA_COMBO existe                : 0
  ...

--- Alertas de produccion ---
  [WARN] DEBUG=True — debe ser False en produccion
```

---

## 9. Pruebas de carga Locust (`perf/`)

### ¿Qué hace?

Define una clase de usuario `HealthCheckUser` para pruebas de carga con [Locust](https://locust.io/). Ejecuta 2 tareas con pesos diferentes:

| Tarea | Método HTTP | Peso | Descripción |
|-------|------------|:----:|-------------|
| `health` | `GET /health/` | 8 | Endpoint de salud del servidor |
| `inventory` | `GET /api/v1/inventory/stock/?page=1` | 2 | Consulta de stock (lectura) |

Tiempo de espera entre tareas: 1–2 segundos.

### Cuándo usarlo

- Automáticamente en `ci_local.py` durante el stage `load_test`.
- Manualmente para pruebas de rendimiento exploratorias.

### Requisitos

- Servidor Django corriendo (en otro terminal).
- Paquete `locust` instalado en el entorno virtual.

### Ejemplos de uso

```bash
# 1. Levantar el servidor Django (en otro terminal)
python manage.py runserver 0.0.0.0:8000

# 2. Locust con interfaz web (abre http://localhost:8089)
locust -f scripts/perf/locustfile.py --host http://localhost:8000

# Locust headless (modo CI: 12 usuarios, 3 spawns/s, 45 segundos)
locust -f scripts/perf/locustfile.py \
       --host http://localhost:8000 \
       --users 12 --spawn-rate 3 --run-time 45s \
       --headless --only-summary
```

### SLAs monitoreados

- **p95** < 500 ms
- **Tasa de error** < 1%

---

## 10. Alias legacy (`docs/`)

### `parse_ers_gherkin.py`

Wrapper delgado de 15 líneas que llama a `scripts.generate_docs` con `--only gherkin`. Existe por compatibilidad con referencias anteriores.

**Recomendación:** Usar directamente `python -m scripts.generate_docs --only gherkin`.

```bash
# Legacy (funciona pero no es preferido)
python scripts/docs/parse_ers_gherkin.py

# Preferido
python -m scripts.generate_docs --only gherkin
```

---

## 11. Checklist antes de `git push`

| Si modificaste… | Ejecuta… | ¿Por qué? |
|-----------------|----------|------------|
| Tests o escenarios Gherkin | `python -m scripts.generate_docs` | Mantener documentación sincronizada |
| Estructura del proyecto (carpetas, apps) | `python scripts/project_structure/generate_project_structure.py` | Actualizar árbol de arquitectura |
| Lógica de negocio o API | `python scripts/security/run_security_scan.py` | Detectar regressions de seguridad |
| Todo lo anterior | `python scripts/ci_local/ci_local.py --no-load` | Verificación integral |

**Importante:** Incluir los archivos generados por estos scripts en el **mismo commit** que los cambios de código.

---

## 12. Convenciones para nuevos scripts

1. **Ubicación:** Crear en una subcarpeta descriptiva (`scripts/<nombre>/`), no en la raíz de `scripts/`.
2. **Paquete:** Añadir `__init__.py` para que sea importable como módulo Python.
3. **Documentación:** Documentar en este README con: propósito, cuándo usarlo, requisitos, uso y ejemplos.
4. **Dry-run:** Ofrecer `--dry-run` si el script modifica archivos del repo.
5. **Tests:** Añadir tests en `tests/scripts/test_<nombre>.py`.
6. **Seguridad:** Nunca ejecutar contra producción sin `--production` explícito y confirmación.
7. **Help:** Incluir argparse con `--help` descriptivo.

---

## 13. Solución de problemas

### Docker no está corriendo (ci_local)

```
[ERROR] Docker no está disponible. Instalar Docker Desktop y确保 que esté corriendo.
```

**Solución:** Iniciar Docker Desktop antes de ejecutar `ci_local.py`.

### Puerto 15432 en uso (ci_local)

```
[ERROR] El puerto 15432 ya está en uso.
```

**Solución:** Detener el contenedor anterior o usar `--keep-container` en el próximo run para reutilizarlo.

### Falta almacenista (seed_db)

```
[ERROR] No existe un usuario almacenista. Ejecuta: python manage.py create_almacenista
```

**Solución:** Ejecutar `python manage.py create_almacenista` antes del seed.

### Neon no accesible (db_neo)

```
[FAIL] CONEXION FALLIDA
```

**Solución:** Verificar que `DATABASE_URL` en `.env.development` apunta a Neon y que la máquina tiene acceso a internet.

### Herramientas de calidad no instaladas (security)

```
[WARN] ruff no encontrado — saltando
```

**Solución:** Instalar las herramientas necesarias: `pip install ruff semgrep bandit pip-audit mypy`.

### Locust no instalado (perf / ci_local load_test)

```
[ERROR] locust no encontrado.
```

**Solución:** `pip install locust` en el entorno virtual.
