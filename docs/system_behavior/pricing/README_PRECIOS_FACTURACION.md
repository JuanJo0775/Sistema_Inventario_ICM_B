# Módulo de Precios y Facturación

Este documento describe la arquitectura, modelos, endpoints y flujos del módulo de precios y facturación comercial del sistema ICM.

Para la decisión arquitectónica de fondo ver [ADR-013](../adr/ADR-013.md).

---

## 1. Resumen del problema resuelto

El sistema ICM fue inicialmente un ledger de unidades sin ningún campo financiero. Los despachos generaban comprobantes PDF que solo incluían SKU y cantidad, haciendo imposible:

- Calcular revenue o márgenes.
- Reconstruir una factura con valor sin consultar el catálogo actual (mutable).
- Integrar con sistemas contables externos.
- Rastrear historial de precios de los productos.

Este módulo cierra esas brechas manteniendo compatibilidad total con todos los movimientos históricos.

---

## 2. Modelos de datos

### 2.1 `Product` — campos de precio (nullable)

```
unit_cost            DecimalField(12,4)  Costo de adquisición (COGS)
sale_price_retail    DecimalField(12,4)  Precio venta al por menor (vitrina)
sale_price_wholesale DecimalField(12,4)  Precio venta al por mayor
tax_rate_pct         DecimalField(5,2)   Tasa IVA aplicable (ej: 19.00)
currency             CharField(3)        Moneda ISO 4217 (default: "COP")
```

Todos son **nullable**. Los 215 productos importados desde el Excel actual quedan con `null` en estos campos — sin error, sin bloqueo de operaciones.

### 2.2 `ProductPriceHistory` — historial inmutable de precios

```
product        FK → Product
changed_by     FK → User
field_changed  CharField(64)    "unit_cost" | "sale_price_retail" | etc.
old_value      DecimalField     Valor anterior (null si era null)
new_value      DecimalField     Valor nuevo
currency       CharField(3)
created_at     DateTimeField    (auto, inmutable)
```

Cada llamada a `update_product_prices()` crea una fila por cada campo que realmente cambió. Si el valor es el mismo, no se registra nada.

### 2.3 `Movement` — snapshot de precio congelado

Los siguientes campos se agregan al ledger de movimientos (todos nullable):

```
unit_price      Precio unitario de venta al momento del despacho
unit_cost       Costo unitario al momento del despacho
discount_pct    Porcentaje de descuento aplicado
discount_amount Monto de descuento calculado
subtotal        unit_price × quantity
tax_rate_pct    Tasa de IVA congelada
tax_amount      IVA calculado sobre la base imponible
total_amount    Subtotal − descuento + IVA
currency        Moneda del despacho
price_type      "retail" | "wholesale" | "cost" | "combo"
customer_snapshot  JSON con datos del cliente (ventas mayores)
```

**Invariante de inmutabilidad**: una vez creado el Movement, estos campos no cambian aunque el precio del producto se actualice. La función `_resolve_price_snapshot()` los fija en el momento exacto del despacho.

### 2.4 `ProductCombo` — pricing de combos

```
price_strategy        "derived" | "fixed"
fixed_price_retail    Precio fijo al por menor del combo (nullable)
fixed_price_wholesale Precio fijo al por mayor del combo (nullable)
```

- **derived**: el sistema suma los precios individuales de cada componente.
- **fixed**: el precio total del combo se distribuye entre los componentes proporcionalmente al costo unitario de cada uno.

### 2.5 `Invoice` — encabezado de factura consolidado

```
number           CharField    Número ICM-XXXX (unique)
movements        M2M → Movement
customer_name    CharField
customer_email   EmailField
customer_phone   CharField
customer_address TextField
subtotal         DecimalField(14,4)
discount_total   DecimalField(12,4)
tax_total        DecimalField(12,4)
total_amount     DecimalField(14,4)
currency         CharField(3)
pdf              FileField    PDF enriquecido con precios
issued_by        FK → User
issued_at        DateTimeField
```

Se crea automáticamente al finalizar cada `register_dispatch()` o `dispatch_combo()`.

---

## 3. Flujo de precio en un despacho

```
PATCH /api/v1/movements/dispatches/  (POST)
         │
         ▼
register_dispatch()
    │
    ├── Validar stock, SKU, cliente, consentimiento...
    │
    ├── _resolve_price_snapshot(product, quantity, movement_type)
    │       ├── SALIDA_VENTA_MENOR → sale_price_retail
    │       ├── SALIDA_VENTA_MAYOR → sale_price_wholesale
    │       ├── SALIDA_DANO/VENCIMIENTO → unit_cost
    │       └── Calcula subtotal, descuento, IVA, total
    │
    ├── Movement.objects.create(..., **price_snapshot, customer_snapshot=...)
    │
    ├── create_invoice_from_movements(movements, invoice_number, customer_data)
    │       └── Invoice creado con totales consolidados + PDF enriquecido
    │
    └── queue_webhook_event("dispatch.completed", { precio, total, sku, cliente })
```

