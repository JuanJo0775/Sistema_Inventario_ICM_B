# System Behavior — Sistema Inventario ICM

Este directorio describe el comportamiento detallado de cada módulo del sistema: modelos, servicios, flujos, reglas de negocio, endpoints y escenarios esperados.

## Dominios

| Módulo | Propósito |
|--------|-----------|
| [auth/](auth/README_AUTH.md) | Autenticación JWT, gestión de usuarios, roles, horarios auxiliares |
| [catalog/](catalog/README_CATALOG.md) | Productos, categorías, subcategorías, combos, precios |
| [inventory/](inventory/README_INVENTORY.md) | Ubicaciones, stock derivado, reconstrucción, tipos de almacenamiento |
| [movements/](movements/README_MOVEMENTS.md) | Ledger inmutable: entradas, salidas, traslados, devoluciones, ajustes |
| [purchasing/](purchasing/README_PURCHASING.md) | Proveedores, órdenes de compra, recepciones |
| [alerts/](alerts/README_ALERTS.md) | Alertas de stock, vencimiento, integridad |
| [audit/](audit/README_AUDIT.md) | Auditoría inmutable de todas las operaciones |
| [webhooks/](webhooks/README_WEBHOOKS.md) | Notificaciones a sistemas externos |
| [dashboard/](dashboard/README_DASHBOARD.md) | Read model operacional para UI ejecutiva |
| [reports/](reports/README_REPORTS.md) | Reportes operativos, financieros y KPIs |
| [storage/](storage/README_STORAGE_DOMAIN.md) | Dominio de almacenamiento: tipos, plantillas, estados operativos |
| [pricing/](pricing/README_PRECIOS_FACTURACION.md) | Precios, facturación y snapshots financieros |

## Convenciones generales

- **API**: REST bajo `/api/v1/`, JSON, JWT Bearer, errores `{ error, message, detail }`
- **Roles**: `almacenista` (control total), `auxiliar_despacho` (franja horaria), `administrador` (solo lectura)
- **Stock**: `Movement` es la fuente de verdad; `StockByLocation` es derivado sincronizado en transacción
- **Inmutabilidad**: movimientos y auditoría no se editan ni eliminan; las correcciones crean nuevos registros
- **Transacciones**: toda operación de escritura usa `@transaction.atomic` y `select_for_update()` donde hay riesgo de concurrencia
- **Soft delete**: entidades del sistema usan `SoftDeleteModel` (`shared.models`) con `deleted_at` para existencia lógica; `is_active` controla disponibilidad para reglas de negocio (nunca mezclar)
- **Lock utility**: `get_for_update_or_404()` (`shared.utils.db`) para obtener objetos con `select_for_update()` o lanzar 404

## Documentación de arquitectura transversal

Los patrones y principios que aplican a **todos** los módulos listados arriba están documentados aquí:

| Documento | Propósito |
|-----------|-----------|
| [architecture/design-patterns.md](../architecture/design-patterns.md) | Catálogo de 10 patrones de diseño: Service Layer, Selector, Strategy, Observer, Facade, Composite, etc. |
| [architecture/solid-principles.md](../architecture/solid-principles.md) | Análisis SOLID con evidencia de código por principio y oportunidades de mejora |
| [architecture/adr_relationships.md](../architecture/adr_relationships.md) | Trazabilidad driver → decisión → ADR |
| [README_ARQUITECTURA.md](../README_ARQUITECTURA.md) | Arquitectura consolidada: capas, ledger, Docker, testing |
