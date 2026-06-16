# Trazabilidad entre drivers y ADRs

Este documento conecta los drivers arquitectónicos con el problema que resuelven, la decisión adoptada y el ADR correspondiente.

## Matriz principal

| Driver | Problema | Decisión arquitectónica | ADR |
|---|---|---|---|
| Consistencia e integridad del inventario | Riesgo de stock inconsistente, movimientos concurrentes y correcciones destructivas | Modelar el inventario como ledger inmutable con stock derivado y transacciones ACID | [ADR-005](adr/ADR-005.md), [ADR-003](adr/ADR-003.md) |
| Seguridad y control de acceso | Acceso indebido a datos, gestión de credenciales y operaciones fuera de horario | JWT con access/refresh, blacklist y permisos por rol/horario | [ADR-004](adr/ADR-004.md), [ADR-007](adr/ADR-007.md) |
| Mantenibilidad y modificabilidad | Riesgo de lógica de negocio dispersa y acoplamiento entre capas | Separación estricta en models/serializers/views/services/selectors/permissions | [ADR-002](adr/ADR-002.md) |
| Interoperabilidad API | Integraciones frágiles entre frontend y backend sin contrato estable | API REST versionada bajo `/api/v1/` y documentación OpenAPI | [ADR-006](adr/ADR-006.md) |
| Portabilidad y despliegue reproducible | Diferencias entre equipos y entornos, errores de arranque y dependencias implícitas | Docker Compose, settings por entorno y variables de entorno | [ADR-008](adr/ADR-008.md), [ADR-009](adr/ADR-009.md), [ADR-012](adr/ADR-012.md) |
| Rendimiento de consultas | Latencia alta en stock y reportes por consultas mal diseñadas | Selectores de lectura, agregaciones en BD e índices sobre el dominio crítico | [ADR-003](adr/ADR-003.md), [ADR-011](adr/ADR-011.md) |
| Trazabilidad y auditoría | Falta de evidencia de quién hizo qué y cuándo | Audit log inmutable y eventos por operación significativa | [ADR-001](adr/ADR-001.md), [ADR-005](adr/ADR-005.md) |
| Calidad verificable | Riesgo de regresiones silenciosas en reglas críticas | Estrategia de testing con pytest, factory-boy y niveles de prueba | [ADR-011](adr/ADR-011.md) |

## Lectura por problema

### 1. Integridad del inventario

**Problema:** el inventario puede corromperse si se actualiza el stock sin un movimiento correspondiente o si dos operaciones concurrentes pisan el mismo valor.

**Decisión:** un ledger inmutable como fuente de verdad, stock derivado y transacciones ACID con locks.

**ADRs involucrados:** [ADR-003](adr/ADR-003.md), [ADR-005](adr/ADR-005.md).

### 2. Control de acceso

**Problema:** la API expone operaciones sensibles y el sistema tiene restricciones de rol y horario.

**Decisión:** JWT stateless, RBAC, blacklist, y validación horaria por request.

**ADRs involucrados:** [ADR-004](adr/ADR-004.md), [ADR-007](adr/ADR-007.md).

### 3. Evolución del código

**Problema:** si la lógica de negocio se dispersa, el sistema se vuelve difícil de probar y mantener.

**Decisión:** separar servicios, selectores y permisos del I/O HTTP y de la persistencia.

**ADR involucrado:** [ADR-002](adr/ADR-002.md).

### 4. Contrato de integración

**Problema:** el frontend necesita un contrato estable y versionado.

**Decisión:** API REST `/api/v1/` con OpenAPI y tags centralizados.

**ADR involucrado:** [ADR-006](adr/ADR-006.md).

### 5. Despliegue y entorno

**Problema:** el equipo trabaja en máquinas distintas y el runtime productivo no puede depender de supuestos ocultos.

**Decisión:** Docker Compose, settings por entorno y dependencias runtime explícitas.

**ADRs involucrados:** [ADR-008](adr/ADR-008.md), [ADR-009](adr/ADR-009.md), [ADR-012](adr/ADR-012.md).

## Conclusión

La arquitectura del proyecto no se justifica por capas genéricas, sino por estos drivers reales:

- integridad del inventario,
- control de acceso,
- trazabilidad,
- mantenibilidad,
- contrato REST,
- portabilidad.

Los ADRs ya existentes cubren esas decisiones; este documento solo las conecta para el entregable académico.

---

## Matriz de trazabilidad  — Driver → Táctica → ADR

Esta tabla cumple la regla de trazabilidad de las slides: cada driver aparece en el Utility Tree con calificación, cada escenario tiene una decisión arquitectónica que lo satisface, y cada ADR responde a un driver específico.

**Clasificación de ADRs por corte:**
- **Corte 1:** ADR-001 a ADR-009, ADR-011 (decisiones fundacionales de arquitectura, seguridad, BD y testing).
- **Corte 2:** ADR-010 (facturación PDF con atomicidad), ADR-012 (imagen de producción con dependencias runtime explícitas).

