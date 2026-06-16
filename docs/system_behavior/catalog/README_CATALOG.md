# Módulo de Catálogo

## 1. Resumen

El módulo `catalog` gestiona el catálogo maestro de productos del sistema ICM: categorías, marcas, productos/SKU, lotes, seriales, combos y precios. Es la referencia central que todos los demás módulos consultan mediante FK.

**RF-003** — Gestión de catálogo de productos (SKU, categorías, marcas, combos).
**BR-04** — Serial obligatorio en categorías de Electroterapia (`requires_serial_number=True`).
**BR-05** — Devolución permitida solo en categorías marcadas como `is_returnable`.
**BR-12** — SKU definido por usuario: patrón 1–4 letras, guion, 1–4 dígitos (ej: `AB-1234`).
**BR-13** — `barcode` = alias de escaneo auto-generado desde el SKU; indexado para búsqueda rápida.

---

## 2. Modelos

### 2.1 Category

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único (BaseModel) |
| `name` | CharField(128, unique) | Nombre de la categoría |
| `slug` | SlugField(128, unique) | Slug auto-generado |
| `requires_serial_number` | BooleanField | BR-04: impone serial en entradas/salidas |
| `is_returnable` | BooleanField | BR-05: admite devoluciones |
| `description` | TextField | Descripción opcional |
| `is_active` | BooleanField | Categoría activa/inactiva |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel |
| `created_at` / `updated_at` | DateTimeField | Automáticos |

### 2.2 Brand

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `name` | CharField(128, unique) | Nombre de la marca |
| `slug` | SlugField(128, unique) | Slug auto-generado |
| `description` | TextField | Descripción opcional |
| `is_active` | BooleanField | Marca activa/inactiva |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel |

**Soft delete:** Category, Brand, Product y ProductCombo heredan de `SoftDeleteModel` (`shared.models`). `deleted_at` controla existencia lógica; `is_active` controla disponibilidad para reglas de negocio (asignación, uso en movimientos). Nunca mezclar ambas responsabilidades.

Las marcas son independientes de las categorías. Un producto puede no tener marca.

### 2.3 Product

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `sku` | CharField(100, unique, indexed) | BR-12: patrón 1-4 letras, guion, 1-4 dígitos |
| `barcode` | CharField(100, unique, indexed, nullable) | BR-13: alias de escaneo auto-generado |
| `name` | CharField(255) | Nombre del producto |
| `category` | FK → Category (PROTECT) | Macrocategoría |
| `brand` | FK → Brand (nullable, SET_NULL) | Marca opcional |
| `expiration_date` | DateField (nullable) | Fecha de vencimiento base |
| `requires_expiration` | BooleanField | Control de vencimiento por lote |
| `weight_grams` | PositiveIntegerField (nullable) | Peso en gramos |
| `requires_cold_chain` | BooleanField | Requiere cadena de frío |
| `is_active` | BooleanField | Producto activo/inactivo |
| `notes` | TextField | Notas |
| `reorder_point` | PositiveIntegerField(default=0) | Umbral para alerta LOW_STOCK |
| `unit_cost` | DecimalField(12,4, nullable) | Costo de adquisición por unidad (COGS) |
| `sale_price_retail` | DecimalField(12,4, nullable) | Precio venta al por menor |
| `sale_price_wholesale` | DecimalField(12,4, nullable) | Precio venta al por mayor |
| `tax_rate_pct` | DecimalField(5,2, nullable) | IVA aplicable (ej: 19.00) |
| `currency` | CharField(3, default="COP") | Moneda ISO 4217 |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel |

**Validación BR-12:** `clean()` normaliza y valida el formato de SKU; la API también valida en `catalog.services.create_product()`.

### 2.4 Lot

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `product` | FK → Product (PROTECT) | Producto asociado |
| `code` | CharField(100) | Código de lote (único por producto) |
| `expiration_date` | DateField | Fecha de vencimiento del lote |

Constraint: `uniq_lot_code_per_product` — el par `(product, code)` es único.
Índices: `(product, expiration_date)` y `(code)`.

### 2.5 ProductSerial

Unidad serializada individual (BR-04). Se crea al registrar una entrada para productos con `requires_serial_number=True`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `product` | FK → Product (PROTECT) | Producto asociado |
| `serial_number` | CharField(100) | Número de serie (único por producto) |
| `status` | CharField(20) | `available` / `dispatched` / `damaged` / `adjusted` |
| `current_location` | FK → Location (nullable, PROTECT) | Ubicación actual |
| `last_movement` | FK → Movement (nullable, SET_NULL) | Último movimiento que lo afectó |

