# Plantilla de Endpoints — Sistema Inventario ICM

**Inventario completo de la API, generado desde `config/urls.py` + `apps/*/urls.py`.**

A diferencia de [REFERENCIA_ENDPOINTS.md](REFERENCIA_ENDPOINTS.md) (que usa datos de
ejemplo reales para los flujos principales), este documento cubre **todos** los
endpoints existentes — incluidos los menos usados (soft-delete, restauración,
reportes operativos) — con cuerpos de request/response en **placeholders genéricos**,
listos para usarse como base de colección Postman/Insomnia o checklist de integración.

> Si un endpoint ya tiene un ejemplo completo y real en REFERENCIA_ENDPOINTS.md, aquí
> se referencia en vez de duplicarlo.

---

## Convención de placeholders

| Placeholder | Significado |
|---|---|
| `<uuid>` | UUID v4 (la mayoría de IDs del sistema) |
| `<int>` | Entero (PK numérica de `Invoice`, `Alert`, `AuditLog`-int, paginación) |
| `<string>` | Texto libre |
| `<bool>` | `true` / `false` |
| `<decimal>` | String numérico con 4 decimales, ej. `"12000.0000"` |
| `<date>` | `"YYYY-MM-DD"` |
| `<datetime>` | ISO-8601 con TZ, ej. `"2026-06-16T10:00:00Z"` |
| `<enum: a\|b\|c>` | Uno de los valores listados |
| `null` | Puede ser nulo explícitamente |
| *(sin body)* | El método no requiere cuerpo de request |

**Patrón soft-delete** (se repite en catalog, inventory, purchasing, webhooks): cada
recurso con baja lógica expone `POST .../<uuid>/disable/` (marca `is_active=False`,
nunca bloquea relaciones históricas), `POST .../<uuid>/enable/` (reactiva) y
`POST .../<uuid>/restore/` (revierte `deleted_at`). Las tres son *sin body* y
retornan el objeto actualizado con el mismo esquema que el detalle (`GET .../<uuid>/`).

---

## Índice

