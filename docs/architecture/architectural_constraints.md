# Restricciones arquitectónicas formales

Este documento resume las restricciones reales que condicionan el diseño del backend ICM. Complementa [docs/calidad_restricciones/README_RESTRICCIONES.md](calidad_restricciones/README_RESTRICCIONES.md) con una lectura más orientada a drivers y decisiones.

## 1. Restricciones estructurales

| Restricción | Tipo | Evidencia | Efecto arquitectónico |
|---|---|---|---|
| Monolito modular por dominio | Estructural | [docs/adr/ADR-001.md](adr/ADR-001.md) | Evita microservicios y favorece límites por app. |
| Negocio solo en `services.py` | Estructural | [docs/README_ARQUITECTURA.md](README_ARQUITECTURA.md) | Obliga a desacoplar reglas de dominio de HTTP y serialización. |
| Lecturas complejas en `selectors.py` | Estructural | [docs/README_ARQUITECTURA.md](README_ARQUITECTURA.md) | Separa consultas de lectura de la lógica transaccional. |
| `Movement` como fuente de verdad | Estructural | [docs/README_ARQUITECTURA.md](README_ARQUITECTURA.md) | Impone inmutabilidad y reconstrucción del stock derivado. |

## 2. Restricciones tecnológicas

| Restricción | Tipo | Evidencia | Efecto arquitectónico |
|---|---|---|---|
| PostgreSQL 18 es la BD soportada en runtime real | Tecnológica | [docs/adr/ADR-003.md](adr/ADR-003.md) | Habilita ACID, `select_for_update()` y constraints fuertes. |
| JWT Bearer es el mecanismo de autenticación | Tecnológica | [docs/adr/ADR-004.md](adr/ADR-004.md) | El API es stateless y depende de tokens con expiración y blacklist. |
| API versionada bajo `/api/v1/` | Tecnológica | [docs/adr/ADR-006.md](adr/ADR-006.md) | Cualquier cambio incompatible exige nueva versión. |
| Tags OpenAPI centralizados | Tecnológica | [docs/api/README_API.md](api/README_API.md) | Evita divergencias en documentación y Swagger. |

## 3. Restricciones operativas

| Restricción | Tipo | Evidencia | Efecto arquitectónico |
|---|---|---|---|
| Auxiliar de despacho con ventana horaria 07:00–12:00 y 14:00–17:00 en America/Bogota | Operativa | [apps/authentication/services.py](../apps/authentication/services.py), [shared/permissions.py](../shared/permissions.py) | Introduce una regla de acceso dependiente del tiempo y del rol. |
| Movimientos y auditoría inmutables | Operativa | [docs/README_ARQUITECTURA.md](README_ARQUITECTURA.md) | Las correcciones se hacen con nuevos eventos, no editando el historial. |
| No stock negativo | Operativa | [apps/movements/services.py](../apps/movements/services.py) | Exige validación transaccional y constraints en BD. |
| Serial obligatorio para Electroterapia | Operativa | [docs/README_ARQUITECTURA.md](README_ARQUITECTURA.md) | Condiciona validaciones de entrada y despacho. |

## 4. Restricciones de despliegue

| Restricción | Tipo | Evidencia | Efecto arquitectónico |
|---|---|---|---|
| Desarrollo y despliegue con Docker Compose | Despliegue | [docs/adr/ADR-008.md](adr/ADR-008.md) | Define la unidad de empaquetado y la paridad de entornos. |
| Configuración por variables de entorno | Despliegue | [docs/adr/ADR-009.md](adr/ADR-009.md) | Evita hardcodear secretos y hace explícito el contrato de runtime. |
| Imagen productiva con dependencias runtime explícitas | Despliegue | [docs/adr/ADR-012.md](adr/ADR-012.md) | El build de producción no puede asumir que `base.txt` basta. |
| Healthcheck antes de levantar web | Despliegue | [docker-compose.prod.yml](../docker-compose.prod.yml) | El arranque depende del estado de PostgreSQL. |

## 5. Restricciones de pruebas

| Restricción | Tipo | Evidencia | Efecto arquitectónico |
|---|---|---|---|
| Suite de pruebas con SQLite in-memory | Pruebas | [config/settings/test.py](../config/settings/test.py) | Reduce fidelidad frente a PostgreSQL y no reproduce locking real. |
| Throttling desactivado en tests | Pruebas | [config/settings/test.py](../config/settings/test.py) | La suite no valida límites operativos reales. |
| Estrategia de testing por capas | Pruebas | [docs/adr/ADR-011.md](adr/ADR-011.md) | Refuerza unitarios, integración e invariantes. |

## 6. Restricciones que más pesan sobre la arquitectura

1. PostgreSQL como base única del runtime real.
2. Ledger inmutable con stock derivado.
3. JWT + RBAC + restricción horaria.
4. Docker Compose y variables de entorno.
5. Suite de pruebas que no replica exactamente producción.

## 7. Riesgos documentados

- La fidelidad de la suite de pruebas es parcial para concurrencia y locks.
- La imagen de producción requiere coordinación explícita de dependencias runtime.
- El sistema no está diseñado para alta disponibilidad distribuida en este alcance.
- La auditoría depende de que nadie escriba fuera del flujo de `services.py`.

---

## 8. Restricciones formales  — Clasificación por tipo (REST-01 a REST-06)

Esta sección presenta las restricciones en el formato requerido por el entregable académico: ID, tipo (Tecnológica / Organizacional / Regulatoria), descripción, impacto en opciones de diseño y ADR vinculado.