| Driver / Escenario Utility Tree | Calificación | Táctica Arquitectónica | ADR Corte 1 | ADR Corte 2 |
|---|:---:|---|---|---|
| **DF-02** / Escenario 2.2: Registro de movimiento < 1s con atomicidad completa | (A, A) | `@transaction.atomic` + `select_for_update()` en todos los servicios que alteren stock; escritura simultánea en `Movement`, `StockByLocation` y `AuditLog` | ADR-005, ADR-003 | ADR-010 (atomicidad extendida a facturas) |
| Escenario 5.1: Consistencia de stock bajo concurrencia, 0 inconsistencias en 1.000 ops | (A, A) | Constraint `CHECK (quantity >= 0)` en BD + ledger inmutable como única fuente de verdad para stock derivado | ADR-005, ADR-003 | — |
| Escenario 1.1: Uptime ≥ 99.5% en jornada operativa, recuperación < 5 min | (A, A) | Docker Compose con `depends_on: condition: service_healthy` + entrypoint con reintentos automáticos + restart policy | ADR-008 | ADR-012 |
| Escenario 3.2: AuditLog 100% inmutable, `DELETE`/`PUT` devuelven 405/403 | (A, A) | Sin endpoints de mutación sobre `Movement`; guardas en model-level + service-level + view-level; tests de intentos de violación | ADR-005, ADR-002 | — |
| **DF-03** / Escenario 3.1: RBAC 100% de cobertura de endpoints | (A, B) | JWT Bearer + clases de permiso DRF por endpoint + `shared/permissions.py` centralizado | ADR-004, ADR-007 | — |
| **DF-01** / Escenario 2.1: Consulta de stock < 500ms con 50 usuarios | (A, M) | `selectors.py` de solo lectura + índices en `StockByLocation (product, location)` + paginación + sin N+1 | ADR-002, ADR-003 | — |
| Escenario 3.3: Restricción horaria evaluada por request, no solo en login | (A, M) | Middleware `IsWithinOperatingHours` en `shared/permissions.py` con `timezone.now()` en `America/Bogota` aplicado a todos los endpoints sensibles | ADR-007 | — |
| Escenario 1.2: 20 usuarios concurrentes inicio de jornada < 800ms | (A, M) | Connection pooling PostgreSQL + workers gunicorn configurados + índices en tablas de alta lectura | ADR-003, ADR-008 | ADR-012 |
| **DF-05** / Escenario 2.3: Reportes KPI < 3s para 10.000 movimientos | (M, M) | Agregaciones en BD via `reports/selectors.py` + índices en `Movement (fecha, tipo, product)` + separación CQRS parcial | ADR-002, ADR-003 | — |
| **DF-04** / Ajustes y devoluciones con ventana de corrección temporal | — | Correcciones como nuevos eventos (no mutación del ledger) + validación de ventana temporal en `movements/services.py` (BR-06) | ADR-005, ADR-002 | — |
| **DF-06** / Resolución SKU/barcode en despacho (BR-08, BR-12, BR-13) | — | Validación cruzada `scanned_code` vs `order_sku` en `movements/services.py` + generación de barcode en `catalog` | ADR-002, ADR-006 | ADR-010 |
| **REST-02** / Despliegue sin orquestadores cloud (monolito vs. microservicios) | — | Monolito modular sobre Docker Compose; descarta microservicios por restricción de equipo y plazo | ADR-001, ADR-008 | ADR-012 |
| **REST-06** / Protección de datos personales (Ley 1581) | — | RBAC con permisos componibles que restringen exposición de datos de clientes por rol | ADR-007 | *(ADR pendiente de privacidad)* |

### Verificación de completitud de la cadena

Para cada ADR existente se verifica que tenga un driver de origen y escenario en el Utility Tree:

| ADR | Driver de origen | Escenario Utility Tree | Calificación |
|-----|---|---|:---:|
| ADR-001 | REST-02, REST-03 | — (restricción, no escenario de calidad) | — |
| ADR-002 | DF-02, DF-01, DF-05 | 2.2, 2.1, 2.3 | (A,A), (A,M), (M,M) |
| ADR-003 | DF-02, DF-01, 5.1 | 2.2, 2.1, 5.1 | (A,A), (A,M), (A,A) |
| ADR-004 | DF-03 | 3.1 | (A,B) |
| ADR-005 | DF-02, 5.1, 3.2 | 2.2, 5.1, 3.2 | (A,A), (A,A), (A,A) |
| ADR-006 | REST-05, DF-06 | — (restricción tecnológica) | — |
| ADR-007 | DF-03, REST-06 | 3.1, 3.3 | (A,B), (A,M) |
| ADR-008 | REST-02 | 1.1, 1.2 | (A,A), (A,M) |
| ADR-009 | REST-04 | — (restricción regulatoria) | — |
| ADR-010 | DF-02, DF-06 | 2.2 (atomicidad extendida) | (A,A) |
| ADR-011 | REST-03 | — (restricción organizacional) | — |
| ADR-012 | REST-02 | 1.1 | (A,A) |

---

## Ver también

- [design-patterns.md](design-patterns.md) — implementación concreta de los patrones que hacen efectivas estas decisiones (Service Layer, Strategy, Observer, Facade, Composite).
- [solid-principles.md](solid-principles.md) — evidencia de SOLID en el código, alineada con los drivers de mantenibilidad y desacoplamiento (ADR-002).
- [architectural_constraints.md](architectural_constraints.md) — restricciones que condicionan las decisiones anteriores.
- [architecture_drivers.md](architecture_drivers.md) — drivers de los que parten los problemas resueltos por cada ADR.
- [docs/adr/README_ADR.md](../adr/README_ADR.md) — índice completo de ADRs.
