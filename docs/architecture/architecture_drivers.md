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

| Driver | Prioridad | Justificación |
|---|---|---|
| Seguridad | Alta | La API expone operaciones sensibles de inventario, usuarios y auditoría; un acceso indebido compromete datos y operación. |
| Consistencia / integridad | Alta | El stock incorrecto impacta directamente recepción, despacho, reportes y decisiones operativas. |
| Mantenibilidad | Alta | La arquitectura evoluciona por dominios y necesita cambios aislados sin mezclar reglas en vistas o serializers. |
| Rendimiento | Medio | El volumen actual es moderado, pero reportes y consultas de stock deben mantenerse ágiles. |
| Disponibilidad | Medio | El sistema es monolítico y no está diseñado para alta disponibilidad distribuida en este alcance. |
| Observabilidad | Medio | Existe auditoría y logging, pero todavía no hay un stack completo de métricas y trazas distribuidas. |

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
