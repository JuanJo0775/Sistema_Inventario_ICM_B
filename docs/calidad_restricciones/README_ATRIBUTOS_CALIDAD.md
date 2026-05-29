# README de Atributos de Calidad - Sistema Inventario ICM

Este documento consolida el estado de los atributos de calidad observables en el repositorio. Cada atributo se apoya en evidencia concreta del codigo, la configuracion y la documentacion; cuando el atributo tiene una madurez parcial, se indica el riesgo y la recomendacion.

## Criterio de lectura

- **Estado actual**: valoracion sintetica de la situacion observada.
- **Evidencia**: archivos o decisiones que la respaldan.
- **Madurez**: Baja, Media o Alta.
- **Métrica posible**: una forma pragmatica de medir el atributo en el futuro.
- **Trade-off**: costo asumido por la decision actual.

## Atributos documentados

| Atributo | Estado actual | Evidencia | Riesgos | Madurez | Recomendaciones | Componentes involucrados | Métricas posibles | Trade-off |
|---|---|---|---|---|---|---|---|---|
| Escalabilidad | Media-baja | Monolito modular, una sola BD, sin replicas de lectura | El volumen de reportes puede competir con escrituras | Media | Agregar caché o replicas lectoras en fases futuras | `apps/*`, PostgreSQL, reportes | p95 por endpoint, CPU de BD, conexiones activas | Menor complejidad ahora, menor elasticidad horizontal |
| Mantenibilidad | Alta | Separacion por capas, docs, ADRs, tests, settings por entorno | Deriva entre codigo y docs si no se sincronizan los cambios | Alta | Mantener docstrings, ADRs y matrices de trazabilidad al dia | `services.py`, `selectors.py`, docs, tests | cobertura por capa, tiempo medio de cambio | Mas disciplina editorial a cambio de menor deuda tecnica |
| Disponibilidad | Media | Docker Compose, health checks y entrypoint con migraciones | No hay HA ni failover en este alcance | Media | Definir estrategia de reinicio y backup si el despliegue crece | Docker, PostgreSQL, `entrypoint.sh` | uptime, restart count, migracion exitosa | Simplicidad operativa a cambio de menos tolerancia a caidas |
| Seguridad | Alta | JWT, RBAC, HTTPS en produccion, CORS restringido, auditoria inmutable | Fuga de tokens o secretos si se gestionan mal | Alta | Rotacion de secretos, hardening de headers y revisiones de permisos | auth, permissions, settings, audit | intentos 401/403, rotacion de refresh, eventos auditados | Seguridad fuerte a cambio de mayor complejidad de acceso |
| Rendimiento | Media | Selectores, paginacion, indices previstos, agregaciones en BD | N+1 o consultas pesadas si se ignoran selectores | Media | Vigilar planes de consulta y agregar caches selectivos | selectors, inventory, reports | p95, conteo de queries, tiempo de respuesta | Consultas mas expresivas a cambio de mas trabajo de optimizacion |
| Observabilidad | Media-baja | Logging de consola y audit log del dominio | Falta trazado distribuido o metrics stack | Baja | Agregar logs estructurados, trazas y metricas exportables | `LOGGING`, `audit` | cobertura de eventos, latencia por etapa, errores por tipo | Menor costo inicial a cambio de menos visibilidad operativa |
| Tolerancia a fallos | Media | Transacciones atomicas y `select_for_update()` en reglas criticas | No hay colas ni reintentos automaticos | Media | Introducir reintentos seguros donde aplique y monitoreo de rollback | movements, inventory, PostgreSQL | tasa de rollback, retries, deadlocks | Integridad fuerte a cambio de menos paralelismo simple |
| Testabilidad | Alta | pytest, factory-boy, docs de pruebas, capas separadas | La suite de pruebas usa SQLite y no reproduce todos los comportamientos | Media | Ejecutar escenarios de concurrencia contra PostgreSQL en pruebas especificas | `tests/`, `apps/*/tests`, `config/settings/test.py` | cobertura, flakiness, tiempo por suite | Rapidez local a cambio de fidelidad parcial |
| Portabilidad | Media | Docker, variables de entorno, settings por entorno | La imagen de produccion exige dependencias runtime explicitas | Media | Mantener matrix de build y runtime por entorno | Docker, settings, requirements | tasa de arranque por entorno, errores de build | Portabilidad razonable a cambio de control estricto del runtime |
| Usabilidad | Media | OpenAPI, Swagger, rutas consistentes, versionado REST | La UX de API depende de que la documentacion siga al codigo | Media | Mantener tags y schemas completos, ejemplos y errores uniformes | API, docs, serializers | completitud OpenAPI, soporte de errores 4xx | Facilidad de consumo a cambio de mas documentacion obligatoria |
| Modificabilidad | Alta | Apps por dominio, servicios aislados, selectors de lectura | Si se rompe la frontera entre capas, el cambio se vuelve riesgoso | Alta | Proteger la capa de servicio con tests de regresion | apps, shared, tests | lead time de cambio, cantidad de archivos tocados por cambio | Cambios mas seguros a cambio de mas estructura |
| Resiliencia | Media | Inmutabilidad del ledger y stock derivado reconstruible | Sin colas o compensaciones automaticas ante fallos complejos | Media | Definir flujos de reintento o compensacion en procesos futuros | movements, inventory, audit | tasa de recuperacion, tiempo de remediacion | Consistencia fuerte a cambio de menos automatizacion reactiva |
| Compatibilidad | Media-alta | REST/JSON, JWT, versionado `/api/v1/` | Cambios incompatibles requieren nueva version | Alta | Respetar contratos de version y usar depuracion via OpenAPI | API, frontend, auth | errores por version, tasa de adopcion de endpoint | Compatibilidad clara a cambio de mayor disciplina de versionado |
| Auditabilidad | Alta | Movimiento inmutable, AuditLog, trazabilidad por usuario | Eventos omitidos o acceso directo a BD degradan la trazabilidad | Alta | Verificar cobertura de eventos y prohibir ediciones directas del ledger | `movements`, `audit`, `reports` | porcentaje de eventos auditados, trazabilidad por usuario | Auditoria completa a cambio de mayor complejidad de escritura |

