# Módulo de Catálogo

## 1. Resumen

El módulo `catalog` gestiona el catálogo de productos, categorías, subcategorías, combos y precios. Es el maestro de productos del sistema.

**RF-003** — Gestión de catálogo (CRUD categorías, subcategorías, productos, combos).
**RF-013** — Precios y facturación (campos financieros en producto, historial de precios).

---

## 2. Modelos

### 2.1 Category

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `name` | CharField(128, unique) | Nombre de la categoría |
| `slug` | SlugField(128, unique) | Auto-generado |
| `requires_serial_number` | BooleanField | BR-04: Electroterapia |
| `is_returnable` | BooleanField | BR-05: admite devoluciones |
| `description` | TextField | Opcional |
| `is_active` | BooleanField | Soft delete |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.2 Subcategory

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `name` | CharField(128) | Nombre |
| `category` | FK -> Category | Categoría padre |
| `slug` | SlugField(128) | Único por categoría |
| `description` | TextField | Opcional |
| `is_active` | BooleanField | Soft delete |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.3 Product — Modelo central

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `sku` | CharField(100, unique) | BR-12: formato `1-4 letras, guion, 1-4 dígitos` |
| `barcode` | CharField(100, unique, nullable) | BR-13: alias de escaneo, auto-generado |
| `name` | CharField(255) | Nombre del producto |
| `category` | FK -> Category (PROTECT) | Categoría |
| `subcategory` | FK -> Subcategory (SET_NULL, nullable) | Subcategoría |
| `brand` | CharField(100, default="Can") | Marca |
| `expiration_date` | DateField (nullable) | Fecha de vencimiento |
| `requires_expiration` | BooleanField | Control de vencimiento |
| `weight_grams` | PositiveIntegerField (nullable) | Peso |
| `requires_cold_chain` | BooleanField | Cadena de frío |
| `reorder_point` | PositiveIntegerField | Umbral de stock bajo |
| `is_active` | BooleanField | Soft delete |
| `unit_cost` | DecimalField(12,4) nullable | Costo (COGS) |
| `sale_price_retail` | DecimalField(12,4) nullable | Precio venta menor |
| `sale_price_wholesale` | DecimalField(12,4) nullable | Precio venta mayor |
| `tax_rate_pct` | DecimalField(5,2) nullable | Tasa IVA |
| `currency` | CharField(3, default="COP") | Moneda |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.4 ProductCombo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `name` | CharField(255) | Nombre del combo |
| `sku` | CharField(100, unique) | SKU propio |
| `is_active` | BooleanField | Soft delete |
| `products` | M2M -> Product (through=ComboItem) | Componentes |
| `price_strategy` | CharField(20) | `derived` (suma) o `fixed` |
| `fixed_price_retail/wholesale` | DecimalField(12,4) nullable | Solo si strategy=fixed |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.5 ProductPriceHistory

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `product` | FK -> Product (PROTECT) | Producto |
| `changed_by` | FK -> User (PROTECT) | Quién cambió |
| `field_changed` | CharField(64) | Campo modificado |
| `old_value` / `new_value` | DecimalField(12,4) nullable | Valor anterior/nuevo |
| `currency` | CharField(3, default="COP") | Moneda |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.6 Lot

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `product` | FK -> Product (PROTECT) | Producto asociado |
| `code` | CharField(100) | Código de lote |
| `expiration_date` | DateField (nullable) | Fecha de vencimiento |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.7 ComboItem (through)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `combo` | FK -> ProductCombo (CASCADE) | Combo padre |
| `product` | FK -> Product (PROTECT) | Producto componente |
| `quantity` | PositiveIntegerField(default=1) | Cantidad en el combo |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

---

## 3. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `create_product(user, data)` | RF-003, BR-04, BR-12 | Valida SKU, crea con barcode |
| `update_product(user, product_id, data)` | RF-003 | SKU inmutable |
| `deactivate_product(user, product_id)` | RF-003 | Soft delete, valida combos activos |
| `update_product_prices(user, product_id, **prices)` | RF-013, BR-17 | Actualiza + historial ProductPriceHistory |
| `create_category(user, data)` | RF-003 | Crea categoría |
| `deactivate_category(user, category_id)` | RF-003 | Valida productos activos (409) |
| `create_combo(user, data)` | RF-003 | Crea combo con items |
| `update_combo(user, combo_id, data)` | RF-003 | Reemplaza items completamente |
| `resolve_identifier(raw)` | BR-13 | Busca por: SKU > barcode > nombre |

---

## 4. Reglas de negocio

| BR | Descripción |
|----|-------------|
| BR-04 | Serial obligatorio si `category.requires_serial_number` |
| BR-05 | Devoluciones solo si `category.is_returnable` |
| BR-12 | SKU: 1-4 letras, guion, 1-4 dígitos (ej: `AB-1234`) |
| BR-13 | Barcode como alias; resolución SKU > barcode > nombre |
| BR-17 | Historial inmutable de cambios de precio |

---

## 5. Endpoints

Todas bajo `/api/v1/catalog/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET/POST | `categories/` | AlmacenistaOrReadOnly | Listar/crear categorías |
| GET/PUT/PATCH/DELETE | `categories/<pk>/` | AlmacenistaOrReadOnly | CRUD categoría |
| POST | `categories/<pk>/restore/` | Almacenista | Restaurar |
| GET/POST | `subcategories/` | AlmacenistaOrReadOnly | Listar/crear |
| GET/PUT/PATCH/DELETE | `subcategories/<pk>/` | AlmacenistaOrReadOnly | CRUD subcategoría |
| POST | `subcategories/<pk>/restore/` | Almacenista | Restaurar |
| GET/POST | `products/` | Almacenista | Listar/crear |
| GET/PUT/PATCH/DELETE | `products/<pk>/` | AlmacenistaOrReadOnly | CRUD producto |
| GET | `products/<pk>/barcode/` | Autenticado | Barcode SVG |
| PATCH | `products/<pk>/prices/` | Almacenista | Actualizar precios |
| GET | `products/<pk>/prices/` | Almacenista | Historial precios |
| POST | `products/<pk>/restore/` | Almacenista | Restaurar |
| GET | `products/resolve/` | Autenticado | Resolver identificador |
| GET/POST | `combos/` | AlmacenistaOrReadOnly | Listar/crear combos |
| GET/PUT/PATCH/DELETE | `combos/<pk>/` | AlmacenistaOrReadOnly | CRUD combo |
| POST | `combos/<pk>/restore/` | Almacenista | Restaurar |

---

## 6. Escenarios esperados

**CAT-S01**: Crear producto con SKU válido → 201, barcode generado.
**CAT-S02**: Crear producto con SKU inválido ("12345") → 422 InvalidSKUFormatError.
**CAT-S03**: Actualizar precios → snapshot en ProductPriceHistory (BR-17).
**CAT-S04**: Desactivar producto en combo activo → 409 Conflict.
**CAT-S05**: Desactivar categoría con productos activos → 409 Conflict.
**CAT-S06**: Resolver producto por barcode → 200, producto encontrado.
**CAT-S07**: Resolver producto por SKU → 200, producto encontrado.
**CAT-S08**: Actualizar combo con reemplazo de items → items viejos eliminados, nuevos creados.
