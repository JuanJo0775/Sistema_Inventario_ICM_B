README CI/CD - Sistema Inventario ICM

## 1. Objetivo

Este documento define el flujo operativo de CI/CD del proyecto para asegurar:

- integracion continua con gates bloqueantes,
- despliegue reproducible sobre Docker Compose,
- trazabilidad por artefacto inmutable (digest),
- recuperacion ante fallos con backup y rollback verificables.

Registry principal: **GHCR** (`ghcr.io`).

---

## 2. Componentes implementados

### 2.1 Workflows

- `.github/workflows/ci.yml`
	- Lint (`black`, `isort`)
	- Security scan Python (`pip-audit --strict`)
	- Tests unitarios
	- Integration tests con PostgreSQL
	- Tests de escenarios (Gherkin)
	- `makemigrations --check --dry-run`

Nota: Los workflows y scripts de despliegue han sido removidos de este repositorio por decisión del equipo; la canalización actual está limitada a comprobaciones y pruebas CI.

---

## 3. Flujo CI/CD (estado operativo)

### 3.1 CI (PR y push)

Secuencia principal:

1. Lint y quality checks.
2. `pip-audit --strict` (bloqueante).
3. Unit-like tests rapidos.
4. Validacion de docs de tests.
5. `makemigrations --check --dry-run`.
6. Trivy image scan (`HIGH,CRITICAL` bloqueante).
7. Integration tests con PostgreSQL.
8. En `main`: build and push a GHCR, manifest y release.

Comandos equivalentes locales:

```bash
python -m pip install -U pip
pip install -r requirements/base.txt
pip install black==23.12.1 isort==5.13.2 pip-audit pytest pytest-django pytest-cov

black --check .
isort --check-only .
pip-audit --progress=off --strict
pytest -q -k "not integration and not ers" --maxfail=1
python -m scripts.generate_docs --check
python manage.py makemigrations --check --dry-run
```

---

## 4. Artefactos inmutables y trazabilidad

## 4.1 Manifest de release

En CI se genera `release-manifest.json` y se publica como artifact y asset en GitHub Release.

Campos esperados para trazabilidad de despliegues:

- commit SHA
- image digest (`ghcr.io/...@sha256:...`)
- timestamp
- environment
- version desplegada
- migraciones ejecutadas

---

## 5. Backups: politica, integridad y restauracion

## 5.1 Politica de retencion

- Variable: `BACKUP_RETENTION_DAYS`.
- Valor recomendado inicial: `14` dias (ajustable por cumplimiento).
- Backups locales en `/srv/backups`.
- Recomendado: subida a almacenamiento remoto cifrado (S3 o equivalente).

## Tests, reproducibilidad y artefactos

- `test-postgres` (/.github/workflows/ci-postgres.yml): ejecuta la suite completa contra un servicio Postgres, genera `coverage.xml` y falla si la cobertura sobre `apps/` es menor al umbral (85%). También ejecuta `pip-audit` y sube artefactos.

Requisitos locales para reproducir:

1. Tener un contenedor Postgres accesible en 127.0.0.1:5432 con credenciales postgres/postgres y DB testdb.
2. Exportar `DJANGO_SETTINGS_MODULE=config.settings.test` y, si quieres ejecutar concurrencia, `RUN_CONCURRENCY_TESTS=1`.

Comandos útiles:

Ejecutar tests con coverage localmente:

```bash
python -m pytest --cov=apps --cov-report=xml
```

Ejecutar solo integración contra Postgres:

```bash
set DJANGO_SETTINGS_MODULE=config.settings.test
set DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/testdb
pytest tests/integration -q
```

Artefactos generados por el job CI:

- `coverage.xml` — reporte cobertura (pyproject/pytest-cov)
- `pip_audit.json` — listado de vulnerabilidades de dependencias (pip-audit)

Notas de seguridad:

- `pip-audit` se ejecuta en modo `continue-on-error` para no bloquear PRs por falsos positivos, pero el artefacto se sube para revisión manual. Podemos hacer que falle si se desea.
