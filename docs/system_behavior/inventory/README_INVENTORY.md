# Módulo de Inventario

## 1. Resumen

El módulo `inventory` gestiona ubicaciones físicas, stock derivado (`StockByLocation`), tipos de almacenamiento y la reconstrucción de stock desde el ledger.

**RF-004** — Gestión de ubicaciones y stock.
**BR-11** — `Movement` es fuente de verdad; `StockByLocation` es caché derivada.
**BR-14** — Estados operativos de ubicación.
**BR-15** — Tipos de almacenamiento.

---

## 2. Modelos

### 2.1 Location

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `code` | SlugField(100, unique) | Auto-generado desde name |
| `name` | CharField(100) | Nombre |
| `description` | TextField | Descripción |
| `is_retail` | BooleanField | Auto-detectado |
| `max_capacity` | PositiveIntegerField (nullable) | Capacidad máxima |
| `storage_type` | FK -> StorageType (nullable) | Tipo de almacenamiento |
| `storage_template` | FK -> StorageTemplate (nullable) | Plantilla de origen |
| `operational_status` | CharField(20) | active / maintenance / restricted / blocked / archived |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel — eliminación lógica, separada de operational_status |
| `capacity_mode` | CharField(20) | none / relative_scale / absolute_legacy |
| `capacity_level` | Integer (1-5, nullable) | Escala relativa |
| `capacity_score` | PositiveIntegerField (nullable) | Puntaje abstracto |
| `occupancy_estimate_pct` | FloatField (nullable) | Estimación ocupación |
| `is_active` | BooleanField | Derivated de operational_status |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.2 OperationalStatus (BR-14)

| Estado | Valor | Entradas | Salidas | Traslados (origen) | Traslados (destino) |
|--------|-------|:--------:|:-------:|:-------------------:|:-------------------:|
| Activa | `active` | ✅ | ✅ | ✅ | ✅ |
| Mantenimiento | `maintenance` | ✅ | ❌ | ❌ | ✅ |
| Restringida | `restricted` | ✅ | ❌ | ❌ | ✅ |
| Bloqueada | `blocked` | ❌ | ❌ | ❌ | ❌ |
| Archivada | `archived` | ❌ | ❌ | ❌ | ❌ |

### 2.3 StockByLocation

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `product` | FK -> Product (PROTECT) | Producto |
| `location` | FK -> Location (PROTECT) | Ubicación |
| `current_stock` | PositiveIntegerField (default=0) | Stock actual (>= 0) |
| `location_reorder_point` | PositiveIntegerField (nullable) | Umbral local |
| `last_movement_at` | DateTimeField (nullable) | Último movimiento |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

**Constraint**: `stock_non_negative` (`current_stock >= 0`).

### 2.4 StorageType (BR-15)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `code` | SlugField(80, unique) | Código técnico |
| `name` | CharField(100, unique) | Nombre |
| `category` | CharField(50) | Agrupación |
| `capabilities` | JSONField | Metadatos |
| `default_is_retail` | BooleanField | Retail por defecto |
| `is_system` | BooleanField | Del sistema |
| `is_active` | BooleanField | Solo activos asignables |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel — eliminación lógica, separada de `is_active` |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.5 StorageTemplate

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `name` | CharField(100, unique) | Nombre de la plantilla |
| `storage_type` | FK -> StorageType | Tipo de almacenamiento asignado |
| `description` | TextField | Opcional |
| `is_active` | BooleanField | Plantilla activa/inactiva |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel — eliminación lógica |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

---

## 3. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `create_location(executor, data)` | RF-004, BR-14, BR-15 | Alta de ubicación |
| `update_location(executor, location_id, data)` | RF-004 | Actualización |
| `transition_location_state(executor, location_id, status)` | RF-004, BR-14 | Cambio de estado |
| `deactivate_location(executor, location_id)` | RF-004 | Desactivación |
| `trigger_stock_reconstruction(executor, product_id, location_id)` | BR-11 | Reconstrucción desde ledger |
| `create_storage_type(executor, data)` | BR-15 | Tipo de almacenamiento |
| `update_storage_type(executor, storage_type_id, data)` | BR-15 | Actualizar tipo |
| `soft_delete_storage_type(executor, storage_type_id)` | SoftDelete | Eliminación lógica + `is_active=False` |
| `restore_storage_type(executor, storage_type_id)` | SoftDelete | Restauración lógica + `is_active=True` |
| `soft_delete_storage_template(executor, template_id)` | SoftDelete | Eliminación lógica |
| `restore_storage_template(executor, template_id)` | SoftDelete | Restauración lógica |
| `soft_delete_location(executor, location_id)` | SoftDelete | Eliminación lógica + `operational_status=archived` |
| `restore_location(executor, location_id)` | SoftDelete | Restauración lógica + estado previo |

### Selectors

| Función | Descripción |
|---------|-------------|
| `get_stock_by_product(product_id)` | Stock por ubicación + total consolidado |
| `get_stock_by_location(location_id)` | Stock en una ubicación |
| `reconstruct_stock_from_ledger(product_id, location_id)` | Compara ledger vs StockByLocation |
| `consolidated_stock_total(product_id)` | Total consolidado en todas las ubicaciones |
| `get_full_inventory(filters)` | Inventario completo |
| `get_low_stock_products(threshold)` | Productos con stock bajo |

---

## 4. Endpoints

Todas bajo `/api/v1/inventory/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `` | Autenticado | Inventario consolidado |
| GET/POST | `storage-types/` | AlmacenistaOrReadOnly | Listar/crear tipos |
| GET/PUT/PATCH/DELETE | `storage-types/<pk>/` | AlmacenistaOrReadOnly | CRUD tipo |
| GET/POST | `storage-templates/` | AlmacenistaOrReadOnly | Listar/crear plantillas |
| GET/PUT/PATCH/DELETE | `storage-templates/<pk>/` | AlmacenistaOrReadOnly | CRUD plantilla |
| GET/POST | `locations/` | AlmacenistaOrReadOnly | Listar/crear ubicaciones |
| GET/PUT/PATCH/DELETE | `locations/<pk>/` | AlmacenistaOrReadOnly | CRUD ubicación |
| POST | `locations/<pk>/state-transitions/` | Almacenista | Transición de estado |
| POST | `reconstruct/` | Almacenista | Reconstruir stock |
| GET | `stock/product/<product_id>/` | Autenticado | Stock por producto |
| GET | `stock/location/<location_id>/` | Autenticado | Stock por ubicación |
| GET | `search/` | Autenticado | Buscar productos |
| PATCH | `stock/<pk>/threshold/` | Almacenista | Umbral de reorden |

---

## 5. Reconstrucción de stock (BR-11)

La función `reconstruct_stock_from_ledger()` calcula el stock del ledger mediante suma algebraica O(1) y lo compara con `StockByLocation.current_stock`:

- Si coinciden → `CONSISTENT`
- Si no → `DISCREPANCY` + alerta `STOCK_MISMATCH`

---

## 6. Escenarios esperados

**INV-S01**: Crear ubicación activa → 201, operational_status=active.
**INV-S02**: Transición a maintenance → origen bloqueado para salidas.
**INV-S03**: Despacho desde ubicación en maintenance → LocationStateNotAllowedError.
**INV-S04**: Transición a archived → is_active=False, solo si stock=0.
**INV-S05**: Reconstrucción consistente → CONSISTENT.
**INV-S06**: Reconstrucción con discrepancia → DISCREPANCY + alerta.
**INV-S07**: Asignar StorageType inactivo a ubicación → error de validación.
