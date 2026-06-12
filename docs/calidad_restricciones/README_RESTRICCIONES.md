# README de Restricciones - Sistema Inventario ICM

Este documento consolida las restricciones reales del backend ICM derivadas del codigo, los settings, los ADRs, Docker y la documentacion funcional. No es una lista generica: cada restriccion tiene evidencia en el repositorio y afecta decisiones de diseno, despliegue u operacion.

## Fuentes de verdad

- [docs/README_ARQUITECTURA.md](../README_ARQUITECTURA.md)
- [docs/api/README_API.md](../api/README_API.md)
- [docs/adr/README_ADR.md](../adr/README_ADR.md)
- [config/settings/base.py](../config/settings/base.py)
- [config/settings/development.py](../config/settings/development.py)
- [config/settings/production.py](../config/settings/production.py)
- [config/settings/test.py](../config/settings/test.py)
- [docker/Dockerfile](../docker/Dockerfile)
- [docker-compose.yml](../docker-compose.yml)
- [docker-compose.prod.yml](../docker-compose.prod.yml)

## 1. Restricciones arquitectónicas

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| Monolito modular por dominio, no microservicios | Tecnológica | ADR-001, docs/README_ARQUITECTURA.md | Define el límite del sistema y evita orquestación distribuida prematura | Acoplamiento interno si no se respeta la frontera por app | Menor complejidad operacional a cambio de escalado horizontal limitado | `apps/*`, `config/` |
| La lógica de negocio vive en `services.py` | Tecnológica | ADR-002, docs/README_ARQUITECTURA.md | Impide reglas de dominio en `models.py`, `serializers.py` o `views.py` | Mezclar capas rompe testabilidad y trazabilidad | Más disciplina de diseño a cambio de mantenimiento más simple | `services.py`, `views.py`, `serializers.py`, `models.py` |
| El stock se deriva del ledger | Tecnológica | ADR-005, docs/README_ARQUITECTURA.md | No se permite actualizar stock directamente fuera del movimiento | Inconsistencias si alguien salta el flujo de movimiento | Consistencia fuerte a cambio de más transacciones | `movements`, `inventory` |
| La API pública vive solo en `/api/v1/` | Tecnológica | ADR-006, docs/api/README_API.md | Cualquier cambio incompatible obliga a versionar | Romper consumidores si se publican cambios sin nueva versión | Evolución controlada a cambio de más mantenimiento de versiones | `config/urls.py`, vistas API |

## 2. Restricciones tecnologicas

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| PostgreSQL es la unica BD soportada en desarrollo y produccion | Tecnológica | ADR-003, `config/settings/base.py` | Condiciona migraciones, locks y transacciones | Portar a otro motor rompe `select_for_update()` y constraints | ACID y concurrencia real a cambio de mayor dependencia de infraestructura | `DATABASES`, migraciones, servicios de inventario |
| JWT Bearer es el mecanismo de autenticacion | Tecnológica | ADR-004, `config/settings/base.py`, `README_API.md` | Limita la integracion a clientes que manejen tokens | Exposicion si el token se filtra o se reutiliza mal | Simplicidad de integración a cambio de manejo cuidadoso de expiración/refresh | `rest_framework_simplejwt`, frontends consumidores |
| Solo se usan tags OpenAPI oficiales | Tecnológica | `shared/openapi.py`, `README_API.md` | Evita desorden en Swagger y colisiones semanticas | Documentacion incoherente si alguien inventa tags nuevos | Gobierno central del contrato a cambio de menos flexibilidad local | Vistas y serializers documentados |
| No se adopta Kubernetes en este alcance | Organizacional | ADR-008 | Limita el despliegue a Docker Compose | Escalado y HA mas limitados | Menor complejidad operativa a cambio de menos elasticidad | Infraestructura, despliegue |

