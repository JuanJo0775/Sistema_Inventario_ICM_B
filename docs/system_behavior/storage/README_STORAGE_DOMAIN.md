# Dominio de Almacenamiento — Visión General

## Propósito

Este dominio extiende la entidad `Location` con clasificación tipada (`StorageType`), plantillas de creación rápida (`StorageTemplate`), estados operativos formales y capacidad relativa informativa.

El invariante central no cambia: el ledger de `Movement` es la única fuente de verdad del stock; `StockByLocation` es caché derivada; los nuevos modelos de este dominio no alteran esa invariante.

---

## Modelos

### StorageType
Tipo configurable de almacenamiento (bodega grande, vitrina, cuarto frío, etc.).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `code` | slug único | Identificador técnico (ej. `bodega-grande`) |
| `name` | str único | Nombre legible |
| `category` | str | Agrupación libre (warehouse, cold_chain, retail…) |
| `capabilities` | JSON | Metadatos extensibles sin migración |
| `default_is_retail` | bool | Si las ubicaciones de este tipo son minoristas por defecto |
| `is_system` | bool | Tipos no editables creados en seed |
| `is_active` | bool | Solo tipos activos pueden asignarse a ubicaciones |
| `deleted_at` | datetime (nullable) | Soft delete — existencia lógica; no rompe FKs existentes, impide nueva asignación |
| `sort_order` | int | Orden en listas |

**Regla clave:** un `StorageType` inactivo no puede asignarse ni en `create_location` ni en `update_location`.

---

### StorageTemplate
Plantilla reutilizable que preconfiguran parámetros de ubicación.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `code` | slug único | Identificador técnico |
| `storage_type` | FK nullable | Tipo de almacenamiento que hereda la ubicación |
| `defaults` | JSON | Valores por defecto: `is_retail`, `max_capacity`, `capacity_mode`, `capacity_level`, `capacity_score`, `occupancy_estimate_pct` |
| `is_active` | bool | Solo plantillas activas pueden usarse al crear ubicaciones |
| `deleted_at` | datetime (nullable) | Soft delete — existencia lógica |

Al crear una `Location` con `storage_template_id`:
1. Se aplican los valores de `defaults` si no se pasan explícitamente.
2. Si `storage_type_id` no se pasa, se hereda del template.

---

### Location (campos nuevos)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `storage_type` | FK nullable | Tipo asignado |
| `storage_template` | FK nullable | Plantilla de origen |
| `operational_status` | choice | Estado operativo formal (ver sección de estados) |
| `capacity_mode` | choice | `none` / `relative_scale` / `absolute_legacy` |
| `capacity_level` | int 1-5 | Escala relativa de capacidad |
| `capacity_score` | int > 0 | Puntaje abstracto de capacidad |
| `occupancy_estimate_pct` | float 0-100 | Estimación de ocupación informativa |
| `deleted_at` | datetime (nullable) | Soft delete — existencia lógica; al eliminar fuerza `operational_status=archived`, `is_active=False` |

---

## Relaciones

```
StorageType ──< Location ──< StockByLocation
StorageTemplate ──< Location
StorageType ──< StorageTemplate
```

---

## Documentos relacionados

- [README_STORAGE_TYPES.md](./README_STORAGE_TYPES.md) — ciclo de vida de tipos
- [README_LOCATION_STATES.md](./README_LOCATION_STATES.md) — estados operativos y reglas de movimiento
- [ADR-StorageType-Model](../adr/) — decisión de modelar StorageType separado de Location
