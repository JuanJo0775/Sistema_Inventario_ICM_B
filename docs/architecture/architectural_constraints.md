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
| PostgreSQL 15 es la BD soportada en runtime real | Tecnológica | [docs/adr/ADR-003.md](adr/ADR-003.md) | Habilita ACID, `select_for_update()` y constraints fuertes. |
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