## 3. Restricciones operativas

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| El auxiliar de despacho solo opera en 07:00-12:00 y 14:00-17:00 America/Bogota | Organizacional | BR-03, `shared/permissions.py`, `config/settings/base.py` | Bloquea autenticacion y requests fuera de ventana | Errores si el reloj del servidor o la zona horaria son incorrectos | Seguridad operativa a cambio de menos flexibilidad horaria | Permisos, login, servicios de movimientos |
| Los movimientos y la auditoria son inmutables | Organizacional | BR-10, docs/README_ARQUITECTURA.md | No existen PUT/PATCH/DELETE para correcciones del ledger | Tocar el historico rompe trazabilidad | Auditoria fuerte a cambio de mayor complejidad de correccion | `movements`, `audit` |
| Las recepciones confirmadas son inmutables y no cancelables | Organizacional | BR-019, BR-021, ADR-014 | Una recepción CONFIRMADA no puede cancelarse ni editarse; su Movement.unit_cost queda congelado | Si se recibe mercancía errónea, se debe generar un ajuste de inventario; no existe rollback | Consistencia del ledger a cambio de mayor fricción operativa ante errores | `purchasing`, `movements` |
| Una OC no puede cancelarse si tiene recepciones confirmadas | Organizacional | BR-020, ADR-014 | `cancel_purchase_order()` bloquea la cancelación si existe Reception en CONFIRMADA | OC queda bloqueada si el almacenista no gestiona las recepciones antes de cancelar | Control de integridad a cambio de flujo de cancelación más restrictivo | `purchasing/services.py` |
| La correccion de movimientos depende de ventana temporal | Organizacional | BR-06, issue P1-02 | Corrige solo dentro de la franja permitida | Rechazos fuera de ventana generan soporte manual | Control de errores a tiempo a cambio de mas restricciones operativas | `movements.services`, permisos |
| CI/CD versionado en `.github/workflows/ci.yml` | Tecnológica | `.github/workflows/ci.yml` (7 jobs: quality, unit, integration, scenarios, seed, concurrency, load) | Pipeline automatizado con gates de calidad | Jobs pueden fallar por tests frágiles o dependencias externas | Automatización a cambio de mantenimiento continuo del pipeline | Flujo de entrega, calidad |

## 4. Restricciones organizacionales

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| Solo almacenista gestiona credenciales | Organizacional | BR-02, docs/README_ARQUITECTURA.md | Limita quien puede crear, cambiar o deshabilitar usuarios | Bloqueos operativos si el almacenista no esta disponible | Separacion de funciones a cambio de dependencia de un rol | `authentication`, `permissions` |
| Roles del sistema limitados a almacenista, auxiliar_despacho y administrador | Organizacional | README.md, README_API.md, docs/README_ARQUITECTURA.md | Restringe el modelo de permisos y los flujos de trabajo | Ampliar roles exige cambios en permisos, docs y pruebas | Gobernanza clara a cambio de menos flexibilidad | Autenticacion, permisos, UI |
| El NIT de un proveedor es único en todo el sistema | Organizacional | BR-018, ADR-014 | Impide registrar el mismo proveedor dos veces con NITs idénticos (activo o inactivo) | Recuperar un proveedor duplicado requiere limpieza manual de datos | Integridad de maestros a cambio de menos flexibilidad en importaciones masivas | `purchasing/models.py`, `purchasing/services.py` |
| Solo el almacenista opera el módulo de compras en modo escritura | Organizacional | RF-025, ADR-014 | Auxiliar no tiene acceso; Administrador tiene solo lectura (GET) | Bottleneck si el almacenista no está disponible para confirmar recepciones | Control centralizado a cambio de menor autonomía de otros roles | `purchasing/permissions.py`, `purchasing/views.py` |
| El trabajo tecnico debe quedar trazado en ADRs e issues | Organizacional | README.md, docs/adr/README_ADR.md | Obliga a documentar decisiones significativas | Si no se mantiene, la historia tecnica se fragmenta | Menos velocidad puntual a cambio de auditoria de decisiones | Documentacion, proceso de cambio |

