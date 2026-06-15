# Drivers arquitectónicos del Sistema Inventario ICM

Este documento sintetiza los drivers reales que condicionan la arquitectura del backend. No es una lista genérica: cada driver se apoya en el código, la configuración, los ADRs y la documentación viva del repositorio.

## 1. Driver dominante

**Driver dominante:** consistencia e integridad transaccional del inventario.

### Por qué domina

- El sistema modela el inventario como un **ledger inmutable** (`Movement`) con **stock derivado** (`StockByLocation`).
- Las operaciones críticas escriben datos relacionados en una sola transacción.
- La concurrencia en despacho, traslados y ajustes exige `select_for_update()` y PostgreSQL.
- La trazabilidad y la auditoría dependen de que el historial no se modifique.

### Decisiones que provoca

- Monolito modular por dominio.
- Lógica de negocio concentrada en `services.py`.
- PostgreSQL como motor único soportado en runtime real.
- Movimientos inmutables y corrección por nuevos eventos.
- Pruebas centradas en invariantes del ledger.

## 2. Drivers funcionales priorizados

| Prioridad | Driver funcional | Descripción | Impacto | Componentes afectados | Decisiones derivadas |
|---|---|---|---|---|---|
| 1 | Inventario consistente | Registrar entradas, salidas, traslados, devoluciones y ajustes sin romper el stock derivado | Alto | `apps/movements/`, `apps/inventory/`, `shared/exceptions.py`, PostgreSQL | Ledger inmutable, atomicidad, locks y reconstrucción desde ledger |
| 2 | Control de acceso seguro | Autenticar usuarios y restringir acciones por rol y horario | Alto | `apps/authentication/`, `shared/permissions.py`, `apps/audit/`, `config/settings/` | JWT, RBAC, blacklist, validación horaria por request |
| 3 | Trazabilidad operacional | Saber quién hizo qué, cuándo y sobre qué entidad | Alto | `apps/audit/`, `apps/movements/`, `apps/authentication/` | Audit log inmutable, `executed_by`, eventos significativos |
| 4 | Gestión de catálogo confiable | Mantener productos, categorías, subcategorías, combos y SKU definidos por usuario | Alto | `apps/catalog/`, `shared/utils/validators.py` | Validación de SKU, reglas de serial y retornabilidad |
| 5 | Consulta de stock y reportes | Exponer lecturas rápidas y consistentes para operación y análisis | Medio | `apps/inventory/`, `apps/reports/`, `selectors.py` | Selectores de solo lectura, agregaciones en BD, paginación |
| 6 | Despliegue reproducible | Levantar el sistema de forma consistente entre equipos y entornos | Medio | `docker/`, `docker-compose*.yml`, `requirements/`, `config/settings/` | Docker Compose, variables de entorno, settings por entorno |
| 7 | Evidencia de calidad y pruebas | Validar reglas críticas sin perder trazabilidad documental | Medio | `tests/`, `apps/*/tests/`, `docs/test/` | pytest, factories, documentación viva de pruebas |

## 3. Drivers de calidad relevantes

| Driver | Prioridad | Justificación | ADRs vinculados |
|---|:---:|---|---|
| Consistencia e Integridad Transaccional | Alta | El ledger inmutable (`Movement`) y el stock derivado (`StockByLocation`) deben permanecer coherentes bajo concurrencia. Cualquier divergencia compromete la validez de todo el inventario: stock incorrecto impacta recepciones, despachos, reportes y decisiones gerenciales en cascada. `@transaction.atomic` y `select_for_update()` son las tácticas implementadas. | ADR-003, ADR-005 |
| Seguridad y Control de Acceso | Alta | La API expone operaciones críticas sobre inventario, usuarios y datos de auditoría. El RBAC con tres roles (almacenista, auxiliar_despacho, administrador) y la restricción horaria (BR-03, ventana 07:00–17:00) deben evaluarse en cada request. Un fallo en la cadena de permisos puede conceder acceso indebido a operaciones que alteran el estado del sistema o exponen datos sensibles. | ADR-004, ADR-007 |
| Mantenibilidad | Alta | La separación estricta de capas (models → serializers → views → services → selectors → permissions) es la táctica que permite evolucionar el sistema por dominio sin propagar cambios entre apps. Si la lógica de negocio migra a `views.py` o `serializers.py`, el acoplamiento aumenta y los cambios dejan de estar contenidos. Umbral observable: ≤ 6 archivos y ≤ 2 apps modificadas por cambio funcional aislado. | ADR-001, ADR-002 |
| Rendimiento | Media | El sistema atiende jornadas con hasta 50 usuarios concurrentes. Las operaciones críticas tienen umbrales operativos definidos: consulta de stock (p95 < 500ms), registro de movimiento (< 1s), reporte KPI (< 3s con 10.000 movimientos). Los selectores de solo lectura (`selectors.py`) y los índices compuestos son las tácticas implementadas. | ADR-002, ADR-003 |
| Disponibilidad | Media | El sistema es un monolito contenerizado sin alta disponibilidad distribuida (REST-02). La disponibilidad se sustenta en health checks de Docker Compose, política de reinicio automático y entrypoint con verificación de migraciones. Objetivo: uptime ≥ 99.5% en jornada operativa (07:00–17:00); recuperación ante caída < 5 minutos. | ADR-008, ADR-012 |
| Observabilidad y Auditabilidad | Media | El sistema implementa `AuditLog` inmutable como mecanismo primario de trazabilidad operativa, requerido por la Ley 1581 y las reglas de negocio (BR-10). La observabilidad técnica (logs estructurados, métricas de latencia, trazas distribuidas) se encuentra en madurez baja y constituye la principal deuda técnica del sistema. Objetivo: 100% de operaciones críticas auditadas; consulta de historial < 2s para 30 días. | ADR-005 |