## Lectura ejecutiva

- Los atributos mas maduros hoy son mantenibilidad, seguridad, auditabilidad y modificabilidad.
- Los atributos con mayor deuda tecnica son observabilidad, disponibilidad y escalabilidad.
- Testabilidad es alta en estructura, pero su fidelidad de motor de base de datos es parcial.

## Recomendaciones prioritarias

1. Añadir observabilidad operativa real: logs estructurados, metricas y trazas.
2. Crear pruebas de concurrencia sobre PostgreSQL para cerrar la brecha de fidelidad.
3. Definir una estrategia futura de disponibilidad, backups y recuperacion.
4. Mantener la disciplina de ADRs para que modificabilidad y auditabilidad no se erosionen.

## Relacion con la documentacion existente

- [docs/calidad_restricciones/README_RESTRICCIONES.md](README_RESTRICCIONES.md) contiene las restricciones que condicionan estos atributos, incluyendo clasificación formal REST-01 a REST-06.
- [docs/README_ARQUITECTURA.md](../README_ARQUITECTURA.md) describe el marco tecnico que sostiene la mayoria de ellos.
- [docs/calidad_restricciones/INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md](INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md) sintetiza la conclusión defendible sobre KISS, DRY, YAGNI, rendimiento, disponibilidad y seguridad.
- [docs/architecture/utility_tree.md](../architecture/utility_tree.md) consolida estos atributos en formato Utility Tree con métricas concretas, calificaciones (A/M/B) y driver más crítico identificado.
- [docs/architecture/architecture_drivers.md](../architecture/architecture_drivers.md) prioriza los drivers con identificadores formales DF-01 a DF-06.
- [docs/architecture/adr_relationships.md](../architecture/adr_relationships.md) contiene la matriz de trazabilidad Driver → Táctica → ADR del Corte 2.