## 5. Restricciones regulatorias y de cumplimiento

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| Productos de Electroterapia requieren serial | Regulatoria | BR-04, docs/README_ARQUITECTURA.md | Rechaza entradas/salidas sin serial | Operacion incompleta si el dato no se captura | Trazabilidad y seguridad a cambio de mas validacion | `catalog`, `movements` |
| Datos personales deben tratarse con cuidado | Regulatoria | RNF-006, docs/README_ARQUITECTURA.md | Limita exposicion y acceso a datos de clientes | Riesgo legal si se expone informacion sensible | Cumplimiento y privacidad a cambio de menos visibilidad transversal | `audit`, `reports`, `movements` |

## 6. Restricciones de despliegue e infraestructura

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| El despliegue local y MVP se hace con Docker Compose | Tecnológica | ADR-008, `docker-compose.yml` | El ciclo operativo depende de contenedores | Desalineacion si alguien ejecuta el stack fuera de Compose | Paridad de entorno a cambio de mas consumo local | `docker/`, Compose files |
| Secrets y configuracion via variables de entorno | Tecnológica | ADR-009, `.env.example`, `config/settings/*.py` | No se hardcodean credenciales en codigo | Fugas si se versionan valores reales | Configuracion flexible a cambio de disciplina operativa | settings, despliegue |
| La imagen de produccion depende de dependencias runtime explicitas | Tecnológica | ADR-012, `docker/Dockerfile`, `requirements/production.txt` | `gunicorn` no esta disponible si solo se instala base.txt | Fallo de arranque en produccion | Build mas auditable a cambio de mayor cuidado en packaging | Docker, CI/CD, despliegue |
| No hay estrategia de replicas de lectura | Tecnológica | ADR-003, docs/README_ARQUITECTURA.md | Los reportes compiten con escrituras en la misma BD | Picos de lectura afectan transacciones | Simplicidad inicial a cambio de escalado limitado | PostgreSQL, reportes, inventario |

## 7. Restricciones de rendimiento e integracion

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| Consultas complejas deben optimizarse con `select_related`/`prefetch_related` | Tecnológica | docs/api/README_API.md, docs/README_ARQUITECTURA.md | Limita la forma de implementar listados | N+1 y latencia alta si se ignora | Consultas mas eficientes a cambio de mas complejidad en selectores | `selectors.py`, `views.py` |
| El frontend consume la API y no accede a la BD | Tecnológica | README.md, README_API.md | La integracion queda encapsulada por REST | Acoplamiento accidental si se salta la API | Desacoplamiento limpio a cambio de mayor esfuerzo de API | Frontend, backend |
| Los endpoints deben documentarse con `@extend_schema` | Tecnológica | README_API.md | La documentacion OpenAPI es obligatoria | Swagger incompleto si falta metadata | Contrato claro a cambio de mas trabajo por endpoint | `views.py`, `serializers.py` |

## 8. Restricciones de pruebas y evolución

| Restricción | Clasificación | Evidencia | Impacto | Riesgo | Trade-off | Componentes afectados |
|---|---|---|---|---|---|---|
| La suite de test usa SQLite in-memory y sin throttling | Organizacional | ADR-011, `config/settings/test.py`, docs/test/README_TEST.md | No reproduce la semantica de produccion al 100% | Falsa sensacion de cobertura en locks y limits | Ejecucion rapida a cambio de menor fidelidad | Tests, settings, validaciones de concurrencia |
| El objetivo de testing mezcla unitarios, integracion e invariantes | Organizacional | ADR-011 | Fija la distribucion esperada de cobertura | Desbalance si se concentra todo en un solo nivel | Mejor diagnosibilidad a cambio de mas disciplina | `apps/*/tests`, `tests/ers` |
| La evolucion funcional debe preservar trazabilidad RF/BR/RNF | Organizacional | docs/README_ARQUITECTURA.md, docs/requisitos/ERS_ICM_Requisitos.md | Cambios sin trazabilidad quedan fuera del contrato | Brechas entre codigo y documentacion | Auditoria fuerte a cambio de menos libertad de cambio rapido | Docs, PRs, tests |

