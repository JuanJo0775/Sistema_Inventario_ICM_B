# Utility Tree del Sistema Inventario ICM

Este Utility Tree prioriza atributos de calidad derivados del backend real del proyecto. Cada escenario tiene métricas concretas y medibles, calificación en formato (Impacto/Dificultad) con escala A/M/B, y justificación del razonamiento.

## Escala de calificación

| Nivel | Impacto | Dificultad |
|:---:|---|---|
| **A** | Si falla, el sistema falla o el negocio se detiene | Requiere patrones complejos, sincronización o infraestructura especial |
| **M** | Degrada la experiencia pero no bloquea el negocio | Implementable con patrones conocidos pero requiere cuidado |
| **B** | Afecta secundariamente, tiene workaround | Sencillo de implementar con el stack actual |

## Vista general

```
Utilidad del Sistema ICM
├── Atributo 1: Disponibilidad
│   ├── Escenario 1.1: Uptime ≥ 99.5% en jornada operativa              → (A, A)
│   └── Escenario 1.2: 20 usuarios concurrentes en inicio de jornada     → (A, M)
├── Atributo 2: Rendimiento
│   ├── Escenario 2.1: Consulta de stock < 500ms con 50 usuarios         → (A, M)
│   ├── Escenario 2.2: Registro de movimiento < 1s con atomicidad        → (A, A)
│   └── Escenario 2.3: Reporte KPI mensual < 3s con 10.000 movimientos   → (M, M)
├── Atributo 3: Seguridad e Integridad
│   ├── Escenario 3.1: RBAC 100% de cobertura de endpoints               → (A, B)
│   ├── Escenario 3.2: AuditLog completamente inmutable                   → (A, A)
│   └── Escenario 3.3: Restricción horaria aplicada por request          → (A, M)
├── Atributo 4: Mantenibilidad
│   ├── Escenario 4.1: Nuevo tipo de movimiento sin modificar otras apps  → (M, M)
│   └── Escenario 4.2: Onboarding de desarrollador nuevo en < 2 días     → (M, B)
└── Atributo 5: Consistencia de Datos
    └── Escenario 5.1: Stock exacto bajo concurrencia, sin stock negativo → (A, A)
```

---

## Atributo 1: Disponibilidad

**Prioridad:** Alta — toda la operación logística depende de la disponibilidad del sistema en jornada laboral.

| # | Escenario (métrica concreta) | Calificación | Justificación |
|---|---|:---:|---|
| 1.1 | El sistema permanece operativo durante toda la jornada laboral (07:00–17:00) con uptime ≥ 99.5%. Ante una caída, se recupera en menos de 5 minutos sin intervención manual. | **(A, A)** | **Impacto A:** Un almacén sin acceso paraliza recepciones, despachos y reportes. Toda la operación logística depende de este servicio. **Dificultad A:** Requiere health checks en Docker Compose, entrypoint con reintentos automáticos (`docker/entrypoint.sh`), estrategia de reinicio definida y vigilancia de PostgreSQL. No hay HA distribuida en este alcance. |
| 1.2 | Durante el pico de operación (inicio de jornada, lunes 07:00), el sistema soporta 20 usuarios concurrentes con tiempo de respuesta < 800ms y sin errores 5xx. | **(A, M)** | **Impacto A:** El inicio de jornada es el momento de mayor actividad; una caída en ese momento bloquea el arranque del día. **Dificultad M:** Manejable con índices correctos, connection pooling de PostgreSQL y configuración de workers en gunicorn/Django. No requiere microservicios ni balanceo horizontal en esta fase. |

**Decisión arquitectónica vinculada:** El uso de Docker Compose con health checks (`depends_on: condition: service_healthy`) y el entrypoint con espera de PostgreSQL documentado en `docker/entrypoint.sh` responden directamente al escenario 1.1. Referencia: ADR-008, ADR-012.

---

## Atributo 2: Rendimiento

