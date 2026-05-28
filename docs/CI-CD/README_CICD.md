# README CI/CD - Sistema Inventario ICM

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

### 2.2 Scripts operativos

Los scripts operativos previamente en `deploy/` fueron eliminados del repositorio. Las tareas operativas (backups, despliegues y smoke tests) deben gestionarse externamente o mediante la plataforma de hosting/environamiento correspondiente.

---

## 3. Flujo CI/CD (estado operativo)

## 3.1 CI (PR y push)

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

## 3.2 Deploy a staging

Trigger: `push` a rama `staging`.

Comportamiento:

1. Build y push de imagen a GHCR para staging.
2. Conexion SSH al host.
3. Backup pre-deploy (si script existe).
4. Pull + update de compose.
5. Smoke tests.

## 3.3 Promocion a production

Trigger: manual (`workflow_dispatch`) con inputs:

- `image_digest` (obligatorio)
- `version` (obligatorio)
- `migrations_executed` (opcional)

Comportamiento:

1. Requiere aprobacion de environment `production`.
2. Backup DB obligatorio.
3. Pinea imagen por digest en `docker-compose.yml` del host.
4. `docker compose up -d --remove-orphans`.
5. Smoke test.
6. Si falla smoke test: rollback automatico al compose previo.
7. Guarda manifiesto JSON en `/srv/icm/releases/`.

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

Nota: el workflow de CI hoy genera un manifest minimo (`image`, `ref`) y el workflow de produccion genera manifiesto enriquecido en servidor. Si se requiere uniformidad total, unificar ambos formatos en siguiente iteracion.

## 4.2 Regla de rollback reproducible

Rollback recomendado:

1. Identificar digest estable anterior desde:
   - GitHub Release `release-<sha>` y su `release-manifest.json`, o
   - `/srv/icm/releases/release-*.json` en host productivo.
2. Re-ejecutar `promote-to-production.yml` con ese `image_digest`.
3. Registrar evento de rollback (motivo, version, timestamp).

---

## 5. Backups: politica, integridad y restauracion

## 5.1 Politica de retencion

- Variable: `BACKUP_RETENTION_DAYS`.
- Valor recomendado inicial: `14` dias (ajustable por cumplimiento).
- Backups locales en `/srv/backups`.
- Recomendado: subida a almacenamiento remoto cifrado (S3 o equivalente).

## 5.2 Validacion de integridad

El script ejecuta:

```bash
gunzip -t <backup>.sql.gz
sha256sum <backup>.sql.gz > <backup>.sql.gz.sha256
```

Verificacion manual:

```bash
gunzip -t /srv/backups/db-backup-YYYYMMDDTHHMMSSZ.sql.gz
sha256sum -c /srv/backups/db-backup-YYYYMMDDTHHMMSSZ.sql.gz.sha256
```

## 5.3 Restauracion (runbook)

Ejemplo de restauracion:

```bash
gunzip -c /srv/backups/db-backup-YYYYMMDDTHHMMSSZ.sql.gz | psql -h <host> -U <user> -d <database>
```

Tiempos estimados:

- Verificacion integridad: segundos.
- Restore: depende del tamano del dump y del I/O del host.

Sugerencia operativa:

- validar restore periodicamente en staging (restore-test automatizado pendiente).

## 5.4 Seguridad de backups

- No publicar dumps como artifacts de GitHub Actions.
- No registrar secretos en logs.
- Limitar permisos de `/srv/backups` (`700`).
- Cifrar almacenamiento remoto y limitar IAM por minimo privilegio.

---

## 6. Migraciones Django (operacion segura)

Controles actuales:

- CI bloquea drift con:

```bash
python manage.py makemigrations --check --dry-run
```

- Produccion solicita `migrations_executed` en promocion para trazabilidad.

Practica recomendada de despliegue con migraciones:

1. Backup pre-migracion (obligatorio).
2. Ejecutar migraciones en ventana controlada.
3. Ejecutar smoke tests.
4. Si falla: rollback de artefacto y restauracion de DB si la migracion no es reversible.