Constraint: `uniq_product_serial_per_product` — `(product, serial_number)` único.

### 2.6 ProductCombo

Kit o combo: varios SKUs bajo un identificador único (RF-003).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `name` | CharField(255) | Nombre del combo |
| `sku` | CharField(100, unique) | SKU del combo |
| `products` | M2M → Product (through ComboItem) | Productos componentes |
| `price_strategy` | CharField(20) | `derived` (suma de componentes) / `fixed` (precio fijo) |
| `fixed_price_retail` | DecimalField(12,4, nullable) | Precio fijo al por menor |
| `fixed_price_wholesale` | DecimalField(12,4, nullable) | Precio fijo al por mayor |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel |

### 2.7 ComboItem

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `combo` | FK → ProductCombo (CASCADE) | Combo padre |
| `product` | FK → Product (CASCADE) | Producto componente |
| `quantity` | PositiveIntegerField(default=1) | Cantidad del componente |

Constraint: `uniq_combo_product_item` — un producto no puede aparecer dos veces en el mismo combo.

### 2.8 ProductPriceHistory

Registro inmutable de cambios de precio. Cada actualización de `unit_cost`, `sale_price_retail`, `sale_price_wholesale` o `tax_rate_pct` genera una fila.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `product` | FK → Product (PROTECT) | Producto |
| `changed_by` | FK → User (PROTECT) | Usuario que realizó el cambio |
| `field_changed` | CharField(64) | Campo modificado |
| `old_value` | DecimalField(12,4, nullable) | Valor anterior |
| `new_value` | DecimalField(12,4, nullable) | Valor nuevo |
| `currency` | CharField(3, default="COP") | Moneda |

---

## 3. Servicios

Todas las funciones en `apps/catalog/services.py`. Requieren rol `almacenista` para escritura.

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `create_product(user, data)` | RF-003, BR-04, BR-12 | Crea producto; valida SKU y categoría activa |
| `update_product(user, product_id, data)` | RF-003, BR-12 | Actualiza campos; registra historial de precios si cambian |
| `disable_product(user, product_id)` | RF-003 | Soft-delete (is_active=False) |
| `enable_product(user, product_id)` | RF-003 | Reactiva producto |
| `create_category(user, data)` | RF-003 | Crea categoría |
| `update_category(user, pk, data)` | RF-003 | Actualiza categoría |
| `disable_category(user, pk)` | RF-003 | Desactiva categoría |
| `enable_category(user, pk)` | RF-003 | Reactiva categoría |
| `create_brand(user, data)` | RF-003 | Crea marca |
| `update_brand(user, pk, data)` | RF-003 | Actualiza marca |
| `disable_brand(user, pk)` | RF-003 | Desactiva marca |
| `enable_brand(user, pk)` | RF-003 | Reactiva marca |
| `create_combo(user, data)` | RF-003 | Crea combo con sus items |
| `update_combo(user, pk, data)` | RF-003 | Actualiza combo e items |
| `resolve_identifier(identifier)` | BR-13 | Busca producto/combo por SKU o barcode |
| `get_product_barcode_image(product)` | BR-13 | Genera imagen PNG del barcode (python-barcode) |
| `update_product_prices(user, product_id, data)` | RF-003 | Actualiza precios + registra historial |

---

## 4. Endpoints

