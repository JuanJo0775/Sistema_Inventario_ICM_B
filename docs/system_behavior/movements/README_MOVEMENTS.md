# Módulo de Movimientos (Ledger)

## 1. Resumen

El módulo `movements` implementa el ledger central del inventario. Todos los cambios de stock se registran como `Movement` inmutables. `StockByLocation` se actualiza en la misma transacción.

**RF-005** — Registrar entrada de inventario.
**RF-006** — Registrar salida/despacho.
**RF-007** — Registrar traslado entre ubicaciones.
**RF-008** — Registrar devolución.
**RF-009** — Registrar ajuste de inventario.
**BR-10** — Movimiento inmutable.
**BR-11** — Ledger como fuente de verdad, stock no negativo.

---

## 2. Modelos

### 2.1 Movement — Ledger central

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador |
| `movement_type` | CharField(32) | ENTRADA, SALIDA_VENTA_MAYOR, SALIDA_VENTA_MENOR, SALIDA_DANO, SALIDA_VENCIMIENTO, TRASLADO, AJUSTE, DEVOLUCION, SALIDA_COMBO |
| `product` | FK -> Product (PROTECT) | Producto |
| `lot` | FK -> Lot (nullable) | Lote |
| `origin_location` | FK -> Location (nullable) | Origen (null en entradas/devoluciones) |
| `destination_location` | FK -> Location (nullable) | Destino (null en salidas) |
| `quantity` | PositiveIntegerField | Cantidad |
| `stock_previo_origen` / `stock_resultante_origen` | PositiveIntegerField (nullable) | Snapshots de stock origen |
| `stock_previo_destino` / `stock_resultante_destino` | PositiveIntegerField (nullable) | Snapshots de stock destino |
| `serial_number` | CharField(100) (nullable) | BR-04: serial Electroterapia |
| `scanned_code` / `order_sku` | CharField(100) (nullable) | BR-08: validación cruzada |
| `invoice_number` | CharField(20) (nullable) | BR-13: factura |
| `invoice_pdf` | FileField (nullable) | PDF de factura |
| `executed_by` | FK -> User (PROTECT) | Quién ejecutó |
| `created_at` | DateTimeField (auto_now_add) | Fecha (inmutable) |
| `related_movement` | FK -> self (nullable) | Movimiento original en correcciones |
| `unit_price`, `unit_cost`, `subtotal`, `discount_pct`, `discount_amount` | DecimalField (nullable) | Snapshot financiero |
| `tax_rate_pct`, `tax_amount`, `total_amount` | DecimalField (nullable) | IVA y total |
| `currency` | CharField(3) (nullable) | Moneda |
| `customer_snapshot` | JSONField (nullable) | Datos del cliente |

### 2.2 InvoiceCounter

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `last_number` | PositiveIntegerField | Último número (singleton pk=1) |

`_next_invoice_number()`: genera "ICM-XXXX" con `select_for_update()`.

### 2.3 Invoice

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `number` | CharField(20, unique) | Número ICM-XXXX |
| `movements` | M2M -> Movement | Movimientos asociados |
| `customer_name/email/phone/address` | Varios | Datos del cliente |
| `subtotal/discount_total/tax_total/total_amount` | DecimalField | Totales |
| `pdf` | FileField | PDF enriquecido |
| `issued_by` | FK -> User | Emisor |

---

## 3. Tipos de movimiento

| Tipo | Código | Origen | Destino | Efecto en stock |
|------|--------|:------:|:-------:|:----------------:|
| Entrada | `ENTRADA` | ❌ | ✅ | + destino |
| Salida venta mayor | `SALIDA_VENTA_MAYOR` | ✅ | ❌ | - origen |
| Salida venta menor | `SALIDA_VENTA_MENOR` | ✅ | ❌ | - origen |
| Salida daño | `SALIDA_DANO` | ✅ | ❌ | - origen |
| Salida vencimiento | `SALIDA_VENCIMIENTO` | ✅ | ❌ | - origen |
| Traslado | `TRASLADO` | ✅ | ✅ | - origen, + destino |
| Ajuste | `AJUSTE` | ✅/❌ | ❌/✅ | Según signo |
| Devolución | `DEVOLUCION` | ❌ | ✅ | + destino |
| Salida combo | `SALIDA_COMBO` | ✅ | ❌ | - origen |

---

## 4. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `register_entry(user, product_id, location_id, quantity, ...)` | RF-005, BR-04, BR-09 | Entrada de mercancía |
| `register_dispatch(user, product_id, location_id, quantity, movement_type, ...)` | RF-006, BR-04, BR-08, BR-11, BR-13 | Salida con factura |
| `register_internal_transfer(user, product_id, origin_id, destination_id, quantity, ...)` | RF-007, BR-04, BR-11, BR-14 | Traslado |
| `register_return(user, product_id, location_id, quantity, ...)` | RF-008, BR-04, BR-05, BR-11 | Devolución |
| `register_adjustment(almacenista_user, product_id, location_id, new_quantity, justification)` | RF-009, BR-04, BR-07, BR-14 | Ajuste formal |
| `correct_movement_within_window(user, movement_id, corrected_data)` | BR-06 | Autocorrección 5 min |
| `dispatch_combo(user, combo_id, location_id, ...)` | RF-003, BR-04, BR-11 | Despachar combo |
| `create_invoice_from_movements(movements, user, invoice_number, customer_data)` | BR-13 | Invoice consolidado |

### Helpers clave