---

## 7. Seguridad y secretos

## 7.1 Secrets requeridos (GitHub Environments/Secrets)

Generales:

- `GHCR_PAT`
- `BACKUP_RETENTION_DAYS`
- `COSIGN_PRIVATE_KEY` (opcional)
- `COSIGN_PASSWORD` (opcional)

Staging:

- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_PORT`
- `STAGING_BASE_URL`

Production:

- `PRODUCTION_SSH_HOST`
- `PRODUCTION_SSH_USER`
- `PRODUCTION_SSH_PRIVATE_KEY`
- `PRODUCTION_SSH_PORT`
- `PRODUCTION_BASE_URL`

Backups remotos (opcional):

- `S3_BUCKET`
- credenciales AWS por mecanismo seguro del host (no hardcodeadas en repo)

## 7.2 Politicas bloqueantes activas

- `pip-audit --strict`
- Trivy `HIGH,CRITICAL` con `exit-code: 1`

---

## 8. Concurrencia, fallos y recuperacion

- Staging deploy usa `concurrency` por rama (`deploy-staging-*`).
- Produccion usa `concurrency` (`promote-production`).
- Si smoke test falla en produccion:
  - se revierte `docker-compose.yml` al backup previo,
  - se relanza `docker compose up -d`.

Recuperacion ante fallos severos:

1. rollback de digest a ultimo release estable,
2. restauracion DB desde backup validado,
3. re-ejecucion de smoke tests,
4. documentar incidente y RCA.

---

## 9. Operacion manual (comandos utiles)

## 9.1 Promocion manual a produccion

Usar UI de GitHub Actions sobre `Promote to Production` con:

- `image_digest`: `sha256:...`
- `version`: `vX.Y.Z`
- `migrations_executed`: `none` o lista

## 9.2 Ver historial de releases en host

```bash
ls -1 /srv/icm/releases
cat /srv/icm/releases/release-<timestamp>.json
```

## 9.3 Ejecutar backup manual en host

```bash
cd /srv/icm
# Los scripts en `deploy/` fueron removidos del repositorio.
# Gestionar backups fuera del repositorio (p. ej. cron, Ansible o la plataforma de hosting).
```

## 9.4 Checklist pre-PR CI/CD

Validar este checklist antes de abrir o actualizar un PR que toque infraestructura, despliegue o seguridad:

- [ ] `black --check .`
- [ ] `isort --check-only .`
- [ ] `pip-audit --progress=off --strict`
- [ ] `python manage.py makemigrations --check --dry-run`
- [ ] `python -m scripts.generate_docs --check`
- [ ] `pytest -q -k "not integration and not ers" --maxfail=1`
- [ ] (si aplica) `pytest tests/integration -q`
- [ ] (si aplica) build local de imagen: `docker build -t icm-local:dev .`
- [ ] actualizar documentación impactada (`README_CICD`, onboarding, arquitectura o API)
- [ ] incluir plan de rollback en la descripción del PR cuando haya cambios de deploy/migraciones

---

## 10. Brechas pendientes y siguientes iteraciones

1. Unificar manifest enriquecido tambien en CI (no solo en host de produccion).
2. Verificacion obligatoria de firma cosign en promocion (`cosign verify`) antes de desplegar.
3. Restore-test automatizado en staging.
4. Observabilidad ampliada:
   - Sentry,
   - metricas Prometheus,
   - healthchecks de app y DB en Compose.
5. Ajustar staging para consumir exactamente el mismo digest promovido a produccion, evitando cualquier rebuild entre entornos.

---

## 11. Criterio de exito operativo

El flujo se considera estable cuando:

- cada despliegue se traza a un digest inmutable,
- existe backup valido antes de cambios de produccion,
- rollback es ejecutable en minutos,
- los gates de seguridad bloquean hallazgos severos,
- los smoke tests detectan fallos funcionales basicos antes de cerrar la promocion.
