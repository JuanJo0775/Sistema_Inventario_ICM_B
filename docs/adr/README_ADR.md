# Indice de Architectural Decision Records (ADRs)

## Resumen

Este directorio contiene las decisiones arquitectonicas del Sistema Inventario ICM. Cada ADR documenta una decision significativa, su contexto, las alternativas consideradas y sus consecuencias.

## Indice

| ID | Titulo | Estado |
|----|--------|--------|
| [ADR-001](ADR-001.md) | Adoptar monolito modular por dominio en lugar de microservicios | Aceptado |
| [ADR-002](ADR-002.md) | Implementar separacion estricta de responsabilidades en capas | Aceptado |
| [ADR-003](ADR-003.md) | Usar PostgreSQL como base de datos relacional unica del sistema | Aceptado |
| [ADR-004](ADR-004.md) | Implementar autenticacion con JWT (access + refresh tokens) | Aceptado |
| [ADR-005](ADR-005.md) | Modelar el inventario como ledger inmutable con stock derivado sincronizado | Aceptado |
| [ADR-006](ADR-006.md) | Exponer toda la funcionalidad mediante API REST versionada bajo /api/v1/ | Aceptado |
| [ADR-007](ADR-007.md) | Implementar RBAC con permisos DRF componibles por endpoint | Aceptado |
| [ADR-008](ADR-008.md) | Contenerizar el sistema completo con Docker Compose | Aceptado |
| [ADR-009](ADR-009.md) | Separar configuraciones de settings en base/development/production con secretos por env vars | Aceptado |
| [ADR-010](ADR-010.md) | Generar facturas digitales en PDF con numeracion secuencial atomica en cada despacho | Aceptado |
| [ADR-011](ADR-011.md) | Estrategia de testing en tres niveles con pytest y factory-boy | Aceptado |
| [ADR-012](ADR-012.md) | Alinear la imagen de produccion con dependencias runtime explicitas | Aceptado |
| [ADR-013](ADR-013.md) | Arquitectura de precios y facturacion comercial sobre el ledger de movimientos | Aceptado |
| [ADR-014](ADR-014.md) | Modulo de compras: proveedores, órdenes de compra y recepciones | Aceptado |
| [ADR-015](ADR-015.md) | Manejo sistemático de DoesNotExist en servicios con select_for_update | Propuesto |

## Resumen de Decisiones Clave

### Core Architectural

- **ADR-001**: Monolito modular con apps Django separadas por dominio.
- **ADR-002**: Separacion estricta de responsabilidades (models/serializers/views/services/selectors/permissions).
- **ADR-005**: Modelo dual ledger inmutable + stock derivado sincronizado.

### Data & Infrastructure

- **ADR-003**: PostgreSQL 18 con transacciones ACID y select_for_update.
- **ADR-008**: Docker Compose para paridad de entornos.
- **ADR-009**: Settings jerarquicos con gestion de secretos por variables de entorno.

### Security & Access

- **ADR-004**: JWT con access token (60 min) y refresh token (7 dias) con blacklist.
- **ADR-007**: RBAC con permisos DRF componibles + restriccion horaria por endpoint.

### API & Integration

- **ADR-006**: API REST versionada /api/v1/ con OpenAPI/Swagger via drf-spectacular.

### Business Logic

- **ADR-010**: Generacion de facturas PDF con numeracion secuencial atomica.
- **ADR-011**: Testing en tres niveles (60% unitario, 25% integracion, 15% invariantes).
- **ADR-012**: Imagen de produccion con dependencias runtime explicitas.
- **ADR-013**: Arquitectura de precios y facturacion: snapshot inmutable en Movement, historial de precios en ProductPriceHistory, modelo Invoice consolidado, combos con precio fijo/derivado, reportes financieros y webhooks de despacho.
- **ADR-014**: Modulo de compras: proveedores, ordenes de compra y recepciones con integracion al ledger via Movement.

## Documentos de síntesis relacionados

- [architecture_drivers.md](../architecture/architecture_drivers.md) — drivers funcionales y arquitectónicos priorizados.
- [utility_tree.md](../architecture/utility_tree.md) — Utility Tree del sistema con escenarios de calidad.
- [architectural_constraints.md](../architecture/architectural_constraints.md) — restricciones reales que condicionan el diseño.
- [adr_relationships.md](../architecture/adr_relationships.md) — trazabilidad entre drivers, problemas, decisiones y ADRs.

## Notas sobre decisiones interrelacionadas

- **ADR-005** es el nucleo arquitectonico mas relevante del proyecto. El modelo ledger + stock derivado tiene implicaciones directas en casi todos los demas modulos.
- **ADR-004** y **ADR-007** estan intimamente acoplados: el JWT lleva el role en el payload, lo que hace que IsWithinOperatingHours no necesite consultar BD, pero introduce el riesgo del desfase de hasta 60 minutos si un rol cambia.
- **ADR-010** tiene una trampa de concurrencia importante: si se usa MAX(invoice_number) + 1 en lugar de una secuencia atomica de PostgreSQL, habra duplicados bajo carga concurrente.
- **ADR-011** asume SQLite in-memory para pruebas, por lo que la suite prioriza velocidad sobre fidelidad exacta del motor de produccion.