**Prioridad:** Media-Alta — las operaciones de stock y registro de movimientos son el cuello de botella operativo del sistema.

| # | Escenario (métrica concreta) | Calificación | Justificación |
|---|---|:---:|---|
| 2.1 | La consulta de stock actual por ubicación (`GET /api/v1/inventory/`) responde en menos de 500ms con 50 usuarios simultáneos en condiciones normales de operación. | **(A, M)** | **Impacto A:** Es la operación más frecuente del sistema y el corazón del negocio. Un retraso sostenido paraliza las decisiones de despacho en tiempo real. **Dificultad M:** Requiere índices en `StockByLocation (product, location)`, uso de `selectors.py` con queries optimizadas, paginación y evitar N+1. No requiere caché distribuido en esta fase. |
| 2.2 | El registro de un movimiento de entrada (`POST /api/v1/movements/entry/`) completa la transacción en menos de 1 segundo, incluyendo validación de todas las BR aplicables, actualización de stock y registro en AuditLog. | **(A, A)** | **Impacto A:** Un movimiento lento bloquea la cola de recepción física. Si supera 1s bajo carga, los auxiliares experimentan timeouts y reintentos que generan duplicados. **Dificultad A:** La transacción atómica (`@transaction.atomic`) con `select_for_update()`, validación encadenada de BR-04/BR-09/BR-10/BR-11 y escritura simultánea en `Movement` + `StockByLocation` + `AuditLog` es la operación más compleja del sistema. |
| 2.3 | La generación de un reporte KPI mensual (`GET /api/v1/reports/`) se completa en menos de 3 segundos para hasta 10.000 movimientos en el período consultado. | **(M, M)** | **Impacto M:** Los reportes se consultan con menor frecuencia y tienen más tolerancia de latencia que el stock. Una degradación no bloquea la operación inmediata. **Dificultad M:** Requiere agregaciones en BD (no en Python), índices en `Movement (fecha, tipo, product)` y uso correcto de `reports/selectors.py`. Implementable sin workers async en esta fase. |

**Decisión arquitectónica vinculada:** El patrón `selectors.py` separado de `views.py`, los índices declarados en modelos y el uso de `select_for_update()` en escrituras críticas responden directamente a estos escenarios. Referencia: ADR-002, ADR-003.

---

## Atributo 3: Seguridad e Integridad

**Prioridad:** Alta — la API expone operaciones sensibles de inventario y datos de clientes; un acceso indebido compromete la operación y la confianza en el sistema.

| # | Escenario (métrica concreta) | Calificación | Justificación |
|---|---|:---:|---|
| 3.1 | Todos los endpoints verifican identidad JWT y aplican RBAC. Un usuario con rol `auxiliar_despacho` que intenta acceder a gestión de usuarios (`POST /api/v1/auth/users/`) recibe 403 Forbidden en el 100% de los intentos, sin excepción. | **(A, B)** | **Impacto A:** Una brecha en el control de acceso puede comprometer datos de clientes y la integridad del inventario. Es un requisito innegociable del negocio. **Dificultad B:** DRF + `simplejwt` + permisos por clase en cada view es un patrón bien establecido en Django. La complejidad es de configuración y consistencia, no de innovación técnica. |
| 3.2 | El historial de movimientos y el AuditLog son completamente inmutables. Cualquier intento de `PUT`, `PATCH` o `DELETE` sobre un `Movement` existente devuelve 405 o 403, independientemente del rol del usuario. Esto aplica al 100% de los movimientos, incluyendo los del propio almacenista. | **(A, A)** | **Impacto A:** La inmutabilidad del ledger es la garantía de auditoría y la base legal del sistema (BR-10). Si un movimiento puede modificarse, toda la trazabilidad pierde validez. **Dificultad A:** Requiere guardas en múltiples capas (model-level, service-level y view-level), tests explícitos de intentos de violación y disciplina de equipo para no romper el invariante en features futuras. |
| 3.3 | Un `auxiliar_despacho` con sesión activa que intenta operar fuera de la ventana 07:00–12:00 / 14:00–17:00 (America/Bogota) recibe 403 en el siguiente request, sin necesidad de re-login. La restricción se evalúa en cada request, no solo en login. | **(A, M)** | **Impacto A:** La restricción horaria (BR-03) es un requisito explícito del negocio que afecta la seguridad operativa. Una operación fuera de horario no debería poder ejecutarse. **Dificultad M:** Requiere middleware de validación horaria (`shared/permissions.py: IsWithinOperatingHours`) aplicado a todos los endpoints sensibles, con `timezone.now()` en `America/Bogota`. No trivial pero bien acotado en código. |