## Escenarios de Calidad (ISO 25010)

Los siguientes escenarios están redactados con el formato: Fuente, Estímulo, Entorno, Artefacto, Respuesta y Medida (vital). Cada escenario es verificable mediante pruebas automatizadas o pruebas de carga/aceptación.

### Idoneidad funcional
- Fuente: Usuario (almacenista/auxiliar_despacho) o sistema externo que crea/ejecuta una orden.
- Estímulo: Solicitud de registro de entrada/salida con SKU válido y (si aplica) número de serie.
- Entorno: Entorno de producción simulado (Docker Compose + PostgreSQL) durante operación normal.
- Artefacto: Endpoint `POST /api/v1/movements/` y `services.register_entry()`.
- Respuesta: El movimiento se crea, `StockByLocation` se actualiza en la misma transacción y el ledger queda inmutable.
- Medida: 100% de peticiones válidas resultan en movimiento persistido y stock consistente (0 inconsistencias en 1000 operaciones secuenciales).

### Rendimiento
- Fuente: Herramienta de carga (locust/jmeter) o pruebas de integración automatizadas.
- Estímulo: 50 usuarios concurrentes ejecutando traslados y consultas de stock durante 10 minutos.
- Entorno: Imagen producto (o equivalente) corriendo en Docker Compose con PostgreSQL de prueba (no SQLite).
- Artefacto: Endpoints `POST /api/v1/movements/` y `GET /api/v1/inventory/stock/`.
- Respuesta: El sistema responde sin errores y mantiene latencias aceptables.
- Medida: p95 < 800ms para operaciones de escritura, p95 < 300ms para lecturas, tasa de éxito >= 99.5% y sin deadlocks persistentes (>0 por cada 10k operaciones).

### Compatibilidad
- Fuente: Integración CI que valida contratos OpenAPI y clientes consumidores (frontend o scripts externos).
- Estímulo: Publicación de una nueva versión menor del API o simulado consumo por cliente antiguo.
- Entorno: Entorno de pruebas con generación de clientes desde `drf-spectacular` y tests de compatibilidad.
- Artefacto: Esquemas OpenAPI (`/schema/`) y endpoints REST.
- Respuesta: Los clientes existentes siguen funcionando para rutas no-deprecadas; contratos incompatibles se detectan.
- Medida: 0 fallos de compatibilidad en pruebas de contrato automatizadas; si se rompe, debe existir ADR o versión `/api/v2/` documentada.

### Usabilidad
- Fuente: Usuario final (almacenista, auxiliar) ejecutando flujos de despacho en entorno de staging.
- Estímulo: Flujo completo de despacho con escaneo `scanned_code` y validación cruzada con `order_sku`.
- Entorno: Staging con datos representativos y documentación OpenAPI disponible.
- Artefacto: Flujo de UI/consumidor que llama a la API y mensajes de error del backend.
- Respuesta: Mensajes de error claros, ejemplos en OpenAPI y procesos de corrección guiados.
- Medida: Tasa de éxito en primer intento ≥ 98% en pruebas de usabilidad; tiempos de tarea (TTR) < 2min para un despacho estándar.

### Confiabilidad
- Fuente: Monitor de operaciones o suite de pruebas de resiliencia.
- Estímulo: Caída temporal del servicio de BD (simulada) o reinicio de contenedor de aplicación.
- Entorno: Docker Compose con restarts/healthchecks habilitados.
- Artefacto: Procesos de escritura en `movements.services` y operaciones de lectura de stock.
- Respuesta: El sistema realiza rollbacks seguros, mantiene integridad del ledger y se recupera sin corrupción de datos.
- Medida: Tiempo de recuperación (RTO) < 5 minutos; ningún movimiento parcialmente aplicado; porcentaje de operaciones fallidas por incidente < 0.5%.

