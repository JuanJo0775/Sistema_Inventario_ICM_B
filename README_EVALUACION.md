Resumen de revisión del repositorio — Sistema Inventario ICM
=========================================================

Estado real (resumen breve)
---------------------------
- Código y documentación congruentes: la arquitectura documentada en `docs/README_ARQUITECTURA.md` está implementada con claridad en apps modulares (`apps/*`) y la separación `services.py` / `selectors.py` / `models.py` se respeta en la mayoría de casos.
- Núcleo crítico funcionando: `apps.movements.services` y modelos asociados (`Movement`, `StockByLocation`, `InvoiceCounter`) implementan las reglas BR-04…BR-13 y están cubiertos por tests unitarios relevantes.
- Excelente documentación de pruebas: hay una suite Gherkin dinámica que enlaza 95 escenarios y scripts para regenerar documentación (`docs/test/*`, `tests/ers/*`); los 6 casos no automatizables en backend quedaron marcados de forma persistente como fuera de alcance.
- Falta pipeline CI/CD automatizado visible y no hay workflows de GitHub Actions; Docker y docker-compose están disponibles.
- Cobertura de tests y generación de docs está preparada, pero no hay evidencia de ejecución automática en CI; la suite de tests unitarios de `apps/movements` prueba casos críticos y la documentación Gherkin preserva los escenarios fuera de alcance tras regeneración.

Hallazgos clave
---------------
- Arquitectura: monolito modular bien estructurado; patrón ledger + stock derivado implementado correctamente.
- Features implementadas: core de movimientos (entradas, salidas, traslados, ajustes, devoluciones), validaciones críticas (serials, validación cruzada, ventanas de corrección), generación de factura (PDF opcional si WeasyPrint disponible).
- Pendientes / gaps detectados: ausencia de CI/CD, ambigüedad en tags OpenAPI (inglés vs español) y posibles discrepancias menores en nomenclatura de tags; no hay workflows para ejecutar `pytest`, lint y generación de docs.
- Calidad tests: buena cobertura en dominio crítico (`apps/movements/tests`); la suite dinámica Gherkin ya distingue entre escenarios implementados y 6 casos UI/infra documentados como fuera de alcance backend.
- Deuda técnica: decisiones abiertas documentadas en `.github/ISSUES/` (idempotencia correcciones, protección append-only para audit logs), y falta de mecanismo de WORM/append-only en storage si se requiere cumplimiento legal más estricto.
- Riesgos operativos: sin CI, regresiones pueden llegar a `staging/main`; falta de pipelines automatizados para migraciones, pruebas y despliegue.

Prioridades (3–5)
------------------
1. Añadir CI/CD básico (GitHub Actions) que ejecute: lint (black/isort), `pytest --maxfail=1 -q`, y generación de `docs/test` y `api/schema` — impacto: alto, reduce riesgo de regresión.
2. Validar y consolidar la suite Gherkin: ejecutar `tests/ers/test_gherkin_dynamic.py` en CI con reportes y mantener documentados los 6 escenarios fuera de alcance backend — impacto: alto en trazabilidad requisitos↔tests.
3. Asegurar idempotencia/concorrencia en correcciones y contador de facturas: revisar y añadir tests de concurrencia para `InvoiceCounter` y `correct_movement_within_window` — impacto: crítico para integridad ledger.
4. Añadir protección de auditoría (append-only) y políticas de retención/pseudonimización para PII en `audit` (si aplica cumplimiento legal) — impacto: medio-alto en cumplimiento.
5. Armonizar documentación OpenAPI (tags/idioma) y añadir checks automáticos para `@extend_schema` en endpoints nuevos — impacto: medio, mejora UX dev y mantenimiento.

Siguiente paso lógico inmediato
------------------------------
Implementar un pipeline CI mínimo (GitHub Actions) que en cada push/PR ejecute: instalación de dependencias, `pytest -q`, lint (black/isort), y genere `docs/test/all_*.md` y el esquema OpenAPI (`/api/schema/`) como artefacto.