---

### REST-01 — Django + PostgreSQL como stack obligatorio

- **Tipo:** Tecnológica
- **Descripción:** El sistema usa Django 4.x + Django REST Framework + PostgreSQL como stack central. No es negociable cambiar el framework ni el motor de base de datos en el alcance del proyecto.
- **Impacto en diseño:** Descarta arquitecturas basadas en NoSQL para el ledger principal; descarta frameworks alternativos (FastAPI, Flask); obliga a usar el ORM de Django con sus patrones (migrations, models, transactions). Habilita ACID, `select_for_update()` y constraints fuertes que sustentan la consistencia del inventario.
- **ADR vinculado:** ADR-003 (PostgreSQL como BD única), ADR-001 (monolito modular con Django).

---

### REST-02 — Despliegue exclusivo con Docker Compose (sin orquestadores cloud)

- **Tipo:** Tecnológica / Organizacional
- **Descripción:** El despliegue del sistema se realiza únicamente con Docker Compose. No se usa Kubernetes, AWS ECS, ni ningún orquestador de contenedores en la nube.
- **Impacto en diseño:** Descarta estrategias de alta disponibilidad complejas (autoescalado horizontal, failover automático entre zonas). La disponibilidad depende de los health checks del Compose y del servidor donde se despliega. Descarta también microservicios en esta fase, ya que su operación requiere orquestación.
- **ADR vinculado:** ADR-008 (Docker Compose), ADR-001 (monolito modular vs. microservicios).

---

### REST-03 — Equipo pequeño con tiempo acotado (contexto universitario)

- **Tipo:** Organizacional
- **Descripción:** El equipo tiene 3-5 integrantes con dedicación parcial y un plazo de semanas por corte. No hay presupuesto para infraestructura cloud pagada ni para herramientas de observabilidad avanzada.
- **Impacto en diseño:** Descarta microservicios (overhead operacional alto), descarta event sourcing completo, descarta Redis para caché en primera fase, y obliga a priorizar simplicidad de implementación sobre optimizaciones prematuras. Justifica también el uso de SQLite en tests (velocidad sobre fidelidad).
- **ADR vinculado:** ADR-001 (monolito modular justificado por restricción de equipo), ADR-011 (estrategia de testing con SQLite por velocidad).

---

### REST-04 — Datos de operación en servidores locales de la empresa (on-premise)

- **Tipo:** Regulatoria
- **Descripción:** Los datos del inventario, movimientos y clientes deben residir en servidores on-premise de la empresa. No se permite almacenamiento en cloud público (AWS S3, Firebase, GCP, etc.) para datos transaccionales del sistema.
- **Impacto en diseño:** Descarta soluciones de storage en nube para backups primarios y sincronización automática a cloud. Obliga a que Docker Compose corra en servidor local. Condiciona la estrategia de backups a herramientas locales.
- **ADR vinculado:** ADR-008 (despliegue Docker en servidor local), ADR-009 (variables de entorno para secretos, sin hardcoding hacia servicios cloud).

---

### REST-05 — API exclusivamente REST sobre HTTP/JSON sin WebSockets en fase actual

- **Tipo:** Tecnológica
- **Descripción:** La comunicación frontend-backend se realiza exclusivamente por HTTP/JSON bajo `/api/v1/`. No se implementa WebSockets, SSE (Server-Sent Events) ni GraphQL en esta fase del proyecto.
- **Impacto en diseño:** Descarta dashboards con actualización push en tiempo real. El monitoreo de stock en tiempo real se implementa con polling desde el frontend, no con WebSockets. Limita el diseño del módulo de alertas a consultas por demanda. Simplifica la capa de servidor al no necesitar canales async.
- **ADR vinculado:** ADR-006 (API REST versionada bajo `/api/v1/`).

---

### REST-06 — Protección de datos personales de clientes (Ley 1581 de Colombia)

- **Tipo:** Regulatoria
- **Descripción:** El sistema maneja datos de clientes (nombre, contacto en despachos). La Ley 1581 de Habeas Data de Colombia exige consentimiento para el tratamiento de datos personales y restringe su exposición a terceros no autorizados.
- **Impacto en diseño:** Obliga a restringir la exposición de datos personales a roles autorizados (no todos los reportes pueden incluir nombres de cliente). Exige que el AuditLog registre quién accedió a datos sensibles. Condiciona el diseño de los serializers de despacho para no exponer datos innecesarios. Referenciado en RNF-006 del ERS.
- **ADR vinculado:** ADR-007 (RBAC con permisos componibles, incluyendo restricción de datos por rol). Si no existe un ADR específico de privacidad, debe crearse para el Corte 2.

---

## Ver también

- [design-patterns.md](design-patterns.md) — cómo se materializan estas restricciones en código (Service Layer para la restricción de lógica en services, Strategy para RBAC, Facade para select_for_update, etc.).
- [solid-principles.md](solid-principles.md) — evidencia de SRP, OCP y DIP que sostienen las restricciones estructurales.
- [adr_relationships.md](adr_relationships.md) — trazabilidad completa driver → problema → ADR.
- [architecture_drivers.md](architecture_drivers.md) — drivers que justifican estas restricciones.
- [docs/calidad_restricciones/README_RESTRICCIONES.md](../calidad_restricciones/README_RESTRICCIONES.md) — catálogo operativo de restricciones no funcionales.
