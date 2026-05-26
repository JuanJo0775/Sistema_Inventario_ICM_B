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