## 9. Restricciones de mayor impacto

- PostgreSQL es obligatorio para el runtime real del sistema.
- El ledger de movimientos no se edita: se corrige con nuevos eventos.
- El auxiliar de despacho opera solo en la ventana horaria definida por el negocio.
- La imagen de produccion necesita dependencias runtime explicitas, no solo la base del contenedor.
- La suite de pruebas no es una replica exacta de produccion porque usa SQLite y no activa throttling.

## 10. Relacion con ADRs

- ADR-001 a ADR-009 documentan la mayoria de las restricciones estructurales.
- ADR-011 documenta la estrategia de pruebas y su limite de fidelidad.
- ADR-012 documenta la restriccion de empaquetado de produccion.

## 11. Documentos de síntesis relacionados

- [docs/architecture/architectural_constraints.md](../architecture/architectural_constraints.md) — resumen formal de las restricciones con foco arquitectónico.
- [docs/architecture/adr_relationships.md](../architecture/adr_relationships.md) — trazabilidad de restricciones y drivers hacia ADRs.
- [docs/architecture/architecture_drivers.md](../architecture/architecture_drivers.md) — drivers que estas restricciones condicionan.

Si una nueva restriccion afecta diseno o despliegue, debe agregarse aqui y, si introduce una decision de arquitectura, debe reflejarse en un ADR.

---

## 12. Clasificación formal para Entregable Corte 2 (REST-01 a REST-06)

Esta sección presenta las restricciones más relevantes en el formato requerido por el entregable académico, clasificadas en las tres categorías del modelo: Tecnológica, Organizacional y Regulatoria.

> *"Un buen arquitecto no lucha contra las restricciones. Un sistema elegante dentro de restricciones reales vale más que uno perfecto que nadie puede implementar."* — Santiago Jaramillo López

| ID | Nombre | Tipo | Impacto principal en diseño | ADR vinculado |
|----|--------|:---:|---|---|
| REST-01 | Django + PostgreSQL como stack obligatorio | Tecnológica | Descarta NoSQL, FastAPI/Flask; obliga a ORM Django, ACID y `select_for_update()` | ADR-001, ADR-003 |
| REST-02 | Despliegue exclusivo con Docker Compose | Tecnológica / Organizacional | Descarta Kubernetes, cloud orchestrators y microservicios en esta fase | ADR-008, ADR-001 |
| REST-03 | Equipo pequeño con tiempo acotado | Organizacional | Descarta event sourcing completo, Redis, optimizaciones prematuras; justifica SQLite en tests | ADR-001, ADR-011 |
| REST-04 | Datos on-premise (no cloud público) | Regulatoria | Descarta AWS S3/Firebase para datos transaccionales; obliga despliegue local | ADR-008, ADR-009 |
| REST-05 | API REST HTTP/JSON sin WebSockets | Tecnológica | Descarta dashboards con push en tiempo real; limita alertas a polling | ADR-006 |
| REST-06 | Protección de datos personales — Ley 1581 Colombia | Regulatoria | Restringe exposición de datos de clientes por rol; obliga a auditoría de acceso a datos sensibles | ADR-007 |

**Relación con restricciones existentes en este documento:**

- REST-01 → Secciones 2 (restricciones tecnológicas) y 1 (monolito modular).
- REST-02 → Sección 6 (despliegue e infraestructura: Docker Compose, sin Kubernetes).
- REST-03 → Sección 4 (organizacionales: equipo, roles, decisiones en ADRs) y sección 8 (pruebas con SQLite).
- REST-04 → Sección 6 (despliegue local, sin cloud storage para datos transaccionales).
- REST-05 → Sección 1 (API pública solo en `/api/v1/`) y sección 7 (frontend consume solo la API REST).
- REST-06 → Sección 5 (regulatorias: datos personales de clientes, RNF-006).