Todas las rutas bajo `/api/v1/catalog/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET/POST | `categories/` | Auth | Listar / crear categorías |
| GET/PUT/PATCH | `categories/<pk>/` | Almacenista | Detalle / actualizar |
| POST | `categories/<pk>/disable/` | Almacenista | Desactivar categoría |
| POST | `categories/<pk>/enable/` | Almacenista | Reactivar categoría |
| POST | `categories/<pk>/restore/` | Almacenista | Restaurar (soft-delete) |
| GET/POST | `brands/` | Auth | Listar / crear marcas |
| GET/PUT/PATCH | `brands/<pk>/` | Almacenista | Detalle / actualizar |
| POST | `brands/<pk>/disable/` | Almacenista | Desactivar marca |
| POST | `brands/<pk>/enable/` | Almacenista | Reactivar marca |
| POST | `brands/<pk>/restore/` | Almacenista | Restaurar marca |
| GET/POST | `products/` | Auth | Listar / crear productos |
| GET/PUT/PATCH | `products/<pk>/` | Auth / Almacenista | Detalle / actualizar |
| GET | `products/<pk>/barcode/` | Auth | Imagen PNG del barcode |
| GET/PUT | `products/<pk>/prices/` | Auth / Almacenista | Ver / actualizar precios |
| POST | `products/<pk>/disable/` | Almacenista | Desactivar producto |
| POST | `products/<pk>/enable/` | Almacenista | Reactivar producto |
| POST | `products/<pk>/restore/` | Almacenista | Restaurar producto |
| GET | `products/resolve/` | Auth | Resolver SKU/barcode → producto |
| GET | `resolve/` | Auth | Alias de resolve (BR-13) |
| GET/POST | `combos/` | Auth / Almacenista | Listar / crear combos |
| GET/PUT/PATCH | `combos/<pk>/` | Auth / Almacenista | Detalle / actualizar |
| POST | `combos/<pk>/restore/` | Almacenista | Restaurar combo |

---

## 5. Reglas de negocio críticas

### BR-12 — Formato de SKU

```
Patrón: ^[A-Za-z]{1,4}-[0-9]{1,4}$
Ejemplos válidos: AB-1234, MED-001, X-1
Ejemplos inválidos: AB1234, ABCDE-1, AB-12345
```

El SKU se normaliza (strip + upper) antes de validar. La validación ocurre tanto en `services.create_product()` como en `Product.clean()` (admin/ModelForm).

### BR-13 — Barcode

El barcode se auto-genera desde el SKU al crear el producto: `shared.utils.barcode.build_product_barcode(sku)`. El endpoint `GET /products/<pk>/barcode/` retorna imagen PNG (python-barcode). Para resolución inversa (escaneo → producto), usar `GET /resolve/?q=<sku_o_barcode>`.

### BR-04 — Serial obligatorio

Si `category.requires_serial_number=True`, el movimiento de entrada debe incluir `serial_number`. El servicio de movimientos (`movements.services`) verifica esto al registrar la entrada.

### BR-05 — Devolución

Solo se permite registrar una devolución si el producto pertenece a una categoría con `is_returnable=True`. Validado en `movements.services`.

---

## 6. Flujo de creación de producto

```
POST /catalog/products/ { sku, name, category_id, brand_id?, ... }
  → create_product(almacenista, data)
    → _require_almacenista()          → 403 si no es almacenista
    → validate_sku_format(sku)        → DomainValidationError si formato inválido
    → Category.objects.get(pk=...)    → 404 si no existe
    → check category.is_active        → DomainValidationError si inactiva
    → check brand.is_active           → DomainValidationError si inactiva
    → Product.objects.create(...)     → barcode auto-generado
    → log_event(PRODUCT_CREATED)      → auditoría
    → retorna Product
```

---

## 7. Precios y historial

Los campos de precio (`unit_cost`, `sale_price_retail`, `sale_price_wholesale`, `tax_rate_pct`, `currency`) son opcionales — compatibles con productos creados antes de implementar precios.

Al actualizar precios vía `PUT /products/<pk>/prices/` o `update_product_prices()`, el servicio:
1. Detecta qué campos cambiaron comparando con el valor actual.
2. Crea una fila en `ProductPriceHistory` por cada campo modificado.
3. Audita el evento `PRODUCT_PRICE_UPDATED`.

Los combos pueden tener estrategia `derived` (suma de `sale_price_retail` de todos los ítems) o `fixed` (precio fijo en `fixed_price_retail` / `fixed_price_wholesale`).

---

## 8. Escenarios esperados

**CAT-S01**: Crear producto con SKU válido → 201 + barcode auto-generado + PRODUCT_CREATED en auditoría.
**CAT-S02**: Crear producto con SKU inválido → 400 DomainValidationError (formato BR-12).
**CAT-S03**: Crear producto en categoría inactiva → 400 DomainValidationError.
**CAT-S04**: Resolver SKU por barcode → 200 con producto encontrado.
**CAT-S05**: Auxiliar intenta crear producto → 403 UnauthorizedCredentialManagementError.
**CAT-S06**: Producto categoría `requires_serial_number=True` + movimiento sin serial → SerialNumberRequiredError.
**CAT-S07**: Crear combo con 2 productos → 201 + items relacionados.
**CAT-S08**: Actualizar precio → ProductPriceHistory registrada + PRODUCT_PRICE_UPDATED.