- [Autenticación](#autenticacion)
- [Catálogo](#catalogo)
- [Inventario](#inventario)
- [Movimientos](#movimientos)
- [Facturación](#facturacion)
- [Compras](#compras)
- [Dashboard](#dashboard)
- [Reportes](#reportes)
- [Alertas](#alertas)
- [Auditoría](#auditoria)
- [Webhooks](#webhooks)

---

## Autenticación

Base: `/api/v1/auth/`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `health/` | público | Health check |
| POST | `login/` | público | Login (auxiliar solo en horario) |
| POST | `token/refresh/` | público | Renovar access token |
| POST | `logout/` | autenticado | Invalida refresh token |
| GET | `me/` | autenticado | Perfil propio |
| GET, POST | `users/` | almacenista | Listar / crear usuarios |
| GET, PUT, PATCH | `users/<uuid:pk>/` | almacenista | Detalle / actualizar usuario |
| POST | `users/<uuid:pk>/disable/` | almacenista | Deshabilitar usuario |
| POST | `users/<uuid:pk>/enable/` | almacenista | Reactivar usuario |
| GET, PUT | `users/<uuid:pk>/schedule/` | almacenista | Horario personalizado del usuario |
| GET, POST | `users/<uuid:pk>/temporary-permits/` | almacenista | Permisos temporales de horario |
| POST | `temporary-permits/<uuid:pk>/revoke/` | almacenista | Revocar permiso temporal |
| POST | `change-password/` | autenticado | Cambiar contraseña propia |
| POST | `forgot-password/` | público | Solicitar enlace de recuperación |
| POST | `reset-password/` | público | Restablecer contraseña con token |

**Request `POST login/`:**
```json
{ "email": "<string>", "password": "<string>" }
```

**Request `POST users/`:**
```json
{
  "username": "<string>",
  "email": "<string>",
  "password": "<string>",
  "first_name": "<string>",
  "last_name": "<string>",
  "role": "<enum: almacenista|auxiliar_despacho|administrador>",
  "phone": "<string>"
}
```

**Response (objeto usuario):**
```json
{
  "id": "<uuid>",
  "username": "<string>",
  "email": "<string>",
  "first_name": "<string>",
  "last_name": "<string>",
  "phone": "<string>",
  "role": "<enum: almacenista|auxiliar_despacho|administrador>",
  "is_active": "<bool>"
}
```

**Request/Response `users/<uuid:pk>/schedule/` (PUT):**
```json
{
  "morning_start": "<string: HH:MM>",
  "morning_end": "<string: HH:MM>",
  "afternoon_start": "<string: HH:MM>",
  "afternoon_end": "<string: HH:MM>",
  "is_active": "<bool>"
}
```

**Request `POST users/<uuid:pk>/temporary-permits/`:**
```json
{
  "start_datetime": "<datetime>",
  "end_datetime": "<datetime>",
  "allow_24_7": "<bool>",
  "custom_morning_start": "<string: HH:MM>",
  "custom_morning_end": "<string: HH:MM>",
  "custom_afternoon_start": "<string: HH:MM>",
  "custom_afternoon_end": "<string: HH:MM>"
}
```

**Request `change-password/`:**
```json
{
  "current_password": "<string>",
  "new_password": "<string>",
  "new_password_confirm": "<string>"
}
```

**Request `forgot-password/`:** `{ "email": "<string>" }`

**Request `reset-password/`:**
```json
{ "token": "<string>", "new_password": "<string>", "new_password_confirm": "<string>" }
```

---

## Catálogo

Base: `/api/v1/catalog/`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET, POST | `categories/` | autenticado / almacenista | Listar / crear categoría |
| GET, PUT, PATCH | `categories/<uuid:pk>/` | — | Detalle / actualizar categoría |
| POST | `categories/<uuid:pk>/disable/` | almacenista | Soft-delete (ver convención arriba) |
| POST | `categories/<uuid:pk>/enable/` | almacenista | — |
| POST | `categories/<uuid:pk>/restore/` | almacenista | — |
| GET, POST | `brands/` | autenticado / almacenista | Listar / crear marca |
| GET, PUT, PATCH | `brands/<uuid:pk>/` | — | Detalle / actualizar marca |
| POST | `brands/<uuid:pk>/disable/` `/enable/` `/restore/` | almacenista | Soft-delete |
| GET, POST | `products/` | almacenista | Listar / crear producto |
| GET, PUT, PATCH | `products/<uuid:pk>/` | autenticado | Detalle / actualizar producto |
| GET | `products/<uuid:pk>/barcode/` | autenticado | Datos de código de barras |
| GET, PATCH | `products/<uuid:pk>/prices/` | almacenista | Historial / configurar precios |
| POST | `products/<uuid:pk>/disable/` `/enable/` `/restore/` | almacenista | Soft-delete |
| GET | `products/resolve/`, `resolve/` | autenticado | Resolver por SKU/barcode/nombre (`?identifier=`) |
| GET, POST | `combos/` | autenticado / almacenista | Listar / crear combo |
| GET | `combos/<uuid:pk>/` | autenticado | Detalle de combo |
| POST | `combos/<uuid:pk>/restore/` | almacenista | Restaurar combo eliminado |

**Request `POST categories/`:**
```json
{
  "name": "<string>",
  "slug": "<string>",
  "requires_serial_number": "<bool>",
  "is_returnable": "<bool>",
  "description": "<string>"
}
```

**Request `POST brands/`:**
```json
{ "name": "<string>", "slug": "<string>", "description": "<string>" }
```

**Request `POST products/`:**
```json
{
  "sku": "<string: 1-4 letras, guion, 1-4 digitos>",
  "name": "<string>",
  "category_id": "<uuid>",
  "brand_id": "<uuid>",
  "requires_expiration": "<bool>",
  "requires_cold_chain": "<bool>",
  "reorder_point": "<int>",
  "notes": "<string>"
}
```

**Request `PATCH products/<uuid:pk>/prices/`:**
```json
{
  "unit_cost": "<decimal>",
  "sale_price_retail": "<decimal>",
  "sale_price_wholesale": "<decimal>",
  "tax_rate_pct": "<decimal>",
  "currency": "<string: COP>"
}
```

**Request `POST combos/`:**
```json
{
  "name": "<string>",
  "sku": "<string>",
  "items": [ { "product_id": "<uuid>", "quantity": "<int>" } ],
  "price_strategy": "<enum: derived|fixed>",
  "fixed_price_retail": "<decimal>",
  "fixed_price_wholesale": "<decimal>"
}
```

**Response (Product, detalle):** ver ejemplo completo en
[REFERENCIA_ENDPOINTS.md → Productos](REFERENCIA_ENDPOINTS.md#productos).

---

## Inventario

Base: `/api/v1/inventory/`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `` (raíz) | autenticado | Inventario consolidado (`?export=csv\|xlsx`) |
| GET, POST | `storage-types/` | autenticado / almacenista | Listar / crear tipo de almacenamiento |
| GET, PUT, PATCH | `storage-types/<uuid:pk>/` | — | Detalle / actualizar |
| POST | `storage-types/<uuid:pk>/disable/` `/enable/` `/restore/` | almacenista | Soft-delete |
| GET, POST | `storage-templates/` | autenticado / almacenista | Listar / crear plantilla |
| GET, PUT, PATCH | `storage-templates/<uuid:pk>/` | — | Detalle / actualizar |
| POST | `storage-templates/<uuid:pk>/disable/` `/enable/` `/restore/` | almacenista | Soft-delete |
| GET, POST | `locations/` | autenticado / almacenista | Listar / crear ubicación |
| GET, PUT, PATCH | `locations/<uuid:pk>/` | — | Detalle / actualizar |
| POST | `locations/<uuid:pk>/restore/` | almacenista | Restaurar ubicación |
| POST | `locations/<uuid:pk>/state-transitions/` | almacenista | Cambiar estado operativo |
| POST | `reconstruct/` | almacenista | Reconstruir stock desde el ledger |
| GET | `products/<uuid:product_id>/stock/`, `stock/product/<uuid:product_id>/` | autenticado | Stock de un producto por ubicación |
| GET | `stock/location/<uuid:location_id>/` | autenticado | Stock de una ubicación |
| GET | `search/` | autenticado | Búsqueda de productos (`?q=`) |
| PATCH | `stock/<uuid:pk>/threshold/` | almacenista | Umbral de reorden por ubicación |

**Request `POST storage-types/`:**
```json
{
  "code": "<string>",
  "name": "<string>",
  "category": "<string>",
  "description": "<string>",
  "capabilities": { "<string>": "<string>" },
  "default_is_retail": "<bool>",
  "sort_order": "<int>"
}
```

**Request `POST storage-templates/`:**
```json
{
  "code": "<string>",
  "name": "<string>",
  "storage_type_id": "<uuid>",
  "description": "<string>"
}
```

**Request `POST locations/`:** ver ejemplo real en
[REFERENCIA_ENDPOINTS.md → Ubicaciones](REFERENCIA_ENDPOINTS.md#ubicaciones).

**Request `POST locations/<uuid:pk>/state-transitions/`:**
```json
{ "new_status": "<enum: active|maintenance|restricted|blocked|archived>" }
```

**Request `POST reconstruct/`:** `{ "product_id": "<uuid>" }` *(opcional; sin body reconstruye todo)*

**Request `PATCH stock/<uuid:pk>/threshold/`:**
```json
{ "location_reorder_point": "<int o null>" }
```

---

## Movimientos

Base: `/api/v1/movements/`

> Ledger inmutable — las correcciones crean movimientos nuevos relacionados, nunca
> modifican uno existente (BR-10).

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `` (raíz) | autenticado | Listado general del ledger |
| GET | `<uuid:pk>/` | autenticado | Detalle de un movimiento |
| GET, POST | `entries/` | almacenista, auxiliar | Listar / registrar entrada |
| GET | `entries/<uuid:pk>/` | autenticado | Detalle de entrada |
| GET, POST | `dispatches/` | almacenista, auxiliar | Listar / registrar despacho |
| GET | `dispatches/<uuid:pk>/` | autenticado | Detalle de despacho |
| GET | `dispatches/<uuid:pk>/invoice/` | autenticado | PDF legacy (sin precio) |
| GET, POST | `transfers/` | almacenista, auxiliar | Listar / registrar traslado |
| GET, POST | `returns/` | almacenista | Listar / registrar devolución |
| GET, POST | `adjustments/` | almacenista | Listar / registrar ajuste |
| POST | `adjustments/correct/` | almacenista | Corregir ajuste |
| POST | `<uuid:pk>/corrections/` | almacenista, auxiliar | Corrección dentro de ventana 5 min (BR-06) |
| POST | `combo-dispatch/` | almacenista, auxiliar | Despachar un combo (un solo combo, ver [Facturación](#facturacion) para mezclar con productos) |
| GET | `invoices/<str:number>/` | autenticado | Detalle de factura comercial |
| GET | `invoices/<str:number>/pdf/` | autenticado | PDF enriquecido con precios |

**Request `POST entries/`, `POST dispatches/`, `POST transfers/`, `POST returns/`,
`POST adjustments/`, `POST combo-dispatch/`, `POST <uuid:pk>/corrections/`:** ver
ejemplos reales completos en
[REFERENCIA_ENDPOINTS.md → Movimientos](REFERENCIA_ENDPOINTS.md#movimientos)
(incluye placeholders de `cold_chain_acknowledged`, `serial_number`, `lot_code`,
`customer_data`, `discount_pct`, etc. ya documentados ahí).

**Response (Movement, esquema base):**
```json
{
  "id": "<uuid>",
  "movement_type": "<enum: ENTRADA|SALIDA_VENTA_MAYOR|SALIDA_VENTA_MENOR|SALIDA_DANO|SALIDA_VENCIMIENTO|TRASLADO|AJUSTE|DEVOLUCION|SALIDA_COMBO|ANULACION>",
  "product": "<uuid>",
  "product_sku": "<string>",
  "lot": "<uuid o null>",
  "origin_location": "<uuid o null>",
  "destination_location": "<uuid o null>",
  "quantity": "<int>",
  "serial_number": "<string o null>",
  "invoice_number": "<string o null>",
  "unit_price": "<decimal o null>",
  "subtotal": "<decimal o null>",
  "tax_amount": "<decimal o null>",
  "total_amount": "<decimal o null>",
  "executed_by": "<int>",
  "created_at": "<datetime>"
}
```

---

## Facturación

Base: `/api/v1/billing/`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET, POST | `invoices/` | almacenista+admin (GET) / almacenista+auxiliar (POST) | Listar / crear factura multi-ítem (producto y/o combo) |
| GET | `invoices/<int:pk>/` | almacenista, administrador | Detalle de factura |
| POST | `invoices/<int:pk>/void/` | almacenista | Anular factura (revierte stock) |
| GET | `invoices/stats/` | almacenista, administrador | Estadísticas de ventas (hoy / mes) |
| GET, PUT | `config/company/` | almacenista (PUT) | Datos fiscales de la empresa |

Ejemplos completos de request/response (incluida la mezcla combo + producto en el
mismo carrito) en
[REFERENCIA_ENDPOINTS.md → Facturación](REFERENCIA_ENDPOINTS.md#facturacion).

**Request `POST invoices/` (esquema de placeholders):**
```json
{
  "invoice_type": "<enum: retail|wholesale>",
  "location_id": "<uuid>",
  "customer": {
    "name": "<string>",
    "id_number": "<string>",
    "email": "<string>",
    "phone": "<string>",
    "address": "<string>"
  },
  "items": [
    {
      "product_id": "<uuid o null — excluyente con combo_id>",
      "combo_id": "<uuid o null — excluyente con product_id>",
      "quantity": "<int>",
      "discount_pct": "<decimal o null — solo product_id>"
    }
  ],
  "note": "<string>",
  "privacy_notice_acknowledged": "<bool>"
}
```

**Request `POST invoices/<int:pk>/void/`:** `{ "reason": "<string, min 5 chars>" }`

**Request `PUT config/company/`:**
```json
{
  "company_name": "<string>",
  "nit": "<string>",
  "address": "<string>",
  "phone": "<string>",
  "email": "<string>",
  "dian_resolution": "<string>",
  "dian_range_from": "<int>",
  "dian_range_to": "<int>",
  "invoice_series": "<string>",
  "invoice_footer": "<string>"
}
```

---

## Compras

Base: `/api/v1/purchasing/`

> Solo `almacenista` escribe (`IsPurchasingOperator`); `administrador` solo lee
> (`IsPurchasingViewer`).

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET, POST | `suppliers/` | — | Listar (`?search=`, `?is_active=`) / crear proveedor |
| GET, PATCH | `suppliers/<uuid:pk>/` | — | Detalle / actualizar |
| POST | `suppliers/<uuid:pk>/disable/` `/enable/` `/restore/` | almacenista | Soft-delete |
| POST | `suppliers/<uuid:pk>/deactivate/` `/activate/` | almacenista | *(alias legacy de disable/enable)* |
| GET, POST | `purchase-orders/` | — | Listar (`?status=`, `?supplier_id=`) / crear OC |
| GET, PATCH | `purchase-orders/<uuid:pk>/` | — | Detalle / actualizar |
| POST | `purchase-orders/<uuid:pk>/confirm/` | almacenista | Confirmar OC |
| POST | `purchase-orders/<uuid:pk>/cancel/` | almacenista | Cancelar OC |
| GET, POST | `receptions/` | — | Listar (`?status=`, `?purchase_order_id=`) / crear recepción |
| GET | `receptions/<uuid:pk>/` | — | Detalle |
| POST | `receptions/<uuid:pk>/confirm/` | almacenista | Confirmar (crea Movement, actualiza stock) |
| POST | `receptions/<uuid:pk>/cancel/` | almacenista | Cancelar (solo si no confirmada) |

**Request `POST suppliers/`, `POST purchase-orders/`, `POST receptions/`,
`POST receptions/<uuid:pk>/confirm/`:** ver ejemplos reales completos en
[REFERENCIA_ENDPOINTS.md → Compras](REFERENCIA_ENDPOINTS.md#compras).

---

## Dashboard

Base: `/api/v1/dashboard/` — Solo `almacenista`.

| Método | Ruta | Params | Descripción |
|---|---|---|---|
| GET | `overview/` | `period_days` | Resumen general |
| GET | `metrics/` | `period_days` | Métricas del día |
| GET | `alerts/` | `expiring_days` | Alertas críticas activas |
| GET | `kpis/` | `period_days` | KPIs numéricos |
| GET | `movements/` | `period_days`, `limit` | Movimientos recientes |

*(Sin body — todos son GET con query params opcionales.)*

---

## Reportes

Base: `/api/v1/reports/` — `almacenista` y `administrador`.

| Método | Ruta | Params principales | Descripción |
|---|---|---|---|
| GET | `inventory/summary/` | — | Resumen de inventario por categoría |
| GET | `expiring/` | `days` (1-365) | Lotes próximos a vencer |
| GET | `movements/summary/` | `start`, `end` | Resumen de movimientos por tipo |
| GET | `movements/report/` | `start`, `end`, `type` | Agregados por producto y usuario |
| GET | `movements/history/` | `product_id`, `location_id`, `user_id`, `start`, `end`, `export` | Historial filtrable (`csv`/`xlsx`) |
| GET | `warehouse-utilization/` | — | Ocupación por ubicación/tipo/estado |
| GET | `quality-operational/` | `period_days` | Indicadores de daño/vencimiento/devolución |
| GET | `discard-operational/` | `period_days` | Indicadores de descarte (daño + vencimiento) |
| GET | `dispatch-operational/` | `period_days` | Resumen operativo de despacho (KPI 4 proxy) |
| GET | `dispatch-operational/orders/` | `start`, `end` | Muestras de despachos por número de factura |
| GET | `data/` | `kind` (**requerido**), `start`, `end`, `product_id`, `user_id`, `invoice_number`, `type`, `days`, `limit`, `period_days` | Dataset canónico unificado — `kind` selecciona cuál de los reportes anteriores devolver |
| GET | `sales/summary/` | `start`, `end` | Resumen de ventas vinculadas a despachos |
| GET | `top-products/` | `limit`, `period_days` | Productos más despachados |
| GET | `invoices/` | `start`, `end`, `invoice_number`, `product_id` | Historial de movimientos con factura |
| GET | `kpi/` | `period_days` | Panel KPI legado (delega a dashboard) |
| GET | `revenue-summary/` | `start`, `end` | Revenue por tipo de venta |
| GET | `margin-by-product/` | `start`, `end`, `limit` | Margen bruto por SKU |
| GET | `sales-by-customer/` | `start`, `end`, `limit` | Ventas por cliente (venta mayor) |

*(Todos GET, sin body — filtros vía query params. `?export=csv|xlsx` disponible en
`inventory/?export=`, `movements/history/`, `expiring/`.)*

**Response `warehouse-utilization/` (placeholder):**
```json
{
  "overall": {
    "occupied_units": "<int>",
    "capacity_units": "<int>",
    "utilization_pct": "<decimal o null>",
    "configured_locations": "<int>",
    "locations_without_capacity": "<int>",
    "unconfigured_occupied_units": "<int>"
  },
  "by_location": [
    {
      "location_id": "<uuid>",
      "code": "<string>",
      "occupied_units": "<int>",
      "capacity_units": "<int o null>",
      "utilization_pct": "<decimal o null>",
      "operational_status": "<string>"
    }
  ],
  "by_storage_type": [ { "storage_type_code": "<string>", "locations": "<int>", "occupied_units": "<int>" } ],
  "by_operational_status": [ { "operational_status": "<string>", "locations": "<int>", "occupied_units": "<int>" } ]
}
```

**Response `quality-operational/` y `discard-operational/` (placeholder, mismo esquema):**
```json
{
  "period": { "days": "<int>", "start": "<datetime>", "end": "<datetime>" },
  "totals": { "movements": "<int>", "units": "<int>" },
  "by_type": [ { "movement_type": "<string>", "movements": "<int>", "units": "<int>" } ],
  "by_product": [ { "movement_type": "<string>", "product_sku": "<string>", "movements": "<int>", "units": "<int>" } ],
  "notes": [ "<string>" ]
}
```

**Response `dispatch-operational/` (placeholder):**
```json
{
  "period": { "days": "<int>", "start": "<datetime>", "end": "<datetime>" },
  "sales": { "<string>": "<decimal>" },
  "invoice_linked_dispatches": "<int>",
  "shipments": "<int>",
  "invoice_linked_ratio": "<decimal>",
  "movement_counts": { "<string>": "<int>" },
  "top_products": [ { "product_id": "<uuid>", "product__sku": "<string>", "units": "<int>" } ],
  "per_order_samples": [
    { "invoice_number": "<string>", "movements": "<int>", "total_quantity": "<int>", "dispatched_at": "<datetime o null>" }
  ],
  "notes": [ "<string>" ]
}
```

**Response `data/?kind=...` (placeholder):** el cuerpo varía según `kind`; corresponde
al `response` del reporte equivalente listado arriba (ej. `kind=warehouse-utilization`
devuelve el mismo esquema que `GET warehouse-utilization/`).

---

## Alertas

Base: `/api/v1/alerts/`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `` (raíz) | almacenista, administrador | Alertas activas (`?export=csv\|xlsx`) |
| GET | `poll/` | todos | Polling incremental (`?since=`, `?severity=`) |
| GET | `history/` | almacenista, administrador | Alertas resueltas |
| GET | `stats/` | almacenista, administrador | Conteos por severidad/categoría |
| GET | `<int:pk>/` | almacenista, administrador | Detalle de alerta |
| POST | `<int:pk>/resolve/` | almacenista | Marcar como resuelta *(sin body)* |

Ver ejemplos reales completos (tipos de alerta, patrón de polling) en
[REFERENCIA_ENDPOINTS.md → Alertas y polling](REFERENCIA_ENDPOINTS.md#alertas-y-polling).

---

## Auditoría

Base: `/api/v1/audit/` — Solo lectura, `almacenista` y `administrador`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `` (raíz) | Listar logs (`?event_type=`, `?user_id=`, `?start=`, `?end=`) |
| GET | `<uuid:pk>/` | Detalle de log |

---

## Webhooks

Base: `/api/v1/webhooks/` — Solo `almacenista`.

| Método | Ruta | Descripción |
|---|---|---|
| GET, POST | `endpoints/` | Listar / crear endpoint |
| GET, PATCH | `endpoints/<uuid:pk>/` | Detalle / actualizar |
| DELETE | `endpoints/<uuid:pk>/` | Desactivar (`is_active=False`) |
| POST | `endpoints/<uuid:pk>/disable/` `/enable/` `/restore/` | Soft-delete |
| POST | `endpoints/<uuid:pk>/test/` | Probar conectividad |
| GET | `deliveries/` | Historial de entregas |
| GET | `stats/` | Estadísticas (pendientes/entregados/fallidos) |

**Request `POST endpoints/`:**
```json
{
  "url": "<string: URL https>",
  "secret": "<string: min 8 chars, write_only>",
  "events": [ "<enum: LOW_STOCK|STOCK_INTEGRITY_DIVERGENCE>" ],
  "is_active": "<bool>",
  "max_retries": "<int>"
}
```

**Request `POST endpoints/<uuid:pk>/test/`:**
```json
{ "event_type": "<string>", "payload": { "<string>": "<string>" } }
```

---

## Notas de mantenimiento

- Generado a partir de `config/urls.py` y cada `apps/*/urls.py` el 2026-06-16.
- Si agregas o renombras un endpoint, actualiza esta tabla y, si aplica, también
  [REFERENCIA_ENDPOINTS.md](REFERENCIA_ENDPOINTS.md) con un ejemplo real.
- ~~Se detectó que la sección "Subcategorías" de `REFERENCIA_ENDPOINTS.md` documentaba
  un endpoint que ya no existe~~ — corregido: el modelo `Subcategory` se migró a
  `Brand` (migración `0012_convert_subcategory_to_brand`); `REFERENCIA_ENDPOINTS.md`
  y `README_API.md` ahora documentan `/catalog/brands/` en su lugar.