**Decisión arquitectónica vinculada:** La separación de `permissions.py` por app, `shared/permissions.py` con `IsWithinOperatingHours` y la arquitectura de `AuditLog` inmutable (sin endpoints de mutación) responden a estos escenarios. Referencia: ADR-004, ADR-007, ADR-005.

---

## Atributo 4: Mantenibilidad

**Prioridad:** Alta — la arquitectura modular solo aporta valor si se preserva a medida que el sistema evoluciona.

| # | Escenario (métrica concreta) | Calificación | Justificación |
|---|---|:---:|---|
| 4.1 | Agregar un nuevo tipo de movimiento (ej. "préstamo temporal") requiere cambios solo en `movements/models.py`, `movements/services.py` y su test, sin modificar views de otras apps ni el módulo de auditoría. El número de archivos modificados es ≤ 6. | **(M, M)** | **Impacto M:** El sistema necesita evolucionar con nuevos tipos de operaciones logísticas, pero cambios mal contenidos pueden romper módulos estables. Un error aquí no detiene la operación actual, pero genera deuda técnica. **Dificultad M:** Requiere la separación estricta de capas aplicada: lógica solo en `services.py`, sin reglas de negocio en `views.py` ni `serializers.py` (principio CRÍTICO documentado en README_ARQUITECTURA). |
| 4.2 | Un desarrollador nuevo puede completar onboarding técnico (entender la arquitectura, ejecutar la suite de tests, realizar su primer PR revisado) en menos de 2 días hábiles usando solo la documentación del repositorio. | **(M, B)** | **Impacto M:** La rotación de equipo es real en proyectos universitarios; una arquitectura incomprensible paraliza al nuevo integrante. **Dificultad B:** Requiere docstrings con referencias a RF/BR, README claro con instrucciones de setup y OpenAPI actualizado. No tiene complejidad técnica, solo disciplina editorial. |

**Decisión arquitectónica vinculada:** La estructura modular por dominio (monolito modular), la separación estricta de capas y el requerimiento de docstrings con referencias a RF/BR responden a estos escenarios. Referencia: ADR-001, ADR-002.

---

## Atributo 5: Consistencia de Datos

**Prioridad:** Alta — el stock incorrecto es el fallo más grave posible en un sistema de inventario.

| # | Escenario (métrica concreta) | Calificación | Justificación |
|---|---|:---:|---|
| 5.1 | Bajo concurrencia (dos usuarios registrando movimientos sobre el mismo producto/ubicación simultáneamente), el stock resultante es exactamente la suma algebraica de ambas operaciones. No hay pérdida de actualizaciones, stock negativo ni inconsistencias entre `Movement` y `StockByLocation`. Verificable en 1.000 operaciones concurrentes con 0 inconsistencias. | **(A, A)** | **Impacto A:** Un stock incorrecto es el fallo más grave de un sistema de inventario. Compromete despachos, alertas, reportes y decisiones gerenciales. El error es silencioso: puede pasar desapercibido hasta que el stock físico no coincide con el digital. **Dificultad A:** Requiere `select_for_update()` en lecturas que preceden escrituras, `@transaction.atomic` en todos los servicios que alteren stock, constraint `CHECK (quantity >= 0)` en BD y tests de concurrencia sobre PostgreSQL real (no SQLite). Es la invariante más compleja del sistema. |