Por qué este paso tiene prioridad
---------------------------------
- Reduce riesgo inmediato de que cambios rompan el ledger, contratos o tests críticos antes de fusionar ramas.
- Protege la inversión existente en tests y documentación, automatizando su ejecución y evidenciando regressions temprano.
- Es un prerequisito para desplegar cambios seguros y para crear gates de calidad (estatus required en PRs).

Plan de ejecución concreto y secuencial
-------------------------------------
1. Añadir workflow `ci.yml` en `.github/workflows/ci.yml` (PRs y pushes a `staging`/`main`):
   - Jobs: `lint`, `test` (unit + ers smoke), `docs` (regenerar `docs/test` y `api/schema`).
   - Runner: `ubuntu-latest`; usar cache de pip.
   - Salidas: publicar `pytest` junit xml + `api/schema.yml` y `all_test_docs` como artefactos.
   - Estimado: 1 día.
2. Configurar jobs:
   - `lint`: `black --check`, `isort --check-only`.
   - `test`: `pytest -q --maxfail=1`; marcar slow tests si aplica.
   - `docs`: ejecutar `python -m scripts.generate_docs` y guardar `docs/test/all_*.md`.
   - Estimado: 0.5–1 día.
3. Añadir badge de CI al `README.md` y documentar workflow en `docs/GUIA_ONBOARDING.md`.
   - Estimado: 0.25 día.
4. Ejecutar en PRs y corregir fallos reportados; priorizar arreglar tests rotos o flakiness.
   - Estimado variable según fallos.
5. Tras estabilizar CI: agregar pipeline de CD (deploy docker-compose to staging) y protección de ramas.
   - Estimado: 1–2 días adicionales.

Supuestos, inconsistencias y decisiones cuestionables
---------------------------------------------------
- Supuesto: entorno local de CI usa PostgreSQL; los tests se configuran con `config.settings.test` (SQLite in-memory) — confirmar que los tests críticos no dependen de Postgres-only behavior.
- Inconsistencia menor: `docs/api/README_API.md` usa tags en español (p. ej. `Autenticación`) mientras `shared/openapi.py` define tags en inglés (`TAG_AUTH = "auth"`). Recomiendo unificar (usar las constantes `TAG_*` como fuente única).
- Decisión pendiente: política de idempotencia para `correct_movement_within_window` y generación de facturas duplicadas; hay issues documentadas que requieren decisión (ver `.github/ISSUES/*`).

Datos críticos faltantes para decidir con más exactitud
-----------------------------------------------------
- Estado actual del coverage (porcentaje). No hay reporte `coverage.xml` en repo: ejecutar `pytest --cov=apps --cov-report=xml` en CI para obtener cifra.
- ¿Requiere el proyecto cumplimiento legal (WORM) para auditoría en producción? Si sí, la arquitectura de storage y políticas de retención cambian.
- ¿Preferencia de plataforma CI (GitHub Actions obligatoria) o uso de otro proveedor? Asumo GitHub Actions por integrarse con repositorio.

Archivos y pruebas relevantes que verifiqué (evidencia)
---------------------------------------------------
- docs/README_ARQUITECTURA.md — implementación y reglas BR-01..BR-13.
- docs/api/README_API.md — contrato API y checklist.
- docs/test/README_TEST.md — estrategia de tests y generación de docs.
- apps/movements/services.py — núcleo de lógica de inventario y facturación.
- apps/movements/models.py — `Movement`, `InvoiceCounter`.
- apps/inventory/models.py — `StockByLocation`, `Location`.
- apps/movements/tests/test_services.py — tests unitarios críticos del ledger.
- tests/ers/test_gherkin_dynamic.py — suite dinámica Gherkin.

Si quieres, implemento el `ci.yml` de GitHub Actions y un PR con la pipeline inicial y badges; dime si lo hago ahora.
