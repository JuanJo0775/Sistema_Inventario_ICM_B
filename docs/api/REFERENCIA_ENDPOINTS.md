# Referencia de Endpoints — Sistema Inventario ICM

**Guía de integración para el equipo de frontend.**

---

## Índice rápido

- [Configuración base](#configuracion-base)
- [Autenticación](#autenticacion)
- [Catálogo](#catalogo)
- [Inventario](#inventario)
- [Movimientos](#movimientos)
- [Dashboard](#dashboard)
- [Reportes y exportación](#reportes-y-exportacion)
- [Alertas y polling](#alertas-y-polling)
- [Auditoría](#auditoria)
- [Webhooks](#webhooks)
- [Errores](#errores)
- [Paginación](#paginacion)
- [Tipos de datos](#tipos-de-datos)

---

## Configuración base

```
URL base:        http://localhost:8000/api/v1/
Autenticación:   Authorization: Bearer <access_token>
Content-Type:    application/json
Zona horaria:    America/Bogota (UTC-5)
Formato fechas:  ISO-8601
```

**Documentación interactiva (desarrollo):**

```
GET /api/docs/     → Swagger UI
GET /api/redoc/    → ReDoc
GET /api/schema/   → OpenAPI JSON
```

> En producción, `/api/docs/` y `/api/schema/` requieren sesión de staff de Django.

---

## Autenticación

### Health check

```
GET /api/v1/auth/health/
```

Sin autenticación. Respuesta:

```json
{ "status": "ok" }
```

---

### Login

```
POST /api/v1/auth/login/
```

**Sin autenticación.** El auxiliar de despacho solo puede autenticarse en franja horaria (07:00–12:00 y 14:00–17:00 hora Bogotá).

**Request:**
```json
{
  "email": "almacenista@icm.co",
  "password": "contraseña"
}
```

O con `username` en lugar de `email`.

**Response 200:**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": "uuid",
    "username": "almacenista1",
    "email": "almacenista@icm.co",
    "first_name": "Juan",
    "last_name": "García",
    "phone": "+573001234567",
    "role": "almacenista",
    "is_active": true
  }
}
```

Roles posibles: `almacenista`, `auxiliar_despacho`, `administrador`.

**Errores:**
- `401` — credenciales inválidas
- `403` — auxiliar fuera de horario operativo

---

### Renovar token

```
POST /api/v1/auth/token/refresh/
```

**Request:**
```json
{ "refresh": "eyJ..." }
```

**Response 200:**
```json
{ "access": "eyJ...", "refresh": "eyJ..." }
```

El refresh anterior queda invalidado (rotación). El auxiliar debe estar en horario para renovar.

---

### Logout

```
POST /api/v1/auth/logout/
Authorization: Bearer <access>
```

**Request:**
```json
{ "refresh": "eyJ..." }
```

**Response 204** — sin cuerpo. El refresh queda en blacklist.

---

### Perfil propio

```
GET /api/v1/auth/me/
Authorization: Bearer <access>
```

**Response 200:** mismo esquema del campo `user` del login.

---

### Gestión de usuarios

Solo `almacenista` puede crear y gestionar usuarios.

```
GET  /api/v1/auth/users/           → listar usuarios
POST /api/v1/auth/users/           → crear usuario
GET  /api/v1/auth/users/<uuid>/    → detalle usuario
PUT  /api/v1/auth/users/<uuid>/    → actualizar completo
PATCH /api/v1/auth/users/<uuid>/   → actualizar parcial
POST /api/v1/auth/users/<uuid>/disable/ → deshabilitar
```

**Request POST:**
```json
{
  "username": "auxiliar_juan",
  "email": "juan@icm.co",
  "password": "contraseña_segura",
  "first_name": "Juan",
  "last_name": "López",
  "role": "auxiliar_despacho",
  "phone": "+573009876543"
}
```

**Response 201:** objeto usuario completo.

**Filtros disponibles en `GET /auth/users/`:**
```
?role=almacenista|auxiliar_despacho|administrador
?search=<texto>        → busca en username, email, first_name, last_name
?include_inactive=true → incluye usuarios desactivados
?page=1&page_size=20   → activa paginación (sin estos params devuelve lista completa)
```

---

### Cambiar contraseña propia

```
POST /api/v1/auth/change-password/
Authorization: Bearer <access>
```

Disponible para cualquier rol autenticado. Invalida todos los tokens JWT activos del usuario.

**Request:**
```json
{
  "current_password": "ContraseñaActual123!",
  "new_password": "NuevaClave2026!",
  "new_password_confirm": "NuevaClave2026!"
}
```

**Response 200:**
```json
{ "message": "Contraseña actualizada correctamente." }
```

**Errores:**
- `400` — `new_password` y `new_password_confirm` no coinciden
- `401` — no autenticado
- `422` — contraseña actual incorrecta o nueva contraseña no cumple políticas

---

### Recuperación de contraseña (flujo completo)

#### Paso 1 — Solicitar enlace

```
POST /api/v1/auth/forgot-password/
```

Sin autenticación. **Siempre devuelve 200** aunque el email no exista (anti-enumeración).

**Request:**
```json
{ "email": "usuario@ejemplo.com" }
```

**Response 200:**
```json
{
  "message": "Si el correo está registrado recibirás instrucciones para recuperar tu contraseña."
}
```

Si el email corresponde a un usuario activo, el sistema:
1. Invalida tokens de reset anteriores del usuario.
2. Crea un token nuevo (válido `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES` minutos, default 10).
3. Envía email al usuario con el enlace: `{FRONTEND_URL}/reset-password?token=<raw_token>`.

**Errores:**
- `400` — formato de email inválido

---

#### Paso 2 — El frontend recibe el token

El usuario hace clic en el enlace del email y llega a la página del frontend:

```
http://localhost:3000/reset-password?token=<raw_token>
```

El frontend extrae `token` del query param y lo pasa al siguiente request.

---

#### Paso 3 — Restablecer contraseña

```
POST /api/v1/auth/reset-password/
```

Sin autenticación.

**Request:**
```json
{
  "token": "<raw_token_del_query_param>",
  "new_password": "NuevaClave2026!",
  "new_password_confirm": "NuevaClave2026!"
}
```

**Response 200:**
```json
{ "message": "Contraseña restablecida correctamente." }
```

**Errores:**
- `400` — contraseñas no coinciden
- `422` — token inválido, expirado o ya utilizado → mostrar "El enlace expiró. Solicita uno nuevo."

Tras el 200, el frontend debe redirigir a `/login`.

---

## Catálogo

### Categorías

```
GET  /api/v1/catalog/categories/             → listar (todos los autenticados)
POST /api/v1/catalog/categories/             → crear (solo almacenista)
GET  /api/v1/catalog/categories/<uuid>/      → detalle
PUT  /api/v1/catalog/categories/<uuid>/      → actualizar
PATCH /api/v1/catalog/categories/<uuid>/     → parcial
```

**Campos de categoría:**
```json
{
  "id": "uuid",
  "name": "Electroterapia",
  "slug": "electroterapia",
  "requires_serial_number": true,
  "is_returnable": false,
  "description": "...",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

> `requires_serial_number`: los productos de esta categoría exigen número de serie en entradas (BR-04).
> `is_returnable`: solo productos de categorías marcadas admiten devoluciones (BR-05).

---

### Subcategorías

```
GET  /api/v1/catalog/subcategories/          → listar
POST /api/v1/catalog/subcategories/          → crear
GET  /api/v1/catalog/subcategories/<uuid>/   → detalle
PUT  /api/v1/catalog/subcategories/<uuid>/   → actualizar
PATCH /api/v1/catalog/subcategories/<uuid>/  → parcial
```

---

### Productos

```
GET  /api/v1/catalog/products/                   → listar (solo almacenista)
POST /api/v1/catalog/products/                   → crear
GET  /api/v1/catalog/products/<uuid>/            → detalle (todos autenticados)
PUT  /api/v1/catalog/products/<uuid>/            → actualizar
PATCH /api/v1/catalog/products/<uuid>/           → parcial
GET  /api/v1/catalog/products/<uuid>/barcode/    → datos del código de barras
PATCH /api/v1/catalog/products/<uuid>/prices/    → configurar precios (solo almacenista)
GET  /api/v1/catalog/products/<uuid>/prices/     → historial de cambios de precio
```

**Request POST:**
```json
{
  "sku": "ELE-0001",
  "name": "Electroestimulador Premium",
  "category_id": "uuid-categoria",
  "subcategory_id": "uuid-subcat",
  "brand": "Medco",
  "requires_expiration": false,
  "requires_cold_chain": false,
  "reorder_point": 5,
  "notes": "Requiere carga antes de primera entrega"
}
```

SKU: 1-4 letras, guion, 1-4 dígitos. Ej: `ELE-0001`, `MED-123`.

**Response de detalle:**
```json
{
  "id": "uuid",
  "sku": "ELE-0001",
  "name": "Electroestimulador Premium",
  "barcode": "ELE-0001",
  "barcode_type": "code128",
  "barcode_payload": "ELE-0001",
  "barcode_svg": "<svg>...</svg>",
  "barcode_svg_data_uri": "data:image/svg+xml;base64,...",
  "category": { "id": "uuid", "name": "Electroterapia", ... },
  "brand": "Medco",
  "requires_expiration": false,
  "requires_cold_chain": false,
  "reorder_point": 5,
  "is_active": true,
  "unit_cost": null,
  "sale_price_retail": null,
  "sale_price_wholesale": null,
  "tax_rate_pct": null,
  "currency": "COP"
}
```

> Los campos de precio son `null` por defecto. Configurarlos via `PATCH /products/<uuid>/prices/`.

---

### Precios de producto (almacenista)

```
PATCH /api/v1/catalog/products/<uuid>/prices/   -> configurar precios
GET  /api/v1/catalog/products/<uuid>/prices/    -> historial inmutable
```

**Request PATCH (todos los campos opcionales):**
```json
{
  "unit_cost": "5000.0000",
  "sale_price_retail": "12000.0000",
  "sale_price_wholesale": "9500.0000",
  "tax_rate_pct": "19.00",
  "currency": "COP"
}
```

**Response GET (historial):**
```json
[
  {
    "id": "uuid",
    "field_changed": "sale_price_retail",
    "old_value": "10000.0000",
    "new_value": "12000.0000",
    "currency": "COP",
    "changed_by": "almacenista",
    "created_at": "2026-05-31T20:00:00Z"
  }
]
```

---

### Resolver identificador

Busca un producto por SKU, barcode o nombre (útil para escáner):

```
GET /api/v1/catalog/resolve/?identifier=ELE-0001
GET /api/v1/catalog/resolve/?identifier=ICM-0001234
```

Respuesta: objeto producto.

---

### Combos

```
GET  /api/v1/catalog/combos/                 → listar (todos autenticados)
POST /api/v1/catalog/combos/                 → crear (solo almacenista)
GET  /api/v1/catalog/combos/<uuid>/          → detalle
```

**Request POST:**
```json
{
  "name": "Kit Fisioterapia Básico",
  "sku": "KIT-001",
  "items": [
    { "product_id": "uuid-prod1", "quantity": 2 },
    { "product_id": "uuid-prod2", "quantity": 1 }
  ],
  "price_strategy": "derived",
  "fixed_price_retail": null,
  "fixed_price_wholesale": null
}
```

`price_strategy`: `"derived"` (default) o `"fixed"`. Con `"fixed"` el precio total se distribuye entre componentes por su costo unitario.

---

## Inventario

### Inventario consolidado

```
GET /api/v1/inventory/
```

Todos los autenticados. Retorna stock por producto con desglose por ubicación.

**Query params:**
| Param | Tipo | Descripción |
|---|---|---|
| `category_id` | UUID | Filtrar por categoría |
| `location_id` | UUID | Solo productos con stock en esta ubicación |
| `storage_type_id` | UUID | Solo ubicaciones de este tipo |
| `operational_status` | string | `active`, `maintenance`, `restricted`, etc. |
| `only_in_stock` | bool | Solo productos con stock > 0 |
| `stock_below_reorder` | bool | Solo productos bajo umbral de reorden |
| `export` | string | `csv` o `xlsx` para descarga |

**Response (JSON):**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/v1/inventory/?page=2",
  "previous": null,
  "results": [
    {
      "product_id": "uuid",
      "sku": "ELE-0001",
      "name": "Electroestimulador Premium",
      "category_id": "uuid",
      "reorder_point": 5,
      "total": 12,
      "by_location": [
        {
          "location_id": "uuid",
          "location_code": "BODEGA-01",
          "location_name": "Bodega Principal",
          "quantity": 8
        },
        {
          "location_id": "uuid",
          "location_code": "VITRINA",
          "location_name": "Vitrina",
          "quantity": 4
        }
      ]
    }
  ]
}
```

**Exportación:** `?export=csv` o `?export=xlsx`. Las filas están aplanadas (una por producto/ubicación).

---

### Ubicaciones

```
GET  /api/v1/inventory/locations/                         → listar
POST /api/v1/inventory/locations/                         → crear
GET  /api/v1/inventory/locations/<uuid>/                  → detalle
PUT  /api/v1/inventory/locations/<uuid>/                  → actualizar completo
PATCH /api/v1/inventory/locations/<uuid>/                 → parcial
DELETE /api/v1/inventory/locations/<uuid>/                → desactivar (baja lógica)
POST /api/v1/inventory/locations/<uuid>/state-transitions/ → cambiar estado operativo
```

**Estados operativos:**

| Estado | Puede recibir | Puede despachar | Descripción |
|---|---|---|---|
| `active` | Sí | Sí | Operación normal |
| `maintenance` | Sí | No | En mantenimiento; solo entradas |
| `restricted` | Sí | No | Restringida; solo entradas |
| `blocked` | No | No | Bloqueada; ninguna operación |
| `archived` | No | No | Permanente; `is_active=False` |

**Request POST estado:**
```json
{ "new_status": "maintenance" }
```

**Request POST ubicación:**
```json
{
  "name": "Bodega Norte",
  "description": "Almacenamiento secundario",
  "is_retail": false,
  "storage_type_id": "uuid-tipo",
  "storage_template_id": "uuid-plantilla",
  "operational_status": "active",
  "capacity_mode": "relative_scale",
  "capacity_level": 3
}
```

---

### Stock por producto

```
GET /api/v1/inventory/products/<uuid>/stock/
GET /api/v1/inventory/stock/product/<uuid>/    (alias)
```

Retorna stock en cada ubicación y total consolidado.

---

### Stock por ubicación

```
GET /api/v1/inventory/stock/location/<uuid>/
```

Retorna todos los productos con stock en esa ubicación.

---

### Umbral de stock por ubicación (NUEVO)

```
PATCH /api/v1/inventory/stock/<uuid>/threshold/
```

Solo `almacenista`. Permite definir un umbral de reorden específico para una combinación producto/ubicación. Si se establece en `null`, vuelve al umbral global del producto.

**Request:**
```json
{ "location_reorder_point": 3 }
```

Para eliminar override:
```json
{ "location_reorder_point": null }
```

**Response 200:**
```json
{
  "id": "uuid",
  "product": "uuid-producto",
  "product_sku": "ELE-0001",
  "location": "uuid-ubicacion",
  "current_stock": 7,
  "location_reorder_point": 3,
  "effective_reorder_point": 3,
  "last_movement_at": "2026-05-31T10:00:00Z"
}
```

`effective_reorder_point` es el umbral que el sistema usará al generar alertas: el local si existe, o el global del producto como fallback.

---

### Búsqueda de productos

```
GET /api/v1/inventory/search/?q=electro&category=uuid&subcategory=uuid
```

Todos los autenticados. Busca por nombre o SKU (con índice `pg_trgm` en producción).

---

### Reconstrucción de stock

```
POST /api/v1/inventory/reconstruct/
```

Solo `almacenista`. Recalcula `StockByLocation` desde el ledger de movimientos.

**Request:**
```json
{ "product_id": "uuid" }
```

O sin body para reconstruir todo el inventario.

---

## Movimientos

> El ledger de movimientos es inmutable. Los registros no se modifican; las correcciones crean nuevos movimientos relacionados.

### Listado general del ledger

```
GET /api/v1/movements/
```

Todos los autenticados.

---

### Detalle de un movimiento

```
GET /api/v1/movements/<uuid>/
```

Todos los autenticados.

**Response:**
```json
{
  "id": "uuid",
  "movement_type": "ENTRADA",
  "product": "uuid-producto",
  "product_sku": "ELE-0001",
  "lot": "uuid-lote",
  "lot_code": "LOT-2026-01",
  "lot_expiration_date": "2027-06-01",
  "origin_location": null,
  "destination_location": "uuid-ubicacion",
  "quantity": 10,
  "stock_previo_destino": 5,
  "stock_resultante_destino": 15,
  "serial_number": "SN-12345",
  "invoice_number": "ICM-000001",
  "executed_by": 1,
  "created_at": "2026-05-31T10:00:00Z"
}
```

**Tipos de movimiento:**

| Tipo | Descripción |
|---|---|
| `ENTRADA` | Recepción de mercancía |
| `SALIDA_VENTA_MAYOR` | Despacho venta al por mayor |
| `SALIDA_VENTA_MENOR` | Despacho venta al por menor |
| `SALIDA_DANO` | Baja por daño |
| `SALIDA_VENCIMIENTO` | Baja por vencimiento |
| `TRASLADO` | Traslado interno entre ubicaciones |
| `AJUSTE` | Ajuste de inventario |
| `DEVOLUCION` | Devolución de mercancía |
| `SALIDA_COMBO` | Despacho de combo (kit) |

---

### Entradas

```
GET  /api/v1/movements/entries/        → listar
POST /api/v1/movements/entries/        → registrar entrada
GET  /api/v1/movements/entries/<uuid>/ → detalle
```

Disponible para `almacenista` y `auxiliar_despacho`.

**Request POST:**
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity": 10,
  "serial_number": "SN-12345",
  "lot_code": "LOT-2026-01",
  "lot_expiration_date": "2027-06-01",
  "quantity_invoiced": 10,
  "discrepancy_note": null,
  "cold_chain_acknowledged": true,
  "electrical_safety_acknowledged": true
}
```

- `serial_number`: requerido si `category.requires_serial_number = true`.
- `lot_code` + `lot_expiration_date`: requeridos si `product.requires_expiration = true`.
- `cold_chain_acknowledged` / `electrical_safety_acknowledged`: requeridos según la categoría.

**Response 201:** objeto Movement.

---

### Despachos

```
GET  /api/v1/movements/dispatches/                   → listar
POST /api/v1/movements/dispatches/                   → registrar despacho
GET  /api/v1/movements/dispatches/<uuid>/             → detalle
GET  /api/v1/movements/dispatches/<uuid>/invoice/     → PDF comprobante legacy (sin precio)
GET  /api/v1/movements/invoices/<number>/             → detalle de factura comercial con totales
GET  /api/v1/movements/invoices/<number>/pdf/         → PDF enriquecido con precios
```

Disponible para `almacenista` y `auxiliar_despacho`.

**Request POST (venta menor):**
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity": 2,
  "movement_type": "SALIDA_VENTA_MENOR",
  "cold_chain_acknowledged": true,
  "electrical_safety_acknowledged": false,
  "privacy_notice_acknowledged": false,
  "discount_pct": "10.00"
}
```

`discount_pct` es opcional. Si el producto no tiene precio, se ignora sin error.

**Request POST (venta mayor — requiere datos del cliente):**
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity": 20,
  "movement_type": "SALIDA_VENTA_MAYOR",
  "customer_data": {
    "customer_name": "Clínica Los Andes",
    "customer_email": "compras@clinica.co",
    "customer_phone": "+573001234567",
    "customer_address": "Cra 7 # 32-16, Bogotá",
    "privacy_notice_acknowledged": true
  },
  "cold_chain_acknowledged": true,
  "electrical_safety_acknowledged": false,
  "privacy_notice_acknowledged": true
}
```

> Los despachos multi-lote se resuelven automáticamente con política FEFO (First Expired, First Out).

**Campos de precio en la respuesta** (`null` si el producto no tiene precio configurado):
```json
{
  "unit_price": "12000.0000",   "subtotal": "24000.0000",
  "tax_rate_pct": "19.00",      "tax_amount": "4560.0000",
  "total_amount": "28560.0000", "currency": "COP",
  "price_type": "retail",       "customer_snapshot": null
}
```

**Factura comercial** (creada automáticamente en cada despacho):
```
GET /api/v1/movements/invoices/ICM-0001/      -> detalle con totales
GET /api/v1/movements/invoices/ICM-0001/pdf/  -> PDF con precios
```

---

### Traslados internos

```
GET  /api/v1/movements/transfers/       → listar
POST /api/v1/movements/transfers/       → registrar traslado
```

**Request POST:**
```json
{
  "product_id": "uuid",
  "origin_id": "uuid-ubicacion-origen",
  "destination_id": "uuid-ubicacion-destino",
  "quantity": 5,
  "cold_chain_acknowledged": true,
  "electrical_safety_acknowledged": false
}
```

---

### Devoluciones

Solo `almacenista`.

```
GET  /api/v1/movements/returns/    → listar
POST /api/v1/movements/returns/    → registrar devolución
```

**Request POST:**
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity": 1,
  "serial_number": "SN-12345"
}
```

Solo categorías con `is_returnable = true` (BR-05).

---

### Ajustes

Solo `almacenista`.

```
GET  /api/v1/movements/adjustments/         → listar
POST /api/v1/movements/adjustments/         → registrar ajuste
POST /api/v1/movements/adjustments/correct/ → corregir ajuste
```

**Request POST:**
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity": -3,
  "justification": "Productos dañados detectados en conteo"
}
```

`justification` es obligatoria (BR-07). Quantity puede ser negativo (baja) o positivo (alta).

---

### Corrección dentro de ventana (BR-06)

```
POST /api/v1/movements/<uuid>/corrections/
```

Disponible para `almacenista` y `auxiliar_despacho`. Ventana de 5 minutos. Solo el autor del movimiento puede corregirlo.

**Tipos corregibles:** `TRASLADO`, `ENTRADA`, `SALIDA_VENTA_MAYOR`, `SALIDA_VENTA_MENOR`.

**Request para TRASLADO:**
```json
{
  "origin_id": "uuid-nuevo-origen",
  "destination_id": "uuid-nuevo-destino",
  "quantity": 3
}
```

**Request para ENTRADA:**
```json
{
  "location_id": "uuid-nueva-ubicacion",
  "quantity": 8
}
```

**Request para SALIDA:**
```json
{
  "location_id": "uuid-ubicacion",
  "quantity": 5,
  "movement_type": "SALIDA_VENTA_MENOR"
}
```

**Response 200:** array con 2 movimientos: `[reversal, corrected]`.

---

### Despacho de combo

```
POST /api/v1/movements/combo-dispatch/
```

Disponible para `almacenista` y `auxiliar_despacho`. Descuenta stock por cada ítem del combo.

**Request:**
```json
{
  "combo_id": "uuid-combo",
  "location_id": "uuid-ubicacion"
}
```

**Response 201:** array de movimientos SALIDA_COMBO (uno por ítem).

**Errores:**
- `404` — combo no existe o está inactivo
- `409` — stock insuficiente para algún ítem

---

## Dashboard

Solo `almacenista`. Read model operacional.

| Endpoint | Descripción | Params |
|---|---|---|
| `GET /api/v1/dashboard/overview/` | Resumen general | `period_days` (1-365) |
| `GET /api/v1/dashboard/metrics/` | Métricas del día | `period_days` |
| `GET /api/v1/dashboard/alerts/` | Alertas críticas activas | `expiring_days` |
| `GET /api/v1/dashboard/kpis/` | KPIs con valores numéricos | `period_days` |
| `GET /api/v1/dashboard/movements/` | Movimientos recientes | `period_days`, `limit` |

---

## Reportes y exportación

Disponible para `almacenista` y `administrador`.

### Historial de movimientos

```
GET /api/v1/reports/movements/history/
GET /api/v1/reports/movements/history/?export=csv
GET /api/v1/reports/movements/history/?export=xlsx
```

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `product_id` | UUID | Filtrar por producto |
| `location_id` | UUID | Filtrar por ubicación (origen o destino) |
| `user_id` | int | Filtrar por usuario ejecutor |
| `start` | ISO-8601 | Fecha inicio |
| `end` | ISO-8601 | Fecha fin |
| `export` | string | `csv` o `xlsx` |

Límite interno: 200 registros en JSON. Sin límite en CSV/XLSX (aunque XLSX limita a 10 000 filas).

---

### Productos próximos a vencer

```
GET /api/v1/reports/expiring/?days=30
GET /api/v1/reports/expiring/?days=30&export=csv
```

`days`: 1–365. Retorna lotes con vencimiento en ese número de días.

---

### Inventario por categoría

```
GET /api/v1/reports/inventory/summary/
```

---

### Exportación de inventario consolidado

```
GET /api/v1/inventory/?export=csv
GET /api/v1/inventory/?export=xlsx
```

Las filas están aplanadas: una fila por combinación producto/ubicación.

Columnas: `sku`, `name`, `reorder_point`, `total`, `location_code`, `location_name`, `quantity`.

---

### Reportes financieros

Disponible para `almacenista` y `administrador`.

```
GET /api/v1/reports/revenue-summary/       -> revenue por tipo de venta
GET /api/v1/reports/margin-by-product/     -> margen bruto por SKU
GET /api/v1/reports/sales-by-customer/     -> ventas por cliente (venta mayor)
```

**Query params comunes:**

| Param | Descripcion |
|---|---|
| `start` | Inicio del periodo ISO-8601 (default: hace 30 dias) |
| `end` | Fin del periodo ISO-8601 (default: ahora) |
| `limit` | Solo margin y customer. Maximo de resultados (default 50) |

**Response `revenue-summary`:**
```json
{
  "wholesale": { "units": 50, "subtotal": "475000.0000", "tax": "90250.0000", "total": "565250.0000" },
  "retail":    { "units": 30, "subtotal": "360000.0000", "tax": "68400.0000",  "total": "428400.0000" },
  "combined":  { "units": 80, "subtotal": "835000.0000", "tax": "158650.0000", "total": "993650.0000" }
}
```

**Response `margin-by-product`:**
```json
[
  { "sku": "CM-01", "units": 5, "revenue": "60000.0000", "cogs": "25000.0000", "gross_margin": "35000.0000", "gross_margin_pct": "58.33" }
]
```

> Retornan `0` o lista vacia si los productos no tienen precio. Nunca un error.

---

### Cómo funciona la exportación

- **CSV:** descarga directa como `StreamingHttpResponse`. Seguro para datasets grandes.
- **XLSX:** en memoria con `openpyxl`. Límite de 10 000 filas. Si se supera:
  - La última fila contiene un aviso de truncamiento.
  - El header de respuesta incluye `X-Export-Truncated: true` y `X-Export-Row-Limit: 10000`.
  - Para datasets completos, usar `?export=csv`.

---

## Alertas y polling

### Alertas activas

```
GET /api/v1/alerts/
GET /api/v1/alerts/?export=csv
```

Solo `almacenista` y `administrador`.

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `alert_type` | string | Ej: `LOW_STOCK`, `EXPIRATION_30` |
| `severity` | string | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` |
| `category` | string | `STOCK`, `EXPIRATION`, `LOCATION`, `INTEGRITY` |
| `product_id` | UUID | Filtrar por producto |
| `location_id` | UUID | Filtrar por ubicación |
| `date_from` | date | Fecha desde (YYYY-MM-DD) |
| `date_to` | date | Fecha hasta |
| `export` | string | `csv` o `xlsx` |

**Tipos de alerta:**

| Tipo | Severidad | Categoría | Descripción |
|---|---|---|---|
| `LOW_STOCK` | HIGH | STOCK | Stock por debajo del umbral de reorden |
| `STOCK_ZERO` | MEDIUM | STOCK | Producto sin stock |
| `EXPIRATION_30` | CRITICAL | EXPIRATION | Vence en 30 días |
| `EXPIRATION_60` | HIGH | EXPIRATION | Vence en 60 días |
| `LOT_EXPIRED` | CRITICAL | EXPIRATION | Lote ya vencido |
| `COLD_CHAIN_MISSING` | HIGH | LOCATION | Cadena de frío irregular |
| `LOCATION_BLOCKED_WITH_STOCK` | HIGH | LOCATION | Ubicación bloqueada tiene stock |
| `STOCK_MISMATCH` | CRITICAL | INTEGRITY | Discrepancia caché vs. ledger |

---

### Polling de alertas (NUEVO)

```
GET /api/v1/alerts/poll/
```

Disponible para **todos los usuarios autenticados** (sin restricción de rol).

**Query params:**

| Param | Tipo | Requerido | Descripción |
|---|---|---|---|
| `since` | ISO-8601 | No | Solo alertas creadas después de este momento. Default: últimas 24 h |
| `severity` | string | No | Severidades separadas por coma. Ej: `CRITICAL,HIGH` |

**Response 200:**
```json
{
  "server_timestamp": "2026-05-31T14:00:00.000000+00:00",
  "count": 2,
  "results": [
    {
      "id": 42,
      "alert_type": "LOW_STOCK",
      "severity": "HIGH",
      "category": "STOCK",
      "product": "uuid-producto",
      "product_sku": "ELE-0001",
      "lot": null,
      "lot_code": null,
      "lot_expiration_date": null,
      "location": "uuid-ubicacion",
      "message": "Stock en BODEGA-01 (3) en o por debajo del umbral 5.",
      "is_resolved": false,
      "resolved_at": null,
      "resolved_by": null,
      "created_at": "2026-05-31T13:55:00Z"
    }
  ]
}
```

**Patrón de integración recomendado:**

```javascript
// Inicializar con el timestamp actual
let since = new Date().toISOString();

async function pollAlerts() {
  const url = `/api/v1/alerts/poll/?since=${encodeURIComponent(since)}&severity=CRITICAL,HIGH`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` }
  });
  const data = await res.json();

  if (data.results.length > 0) {
    // Mostrar notificaciones
    handleNewAlerts(data.results);
  }

  // Usar server_timestamp para el próximo poll
  since = data.server_timestamp;
}

// Ejecutar cada 30 segundos
setInterval(pollAlerts, 30_000);
```

> Máximo 50 alertas por request. Errores: `400` si `since` tiene formato inválido.

---

### Historial de alertas resueltas

```
GET /api/v1/alerts/history/
```

Mismos filtros que `/alerts/`.

---

### Estadísticas de alertas

```
GET /api/v1/alerts/stats/
```

**Response:**
```json
{
  "total_active": 12,
  "by_severity": {
    "CRITICAL": 3,
    "HIGH": 5,
    "MEDIUM": 4,
    "LOW": 0,
    "INFO": 0
  },
  "by_category": {
    "STOCK": 7,
    "EXPIRATION": 3,
    "LOCATION": 1,
    "INTEGRITY": 1
  }
}
```

---

### Resolver alerta

```
POST /api/v1/alerts/<pk>/resolve/
```

Solo `almacenista`. Sin body. Marca la alerta como resuelta.

**Response 200:** objeto Alert actualizado.

---

## Auditoría

Solo `almacenista` y `administrador`. Solo lectura.

```
GET /api/v1/audit/           → listar logs (paginado)
GET /api/v1/audit/<uuid>/    → detalle log
```

**Filtros disponibles:** `event_type`, `user_id`, `start`, `end`.

**Respuesta de un log:**
```json
{
  "id": "uuid",
  "event_type": "MOVEMENT_CREATED",
  "user": 1,
  "movement": "uuid-movement",
  "description": "Entrada de mercancía",
  "metadata": { "type": "ENTRADA" },
  "ip_address": "192.168.1.10",
  "created_at": "2026-05-31T10:00:00Z"
}
```

**Tipos de evento de auditoría:**

| Tipo | Descripción |
|---|---|
| `LOGIN_SUCCESS` | Login exitoso |
| `LOGIN_FAILED` | Intento de login fallido |
| `LOGOUT` | Cierre de sesión |
| `USER_CREATED` | Usuario creado |
| `USER_UPDATED` | Usuario actualizado |
| `USER_DISABLED` | Cuenta deshabilitada |
| `MOVEMENT_CREATED` | Movimiento registrado |
| `MOVEMENT_CORRECTED` | Corrección BR-06 aplicada |
| `ADJUSTMENT_CREATED` | Ajuste de inventario |
| `RETURN_CREATED` | Devolución registrada |
| `PRODUCT_CREATED` | Producto creado |
| `PRODUCT_UPDATED` | Producto actualizado |
| `COMBO_CREATED` | Combo creado |
| `STOCK_RECONSTRUCTED` | Stock reconstruido desde ledger |
| `ALERT_ACKNOWLEDGED` | Alerta reconocida |
| `UNAUTHORIZED_ACCESS_ATTEMPT` | Intento de acceso no autorizado |
| `MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD` | Intento de modificar ledger |

---

## Webhooks

Solo `almacenista` (`IsAlmacenista` — rol rector del sistema). Permite notificar a sistemas externos cuando ocurren eventos críticos.

> El rol `administrador` es de solo lectura y **no tiene acceso** a los webhooks.

### Crear endpoint de webhook

```
POST /api/v1/webhooks/endpoints/
```

**Request:**
```json
{
  "url": "https://mi-erp.ejemplo.com/webhooks/icm",
  "secret": "clave_secreta_minimo_8_chars",
  "events": ["LOW_STOCK"],
  "is_active": true,
  "max_retries": 3
}
```

**Eventos disponibles:**

| Evento | Cuándo |
|---|---|
| `LOW_STOCK` | Stock cae al umbral de reorden o por debajo |
| `STOCK_INTEGRITY_DIVERGENCE` | El command `verify_stock_integrity` detecta discrepancia |

**Response 201:**
```json
{
  "id": "uuid",
  "url": "https://mi-erp.ejemplo.com/webhooks/icm",
  "events": ["LOW_STOCK"],
  "is_active": true,
  "max_retries": 3,
  "created_by": 1,
  "created_at": "2026-05-31T10:00:00Z"
}
```

> El campo `secret` es `write_only`; no aparece en respuestas GET.

---

### Listar / gestionar endpoints

```
GET    /api/v1/webhooks/endpoints/              → listar
GET    /api/v1/webhooks/endpoints/<uuid>/       → detalle
PATCH  /api/v1/webhooks/endpoints/<uuid>/       → actualizar
DELETE /api/v1/webhooks/endpoints/<uuid>/       → desactivar (is_active=False)
```

---

### Probar endpoint

```
POST /api/v1/webhooks/endpoints/<uuid>/test/
```

**Request:**
```json
{
  "event_type": "TEST",
  "payload": { "mensaje": "prueba de conectividad" }
}
```

**Response 200:**
```json
{ "status": "DELIVERED", "response_code": 200 }
```

O `"status": "FAILED"` si el endpoint no respondió.

---

### Historial de entregas

```
GET /api/v1/webhooks/deliveries/
```

**Respuesta:**
```json
{
  "results": [
    {
      "id": "uuid",
      "endpoint": "uuid-endpoint",
      "endpoint_url": "https://mi-erp.ejemplo.com/webhooks/icm",
      "event_type": "LOW_STOCK",
      "status": "DELIVERED",
      "attempts": 1,
      "last_attempt_at": "2026-05-31T10:05:00Z",
      "next_retry_at": null,
      "response_code": 200,
      "created_at": "2026-05-31T10:00:00Z"
    }
  ]
}
```

**Estados:** `PENDING`, `DELIVERED`, `FAILED`.

---

### Estadísticas de webhooks

```
GET /api/v1/webhooks/stats/
```

```json
{
  "pending": 3,
  "delivered": 142,
  "failed": 2,
  "active_endpoints": 1
}
```

---

### Cómo implementar el receptor (backend del ERP/frontend)

```python
import hashlib, hmac
from flask import request, abort

SECRET = "clave_secreta_minimo_8_chars"

@app.route("/webhooks/icm", methods=["POST"])
def receive_webhook():
    body = request.get_data()
    signature = request.headers.get("X-ICM-Signature", "")

    expected = "sha256=" + hmac.new(
        SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        abort(401)  # firma inválida

    event_type = request.headers.get("X-ICM-Event")
    data = request.get_json()
    # procesar data...
    return "", 200
```

**Headers que envía ICM:**
- `Content-Type: application/json`
- `X-ICM-Signature: sha256=<hmac-hex>`
- `X-ICM-Event: <event_type>`

**Política de reintentos:** El sistema reintenta con backoff exponencial (1 min → 5 min → 30 min) hasta `max_retries` veces. Responder con cualquier HTTP 2xx se considera éxito.

---

## Errores

Todos los errores siguen el formato uniforme:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Error de validación en la solicitud.",
  "detail": {
    "quantity": ["Este campo es requerido."],
    "location_id": ["UUID inválido."]
  }
}
```

**Códigos de error (`error`):**

| Código | HTTP | Descripción |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Campos inválidos, formato incorrecto |
| `NOT_AUTHENTICATED` | 401 | Token ausente, inválido o expirado |
| `PERMISSION_DENIED` | 403 | Sin permisos (rol incorrecto o horario) |
| `NOT_FOUND` | 404 | Recurso no existe |
| `METHOD_NOT_ALLOWED` | 405 | Método HTTP no permitido |
| `CONFLICT` | 409 | Conflicto de negocio (stock insuficiente, etc.) |
| `THROTTLED` | 429 | Límite de requests excedido |
| `CLIENT_ERROR` | 4xx | Error genérico de cliente |
| `UNHANDLED_ERROR` | 500 | Error inesperado del servidor |

**Errores de dominio comunes:**

| Escenario | HTTP | `error` |
|---|---|---|
| Stock insuficiente para despacho | 409 | `CONFLICT` |
| Corrección fuera de ventana 5 min | 409 | `CONFLICT` |
| Producto no retornable | 409 | `CONFLICT` |
| Ubicación bloqueada | 409 | `CONFLICT` |
| SKU con formato inválido | 400 | `VALIDATION_ERROR` |
| Serial requerido pero ausente | 422 | `VALIDATION_ERROR` |
| Lote requerido pero ausente | 422 | `VALIDATION_ERROR` |
| Auxiliar fuera de horario | 403 | `PERMISSION_DENIED` |
| Token expirado | 401 | `NOT_AUTHENTICATED` |

---

## Paginación

Los listados están paginados. Respuesta estándar:

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/catalog/products/?page=2",
  "previous": null,
  "results": [...]
}
```

**Query params:**
- `page`: número de página (default: 1)
- `page_size`: registros por página (default: 20, max: 100)

---

## Tipos de datos

| Tipo | Formato | Ejemplo |
|---|---|---|
| UUID | String RFC-4122 | `"a1f808fc-66f0-4686-8ce0-4940cec7906e"` |
| Fecha | ISO-8601 date | `"2027-06-01"` |
| DateTime | ISO-8601 con TZ | `"2026-05-31T10:00:00Z"` |
| Boolean | JSON bool | `true`, `false` |
| Integer | JSON number | `10`, `-3` |
| SKU | Patrón | `"ELE-0001"` (1-4 letras, guion, 1-4 dígitos) |
| Decimal | String numérico | `"12000.0000"` (4 cifras decimales, entre comillas) |

---

## Descripción de roles

> ⚠️ Los nombres de rol en código NO coinciden con la intuición habitual. Leer con atención.

| Rol (`role`) | Permiso DRF | Descripción |
|---|---|---|
| `almacenista` | `IsAlmacenista` | **Control total.** Rol rector del sistema (BR-02). Gestiona usuarios, catálogo, inventario, movimientos, webhooks y dashboard. |
| `auxiliar_despacho` | `IsAuxiliarDespacho` | Operaciones de campo dentro de franja horaria 07:00–12:00 y 14:00–17:00 (BR-03). |
| `administrador` | `IsAdministrador` | **Solo lectura.** Puede ver reportes, alertas y auditoría. No puede crear ni modificar nada operativo. |

## Acceso rápido por acción

| Acción | `almacenista` | `auxiliar_despacho` | `administrador` |
|---|---|---|---|
| Login | ✅ | ✅ (horario) | ✅ |
| Crear usuarios | ✅ | ❌ | ❌ |
| Gestionar catálogo | ✅ | ❌ | ❌ |
| Ver inventario | ✅ | ✅ | ✅ |
| Registrar entradas | ✅ | ✅ | ❌ |
| Registrar despachos | ✅ | ✅ | ❌ |
| Registrar traslados | ✅ | ✅ | ❌ |
| Gestionar devoluciones | ✅ | ❌ | ❌ |
| Ajustes de inventario | ✅ | ❌ | ❌ |
| Ver dashboard | ✅ | ❌ | ❌ |
| Ver reportes | ✅ | ❌ | ✅ |
| Ver alertas | ✅ | ❌ | ✅ |
| Polling alertas | ✅ | ✅ | ✅ |
| Ver auditoría | ✅ | ❌ | ✅ |
| Gestionar webhooks | ✅ | ❌ | ❌ |
| Configurar precios de producto | ✅ | ❌ | ❌ |
| Ver facturas comerciales | ✅ | ✅ | ❌ |
| Ver reportes financieros | ✅ | ❌ | ✅ |

Para la matriz completa de cada endpoint, ver [README_MATRIZ_PERMISOS.md](README_MATRIZ_PERMISOS.md).

---

*Actualizado: 2026-05-31. Sincronizado con el estado real del código (508 tests, production-readiness ~95%).*