---

## 4. Endpoints

### Gestión de precios de producto

| Método | Endpoint | Descripción | Rol requerido |
|--------|----------|-------------|---------------|
| `PATCH` | `/api/v1/catalog/products/<id>/prices/` | Actualizar uno o más campos de precio | almacenista |
| `GET`   | `/api/v1/catalog/products/<id>/prices/` | Historial inmutable de cambios de precio | almacenista |

**Cuerpo de PATCH (todos opcionales):**
```json
{
  "unit_cost": "5000.0000",
  "sale_price_retail": "12000.0000",
  "sale_price_wholesale": "9000.0000",
  "tax_rate_pct": "19.00",
  "currency": "COP"
}
```

### Facturas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/movements/invoices/<number>/` | Detalle de factura con totales y lista de movement_ids |
| `GET` | `/api/v1/movements/invoices/<number>/pdf/` | Descarga del PDF enriquecido con precios |
| `GET` | `/api/v1/movements/dispatches/<id>/invoice/` | PDF básico (legacy, compatibilidad) |

### Despacho con descuento

El endpoint de despacho ahora acepta un campo opcional:
```json
{
  "product_id": "...",
  "location_id": "...",
  "quantity": 3,
  "movement_type": "SALIDA_VENTA_MENOR",
  "discount_pct": "10.00"
}
```

### Reportes financieros

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/reports/revenue-summary/` | Revenue por tipo de venta, subtotales, IVA, totales |
| `GET` | `/api/v1/reports/margin-by-product/` | Margen bruto por SKU (revenue − COGS) |
| `GET` | `/api/v1/reports/sales-by-customer/` | Ventas al por mayor agrupadas por cliente |

Todos aceptan parámetros `?start=<ISO8601>&end=<ISO8601>`. Los reportes de margen también aceptan `?limit=<N>`.

---

## 5. Cómo cargar precios a los productos

### Opción A — Endpoint individual (recomendado para pocos productos)
```bash
PATCH /api/v1/catalog/products/<uuid>/prices/
Authorization: Bearer <token_almacenista>
Content-Type: application/json

{
  "sale_price_retail": "12000.0000",
  "sale_price_wholesale": "9500.0000",
  "unit_cost": "5000.0000",
  "tax_rate_pct": "19.00"
}
```

### Opción B — Desde el Excel de importación (para carga masiva)

Agregar columnas a partir de la columna D en cada hoja del Excel con cualquiera de estos encabezados:

| Encabezado en Excel | Campo que llena |
|---------------------|-----------------|
| `Precio Venta` / `Precio Menor` / `Precio Minorista` | `sale_price_retail` |
| `Precio Mayorista` / `Precio Mayor` | `sale_price_wholesale` |
| `Costo` / `Costo Unitario` | `unit_cost` |
| `IVA` / `IVA%` / `Tasa IVA` | `tax_rate_pct` |
| `Moneda` | `currency` |

Luego ejecutar:
```bash
python manage.py import_catalog
```

El comando es idempotente: productos ya existentes se omiten. Para re-importar con precios, primero agregar los productos en la BD y luego usar el endpoint individual.

---

## 6. Reglas de negocio

**BR-16 — Precio congelado en despacho:**
El precio capturado en un Movement es definitivo e inmutable. Modificar el precio de un producto en el catálogo no altera retroactivamente ningún movimiento ni factura pasada. Esta propiedad es crítica para la integridad contable.

**BR-17 — Historial de precios auditado:**
Cada actualización de precio de producto genera una fila en `ProductPriceHistory` con el campo modificado, el valor anterior y el valor nuevo. Si el valor enviado es idéntico al actual, no se registra nada. El historial es consultable vía `GET /api/v1/catalog/products/<id>/prices/`.

---

## 7. Comportamiento cuando el producto no tiene precio

Si un producto no tiene precio configurado al momento del despacho, el snapshot queda con todos los campos financieros en `null` y el despacho se completa normalmente. El comprobante PDF se genera con los campos de precio en blanco. El reporte de margen excluye estos movimientos.

Este es el comportamiento actual para los 215 productos del catálogo inicial.

---

## 8. Evento webhook `dispatch.completed`

Cuando hay al menos un endpoint de webhook suscrito al evento `dispatch.completed`, el sistema emite:

```json
{
  "invoice_number": "ICM-0001",
  "movement_ids": ["uuid1"],
  "product_sku": "CM-01",
  "quantity": 2,
  "movement_type": "SALIDA_VENTA_MENOR",
  "unit_price": "12000.0000",
  "total_amount": "14280.0000",
  "currency": "COP",
  "customer": null
}
```

Para ventas mayores, `customer` incluye el objeto completo de `customer_snapshot`.