**Decisión arquitectónica vinculada:** El uso de transacciones atómicas, `select_for_update()` y el constraint de stock no negativo en PostgreSQL son la respuesta directa. El ledger inmutable (`Movement`) como fuente de verdad garantiza la reconstrucción del stock ante cualquier inconsistencia detectada. Referencia: ADR-003, ADR-005.

---

## Tabla de prioridad general (resumen)

| Atributo | Prioridad | Escenarios críticos (A, A) | Motivo de priorización |
|---|:---:|---|---|
| Disponibilidad | Alta | 1.1 | Sin disponibilidad en jornada no hay operación logística. |
| Rendimiento | Alta | 2.2 | El registro de movimientos es el cuello de botella transaccional. |
| Seguridad e Integridad | Alta | 3.2 | La inmutabilidad del ledger es la garantía legal y operativa del sistema. |
| Mantenibilidad | Alta | — (ninguno A,A) | La separación de capas es el mecanismo de evolución segura del sistema. |
| Consistencia de Datos | Alta | 5.1 | Stock incorrecto invalida todo el inventario. |

---

## Identificación del Driver Más Crítico

**Driver más crítico: DF-02 / Escenarios 2.2 + 5.1 — Registro transaccional de movimientos con consistencia de stock**

**Calificación combinada: (A, A)**

**Justificación:**

Este es el driver más crítico del sistema ICM porque concentra el mayor número de factores de riesgo simultáneos:

1. **Es el flujo de negocio central:** sin el registro de movimientos, no existe inventario. Cada despacho, recepción, traslado y ajuste pasa por este driver.
2. **Su fallo en consistencia invalida todo el sistema:** un stock incorrecto no solo afecta un reporte; compromete decisiones de compra, despacho y auditoría en cascada.
3. **Afecta 5 módulos simultáneamente:** `movements`, `inventory`, `catalog`, `audit` y (en despachos) `reports`. No hay otro driver con este nivel de impacto transversal.
4. **Es técnicamente el más complejo:** atomicidad + locks de fila + múltiples validaciones BR encadenadas + escritura en tres tablas en una sola transacción + constraint de stock no negativo.
5. **Tiene el mayor riesgo de error silencioso:** un bug de concurrencia puede generar stock incorrecto que solo se detecta días después al hacer un inventario físico.

**Decisión arquitectónica exacta que implica:**

> *"El servicio `movements.services.register_entry()` (y sus equivalentes para salida, traslado, ajuste y devolución) DEBE ejecutarse siempre dentro de una transacción atómica (`@transaction.atomic`) que incluya: validación de todas las BR aplicables al tipo de movimiento, adquisición de lock con `select_for_update()` sobre `StockByLocation`, actualización del stock derivado, creación del registro `Movement` y registro en `AuditLog`. Ninguna de estas operaciones puede ocurrir fuera de esta transacción ni en orden diferente."*

Este requerimiento justifica directamente: la elección de PostgreSQL (ADR-003, soporte nativo de transacciones ACID), la separación en `services.py` (ADR-002, para aislar la complejidad transaccional del I/O HTTP) y el patrón de ledger inmutable (ADR-005, para garantizar la reconstrucción del stock desde el historial).

---

## Relación con documentación existente

- [docs/calidad_restricciones/README_ATRIBUTOS_CALIDAD.md](../calidad_restricciones/README_ATRIBUTOS_CALIDAD.md) — atributos con métricas posibles y escenarios ISO 25010.
- [docs/architecture/architecture_drivers.md](architecture_drivers.md) — drivers funcionales priorizados (incluyendo DF-01 a DF-06).
- [docs/architecture/adr_relationships.md](adr_relationships.md) — trazabilidad Driver → Táctica → ADR.
- [docs/architecture/architectural_constraints.md](architectural_constraints.md) — restricciones que limitan las opciones arquitectónicas.