### Seguridad
- Fuente: Auditor de seguridad o pruebas automatizadas (SAST/DAST) y revisión de tokens.
- Estímulo: Intentos de acceso no autorizado y reuso de tokens expirados.
- Entorno: Entorno de pruebas con JWT y reglas RBAC habilitadas.
- Artefacto: Endpoints protegidos, sistema de tokens (`rest_framework_simplejwt`) y logs de auditoría.
- Respuesta: Accesos no autorizados son rechazados, eventos registrados en audit log y tokens invalidos no permiten operación.
- Medida: 100% de intentos inválidos producen 401/403; auditoría completa para todas las operaciones sensibles; rotación de secretos documentada cada X meses (según política).

### Mantenibilidad
- Fuente: Equipo de desarrollo realizando cambios de feature o refactor.
- Estímulo: PR que modifica `services.py` y `selectors.py` para un caso de negocio.
- Entorno: CI local con linters y suite de tests unitarios e integracion (pytest).
- Artefacto: Código en `apps/*/services.py`, tests y ADRs relacionados.
- Respuesta: Cambios validados por tests, docstrings y ADRs; cobertura no degrada invariantes críticas.
- Medida: Tiempo medio para PR aceptado < 48h; cobertura de tests no disminuye más de 2% por PR; número de archivos afectados por cambio típico < 6.

### Portabilidad
- Fuente: Ingeniero de DevOps construyendo la imagen de producción.
- Estímulo: Build de imagen de Docker usando `docker/Dockerfile` y `requirements/production.txt`.
- Entorno: Pipeline de build o local con la misma versión de Python y dependencias.
- Artefacto: Imagen Docker resultante y despliegue via `docker-compose.prod.yml`.
- Respuesta: La imagen arranca correctamente con `gunicorn` y configura variables de entorno desde `.env`.
- Medida: 100% de builds reproducibles en el pipeline; tiempo de arranque de la app < 30s en entorno controlado; errores de arranque por dependencias faltantes = 0.

---

He añadido estos escenarios verificables al final del documento para que cada atributo tenga al menos un escenario en el formato requerido. Si quieres, puedo:

- Añadir scripts de prueba (locust / pytest) que validen automáticamente algunos de estos escenarios.
- Generar plantillas de pruebas de compatibilidad OpenAPI y de concurrencia PostgreSQL.

## Evidencia de cumplimiento (acciones rápidas aplicadas)

Se han añadido artefactos mínimos para proporcionar evidencia reproducible de los atributos y habilitar checks básicos en CI:

- Workflow CI: `.github/workflows/basic_checks.yml` — ejecuta `pytest -q` y `bandit -r .` para validar comportamiento y SAST básico.
- Script de carga ligero: `scripts/perf/locustfile.py` — escenario mínimo que ejecuta `GET /health/` y consultas de stock (`GET /api/v1/inventory/stock/`).

Cómo ejecutar localmente (entorno de desarrollo con la app corriendo):

```bash
# Tests unitarios/integración
pytest -q

# Bandit SAST
pip install bandit
bandit -r . -ll

# Locust (prueba de rendimiento ligera)
pip install locust
locust -f scripts/perf/locustfile.py --host=http://localhost:8000

# En el UI de Locust, lanzar 50 usuarios y revisar p95 en el resumen.
```

Notas:

- Estos artefactos no sustituyen una estrategia completa de HA o observabilidad, sino que proporcionan evidencia reproducible y gates mínimos para declarar completitud operativa sin sobre‑ingeniería.
- Próximo paso recomendado: ejecutar los checks y adjuntar los reportes (pytest xml, bandit report, resumen locust) en una carpeta `docs/evidence/` dentro del repo si los resultados cumplen con los umbrales definidos.


