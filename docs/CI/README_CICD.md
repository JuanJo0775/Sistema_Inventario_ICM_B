# README CI/CD - Sistema Inventario ICM

## 1. Objetivo

Este documento resume el estado operativo de CI del proyecto para que los gates de calidad, pruebas y documentación queden alineados con el repositorio real.

Alcance actual:

- lint y formato,
- seguridad estática y supply chain,
- validación de migraciones,
- documentación de tests sincronizada,
- suite de pruebas unitarias, integración de scripts/tests, escenarios, concurrencia y locust,
- seed DB end-to-end en PR,
- carga opcional con Locust.

No existe en este repositorio un flujo de despliegue automatizado completo. La canalización activa está enfocada en validación y pruebas.

---

## 2. Workflows actuales

### 2.1 `.github/workflows/ci.yml`

Este workflow se ejecuta en `push`, `pull_request` y `workflow_dispatch`.

Jobs reales:

1. `quality`
2. `unit_tests`
3. `integration_tests`
4. `scenarios`
5. `seed_db_tests` (solo `pull_request`)
6. `concurrency_tests`
7. `load_test`

### 2.2 Resumen de cada job

#### `quality`

Ejecuta:

- `black --check .`
- `isort --check-only .`
- `flake8 apps/ shared/`
- `bandit -r apps shared -ll`
- `pip-audit --progress=off`
- `mypy apps/ shared/`
- `python manage.py makemigrations --check --dry-run`
- `python -m scripts.generate_docs --check`

#### `unit_tests`

Ejecuta la suite rápida de apps:

- `pytest apps/ -q --ignore=tests`

Genera:

- `junit-unit.xml`
- `coverage-unit.xml`

#### `integration_tests`

Ejecuta los tests de integración liviana del repositorio:

- `pytest tests/integration tests/scripts tests/shared -q`

Genera:

- `junit-integration-tests.xml`
- `coverage-integration-tests.xml`

#### `scenarios`

Levanta PostgreSQL y ejecuta los escenarios Gherkin / ERS:

- `pytest tests/ers -q`

Genera:

- `junit-gherkin.xml`
- `coverage-gherkin.xml`

#### `seed_db_tests`

Ejecuta el seed end-to-end completo:

- `pytest tests/scripts/test_seed_db.py -q`

Este job corre solo en `pull_request`.

#### `concurrency_tests`

Ejecuta:

- `pytest tests/concurrency -v`

Usa PostgreSQL y la variable:

- `RUN_CONCURRENCY_TESTS=1`

#### `load_test`

Ejecuta Locust contra un servidor Django levantado en el mismo job.

Genera:

- `locust-results_*.csv`

---

## 3. Comandos locales equivalentes

Para reproducir los gates principales:

```bash
python -m pip install -U pip
pip install -r requirements/base.txt
pip install black==23.12.1 isort==5.13.2 pip-audit pytest pytest-django pytest-cov bandit

black --check .
isort --check-only .
bandit -r apps shared -ll
pip-audit --progress=off
python manage.py makemigrations --check --dry-run
python -m scripts.generate_docs --check
pytest apps/ -q --ignore=tests
pytest tests/integration tests/scripts tests/shared -q
pytest tests/ers -q
pytest tests/scripts/test_seed_db.py -q
pytest tests/concurrency -v
```

Para correr la suite completa:

```bash
pytest -q
```

---

## 4. Estado actual de pruebas

Último estado verificado localmente:

- `646 tests recolectados`
- `637 pasan`
- `9 skips legítimos`
- `0 fallos`

Referencia viva:

- [docs/test/README_TEST.md](../test/README_TEST.md)
- [docs/test/CHANGELOG_TESTING.md](../test/CHANGELOG_TESTING.md)

---

## 5. Artefactos de CI

Los artefactos esperados en CI son:

- `junit-unit.xml`
- `coverage-unit.xml`
- `junit-integration-tests.xml`
- `coverage-integration-tests.xml`
- `junit-gherkin.xml`
- `coverage-gherkin.xml`
- `junit-seed-db.xml`
- `junit-concurrency.xml`
- `locust-results_*.csv`

---

## 6. Notas operativas

- `python -m scripts.generate_docs --check` debe pasar en `quality`.
- La documentación de pruebas debe mantenerse sincronizada cuando cambian tests o escenarios Gherkin.
- La suite de concurrencia requiere PostgreSQL y no se ejecuta sobre SQLite.
- El job `load_test` es informativo y depende de un servidor Django accesible dentro del runner.