| Función | Propósito |
|---------|-----------|
| `_validate_serial_required(product, serial)` | BR-04: valida serial si categoría lo exige |
| `_lock_stock(product_id, location_id)` | `select_for_update()` sobre StockByLocation |
| `_next_invoice_number()` | BR-13: número secuencial atómico |
| `_resolve_price_snapshot(product, quantity, movement_type, discount_pct)` | Calcula snapshot financiero |
| `_product_allows_returns(product)` | BR-05: verifica is_returnable |

---

## 5. Validaciones críticas

### BR-04 — Serial obligatorio
Si `category.requires_serial_number` y no se envía serial → `SerialNumberRequiredError`.

### BR-06 — Autocorrección
Solo el mismo usuario, dentro de 5 minutos, para tipos: TRASLADO, ENTRADA, SALIDA_VENTA_MAYOR, SALIDA_VENTA_MENOR.
Nunca muta el original: crea reversal + movimiento corregido.

### BR-07 — Justificación en ajustes
`register_adjustment()` requiere `justification` no vacía.

### BR-08 — Validación cruzada
En `register_dispatch()`: si se envían `scanned_code` y `order_sku`:
1. `resolve_identifier(scanned_code)` resuelve producto
2. Verifica `scanned_product.id == product_id`
3. Verifica `product.sku == order_sku`
Si solo uno de los dos campos se envía → `CrossValidationFailedError`.

### BR-09 — Discrepancia en entrada
Si `qty_invoiced != quantity` y no hay `discrepancy_note` → `DiscrepancyNoteRequiredError`.

### BR-11 — Stock no negativo
- CheckConstraint BD: `current_stock >= 0`
- Validación aplicación: `InsufficientStockError` si no hay suficiente stock

---

## 6. Endpoints

Todas bajo `/api/v1/movements/`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `` | Listar movimientos |
| GET | `<pk>/` | Detalle (solo lectura, PUT/PATCH/DELETE → 405) |
| GET/POST | `entries/` | Listar/crear entradas |
| GET | `entries/<pk>/` | Detalle entrada |
| GET/POST | `dispatches/` | Listar/crear despachos |
| GET | `dispatches/<pk>/` | Detalle despacho |
| GET | `dispatches/<pk>/invoice/` | Descargar PDF factura |
| GET/POST | `transfers/` | Listar/crear traslados |
| GET/POST | `returns/` | Listar/crear devoluciones |
| GET/POST | `adjustments/` | Listar/crear ajustes |
| POST | `adjustments/correct/` | Corregir ajuste |
| POST | `<pk>/corrections/` | Corregir movimiento |
| POST | `combo-dispatch/` | Despachar combo |
| GET | `invoices/<number>/` | Detalle factura |
| GET | `invoices/<number>/pdf/` | Descargar PDF factura |

---

## 7. Flujo de entrada

```
POST /movements/entries/ { product_id, location_id, quantity, ... }
  → register_entry()
    → Lock: Product.select_for_update(), Location.select_for_update()
    → BR-14: validar destino permitido
    → BR-04: validar serial
    → BR-09: validar discrepancy_note si qty_invoiced != quantity
    → Crear/recuperar Lot si requires_expiration
    → _lock_stock(): StockByLocation.current_stock += quantity
    → Crear Movement (ENTRADA) con snapshots
    → log_event(MOVEMENT_CREATED)
    → check_and_create_alerts(product, location)
```

## 8. Flujo de despacho

```
POST /movements/dispatches/ { product_id, location_id, quantity, movement_type, ... }
  → register_dispatch()
    → BR-14: validar origen permitido
    → BR-08: validación cruzada scanned_code vs order_sku
    → BR-04: validar serial
    → _resolve_price_snapshot(): congelar precio
    → Manejo de lotes: FIFO por vencimiento, multi-lote si es necesario
    → _lock_stock(): verificar stock suficiente
    → generate_invoice_number(): "ICM-XXXX" atómico
    → Crear Movement(s) con invoice_number, price_snapshot
    → StockByLocation.current_stock -= quantity
    → create_invoice_from_movements(): consolidar factura
    → queue_webhook_event("dispatch.completed")
    → log_event(DISPATCH_WITH_PRICE_COMPLETED)
    → check_and_create_alerts(product, location)
```

---

## 9. Escenarios esperados

**MOV-S01**: Entrada exitosa → stock incrementado, MOVEMENT_CREATED.
**MOV-S02**: Entrada con discrepancia sin nota → 422 DiscrepancyNoteRequiredError.
**MOV-S03**: Despacho con stock insuficiente → InsufficientStockError.
**MOV-S04**: Despacho con validación cruzada exitosa → scanned_code coincide con order_sku.
**MOV-S05**: Despacho con validación cruzada fallida → CrossValidationFailedError.
**MOV-S06**: Traslado con stock insuficiente → InsufficientStockError.
**MOV-S07**: Traslado que conserva stock total → stock total pre == stock total post.
**MOV-S08**: Devolución de producto no retornable → ProductNotReturnableError.
**MOV-S09**: Ajuste de 0 → error (no cambia stock).
**MOV-S10**: Ajuste sin justificación → AdjustmentJustificationRequiredError.
**MOV-S11**: Corregir movimiento después de 5 min → CorrectionWindowClosedError.
**MOV-S12**: PUT/PATCH sobre movimiento → 405 ImmutableRecordError.
**MOV-S13**: Despacho combo → todos los items descargados, un invoice.