> **Referencia completa:** Los escenarios ATAM formales de cada driver —con Fuente del Estímulo, Estímulo, Entorno, Artefacto, Respuesta Esperada y Medida de Respuesta— están documentados en [docs/architecture/utility_tree.md § Tabla ATAM de Drivers de Calidad](utility_tree.md#tabla-atam-de-drivers-de-calidad).

## 4. Componentes más condicionados por los drivers

- `apps/movements/services.py`: núcleo de consistencia, concurrencia e inmutabilidad.
- `apps/authentication/services.py`: autenticación, restricción horaria, revocación y trazabilidad.
- `apps/catalog/services.py`: validación de SKU, categorías y catálogo operativo.
- `apps/inventory/services.py` y `selectors.py`: stock derivado, reconstrucción y consultas de lectura.
- `apps/audit/services.py`: trazabilidad inmutable.
- `shared/permissions.py`: RBAC y control horario.
- `config/settings/*.py`: seguridad, JWT, base de datos y comportamiento por entorno.
- `docker-compose*.yml` y `docker/Dockerfile`: portabilidad y despliegue.

## 5. Lectura ejecutiva

Si este sistema cambia, lo más probable es que cambie primero uno de estos ejes:

1. reglas de inventario,
2. seguridad y acceso,
3. trazabilidad,
4. contrato REST,
5. despliegue reproducible.

Eso explica por qué la arquitectura favorece servicios transaccionales, permisos explícitos, auditoría y documentación viva.

---

## 6. Drivers funcionales con identificador formal

Esta sección formaliza los drivers funcionales con el criterio de la clase: un RF es driver si su cambio obliga a rediseñar componentes múltiples, si su falla detiene el propósito central del sistema o si afecta múltiples módulos o capas simultáneamente.

### Criterio de selección aplicado

De los 12 RF documentados en el ERS, solo los siguientes 6 cumplen el umbral de driver. Los demás son requisitos de soporte (validaciones aisladas, configuraciones de UI, exportaciones secundarias).

| ID | Driver Funcional | RF asociado | Por qué ES driver y no solo requisito |
|----|-----------------|-------------|---------------------------------------|
| DF-01 | Consulta de stock en tiempo real por ubicación | RF-004 | Define la estrategia completa de acceso a datos. Si el modelo de stock cambia (ej. agregar subdivisiones o múltiples ubicaciones), impacta `inventory`, `movements`, `reports` y `audit` simultáneamente. Sin este driver no existe un inventario consultable. |
| DF-02 | Registro de movimientos con trazabilidad inmutable | RF-005, RF-006, RF-007 | Es el núcleo transaccional del sistema. Define el modelo de datos central (ledger inmutable), las reglas de atomicidad y la arquitectura de auditoría. Si este driver falla o se relaja, todo el inventario pierde validez. Afecta `movements`, `inventory`, `audit` y `catalog` en cada operación. |
| DF-03 | Control de acceso por 4 roles con restricción horaria | RF-001, RF-002 | Define la arquitectura completa de autenticación y autorización (JWT + RBAC + middleware horario en `shared/permissions.py`). Afecta cada endpoint del sistema. Cambiarlo implicaría rediseñar la cadena de seguridad de extremo a extremo. |
| DF-04 | Ajustes y devoluciones con ventana de corrección temporal | RF-008, RF-009 | Define la política de inmutabilidad con excepción controlada (BR-06). Obliga a lógica especial en `movements/services.py` para distinguir correcciones válidas de manipulaciones. Afecta `movements`, `audit` y las reglas de negocio de servicios. |
| DF-05 | Generación de reportes e indicadores KPI | RF-010 | Define la estrategia de lectura separada (`selectors.py`, agregaciones en BD) y el patrón CQRS parcial del sistema. Si los reportes crecen en complejidad, obliga a rediseñar la capa de lectura sin tocar la capa de escritura. |
| DF-06 | Resolución y validación de identificadores de producto (SKU/barcode) | RF-003, RF-006 | Define el flujo de validación cruzada en despacho (BR-08, BR-12, BR-13). Un cambio en el modelo de identificación impacta catálogo, movimientos y facturación. Es el driver que conecta el mundo físico (código de barras escaneado) con el modelo de datos. |

### Justificaciones extendidas

**DF-01 — Consulta de stock por ubicación**
Si este driver cambia (ej. el negocio exige stock por sub-zona o por lote), no solo cambia el endpoint `GET /api/v1/inventory/`; obliga a rediseñar el modelo `StockByLocation`, las migraciones, los selectores de lectura, los reportes y cualquier vista que muestre stock. Esto afecta al menos 4 apps del sistema. Es driver porque es la fuente de verdad operativa que todas las demás capas consumen.

**DF-02 — Registro de movimientos inmutable**
Este driver define el corazón del sistema: el ledger. Si se relaja la inmutabilidad (ej. permitir editar un movimiento pasado), se invalida el AuditLog, los reportes históricos, las reconstrucciones de stock y la confianza legal en el sistema. Técnicamente obliga a `@transaction.atomic`, `select_for_update()`, constraints en BD y un diseño de correcciones por nuevos eventos. Es el driver de mayor impacto transversal.

**DF-03 — Control de acceso RBAC + horario**
Cada endpoint del sistema pasa por la capa de permisos. Si se agrega un nuevo rol, se cambia la ventana horaria o se modifica el mecanismo de autenticación, el impacto recorre desde el middleware hasta los serializers. No es un módulo aislado: es un corte transversal que condiciona toda la arquitectura REST.

**DF-04 — Ajustes y devoluciones con ventana temporal**
La regla BR-06 define que ciertos movimientos pueden corregirse solo dentro de una ventana de tiempo. Esto introduce lógica de tiempo en `services.py` que va más allá de validar datos de entrada. Si la ventana cambia o se elimina, la arquitectura de correcciones (actualmente basada en nuevos eventos) necesitaría revisarse. Afecta negocio, auditoría y permisos.

**DF-05 — Reportes KPI**
Los reportes no son solo consultas SQL. Definen una capa de lectura separada (`reports/selectors.py`) con agregaciones en base de datos, índices específicos y, en un futuro, posibilidad de réplica de lectura. Si los KPIs cambian significativamente, la estrategia de consulta y los índices deben evolucionar. Es driver porque define la frontera entre el modelo OLTP y el modelo de análisis.

**DF-06 — Resolución SKU/barcode**
En el flujo de despacho, el sistema recibe un código escaneado (`scanned_code`) y debe validarlo contra el SKU del pedido (`order_sku`) según reglas complejas (BR-08, BR-12, BR-13). Si el esquema de identificación cambia (ej. agregar RFID o cambiar formato de barcode), impacta el catálogo, el flujo de despacho y la validación de facturas. Es driver porque es el punto de entrada del mundo físico al sistema digital.

---

## Ver también

- [design-patterns.md](design-patterns.md) — implementación concreta de los patrones que hacen efectivos estos drivers (Service Layer para DF-02, Strategy para DF-03, Observer para eventos de dominio, Facade para concurrencia segura).
- [solid-principles.md](solid-principles.md) — cómo los principios SOLID traducen los drivers de mantenibilidad (SRP, OCP, DIP) y escalabilidad (ISP) a código real.
- [adr_relationships.md](adr_relationships.md) — matriz que conecta cada driver con el ADR que lo resuelve.
- [architectural_constraints.md](architectural_constraints.md) — restricciones derivadas de estos drivers.
- [docs/adr/README_ADR.md](../adr/README_ADR.md) — decisiones arquitectónicas formales.
