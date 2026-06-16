# Plan: Arquitectura de Precios y Facturación — Sistema Inventario ICM

---

## Contexto

El sistema ICM está diseñado como un ledger operativo de inventario (movimientos físicos de unidades).
Actualmente **no existe ningún campo de precio, costo, impuesto, descuento o moneda en ningún modelo**.
El usuario requiere que el sistema sea capaz de reconstruir documentos comerciales (facturas, remisiones, reportes de márgenes) a partir de los movimientos de despacho, **sin depender de datos mutables del producto en el momento de consulta**.

Este plan cierra la brecha completa entre "ledger de unidades" y "sistema listo para facturación".

---

## 1. Diagnóstico actual

### Lo que existe (capa operativa)
| Componente | Ubicación | Estado |
|---|---|---|
| Movement — ledger inmutable | `apps/movements/models.py:24` | Completo para cantidades |
| MovementType (8 tipos de despacho) | `apps/movements/models.py:12` | Completo |
| InvoiceCounter singleton (BR-13) | `apps/movements/models.py:120` | Numeración secuencial |
| PDF generation (WeasyPrint) | `apps/movements/services.py:105` | Solo SKU + cantidad |
| customer_data JSON (validación) | `apps/movements/services.py:371` | Validado pero NO persistido en Movement |
| ProductCombo + ComboItem | `apps/catalog/models.py:169` | Solo cantidad, sin precio |
| Webhook infrastructure | `apps/webhooks/` | Implementado pero no conectado a despachos |
| Audit trail | `apps/audit/` | Solo eventos operativos, sin eventos financieros |
| Reports | `apps/reports/selectors.py:32` | Solo totales en unidades |

### Lo que NO existe (capa financiera)
- **Ningún campo de precio** en `Product`, `Movement`, `ProductCombo`, `StockByLocation`
- **Ningún modelo** `PriceList`, `PriceHistory`, `ProductPrice`, `Invoice`, `InvoiceLineItem`
- `customer_data` se valida en el serializer/servicio pero **no se persiste en la base de datos**
- PDF de comprobante contiene solo: número, fecha, SKU, cantidad, tipo
- Reporte de ventas retorna solo `Sum("quantity")` — el código comenta explícitamente: *"El catálogo no almacena precio unitario (ICM)."* (`apps/reports/selectors.py:238`)
- Sin separación retail / mayorista / costo / promocional
- Sin impuestos, descuentos, moneda
- Sin KPIs financieros (revenue, margen, COGS)

---

## 2. Riesgos detectados

### R-01 — CRÍTICO: Irreversibilidad histórica
**Problema:** Movement es inmutable por diseño (BR-10). Si se registran despachos ahora sin precio, esos movimientos nunca podrán tener precio asociado.
**Impacto:** Imposibilidad de generar facturas retroactivas para todo el historial existente.
**Mitigación en plan:** Agregar campos de precio como nullable en Migration — los movimientos históricos quedan sin precio (documentado), los nuevos lo capturan.

### R-02 — ALTO: customer_data no persiste en Movement
**Problema:** `customer_data` (nombre, email, teléfono, dirección del cliente) es validado en `register_dispatch()` para ventas mayores, pero **no se guarda en ningún campo del modelo Movement**.
**Impacto:** Si el PDF de comprobante se pierde o regenera, los datos del cliente se pierden permanentemente.
**Mitigación:** Agregar `customer_snapshot = JSONField(null=True)` a Movement.

### R-03 — ALTO: Combos sin precio ni estrategia de pricing
**Problema:** `ProductCombo` no tiene campo `price` ni `price_strategy`. Los combos despachan componentes individuales con `SALIDA_COMBO` pero sin precio de venta del combo.
**Impacto:** Imposible generar factura de combo con precio total ni calcular margen de bundle.

### R-04 — MEDIO: UniqueConstraint invoice_number impide multi-movement invoice
**Problema:** `uniq_movement_invoice_number_when_set` prohíbe que dos Movement compartan `invoice_number`.
**Impacto:** Para despachos multi-lote (múltiples Movements con mismo invoice), solo uno puede tener el número. La arquitectura de facturación necesita agrupar por invoice.
**Mitigación:** Crear modelo `Invoice` separado que agrupe Movements; el campo `invoice_number` en Movement queda como referencia.

### R-05 — MEDIO: Sin snapshot de precio histórico en Producto
**Problema:** Si se agrega precio a Product y luego se modifica, los movimientos históricos no sabrán cuál era el precio al momento del despacho.
**Mitigación:** Capturar precio en Movement en el momento del despacho (frozen price snapshot).

### R-06 — BAJO: Sin separación retail/mayorista en precio
**Problema:** El sistema distingue `SALIDA_VENTA_MAYOR` vs `SALIDA_VENTA_MENOR` a nivel de tipo de movimiento, pero aplica el mismo (inexistente) precio.
**Mitigación:** `Movement.unit_price` + `Movement.price_type` capturan el precio correcto según el tipo de despacho.

### R-07 — BAJO: Webhooks no emiten eventos de despacho
**Problema:** La infraestructura de webhooks está implementada pero `queue_webhook_event()` nunca es llamada desde `register_dispatch()`.
**Impacto:** Integraciones contables externas no pueden suscribirse a eventos de despacho.

---

## 3. Impacto técnico y funcional

| Área | Impacto técnico | Impacto funcional |
|---|---|---|
| Movement model | Agregar ~8 campos nullable | Sin breaking change; campos opcionales |
| Product model | Agregar ~5 campos nullable | Productos existentes quedan sin precio; UI debe mostrar alerta |
| ProductCombo model | Agregar 2 campos + nueva lógica | Combos con precio fijo o derivado |
| register_dispatch() | Resolver precio + calcular totales | Despachos capturan precio real |
| generate_invoice_pdf() | Template enriched | Comprobantes con información financiera completa |
| API contracts | Nuevos campos opcionales | Backward-compatible |
| Reports | Nuevos selectores financieros | KPIs de revenue y margen |
| Tests | ~50-80 tests nuevos | Cobertura financiera |

---

## 4. Fases de implementación

### Dependencias entre fases
```
Fase 1 (Product pricing)
    ↓
Fase 2 (Movement price snapshot)  ←  Depende de Fase 1
    ↓
Fase 3 (Invoice model + PDF enriquecido)  ←  Depende de Fase 2
    ↓
Fase 4 (Combo pricing)  ←  Depende de Fase 1 + Fase 2
    ↓
Fase 5 (Reportes + Webhooks)  ←  Depende de Fase 2 + Fase 3
```

---

### FASE 1 — Precios en el catálogo de productos

**Archivos afectados:**
- `apps/catalog/models.py`
- `apps/catalog/serializers.py`
- `apps/catalog/services.py`
- `apps/catalog/migrations/0XXX_add_product_pricing.py` (nueva)
- `apps/catalog/tests/test_product_pricing.py` (nuevo)

**Cambios en base de datos — Migration `catalog/0XXX`:**
```python
# Agregar a Product (todos nullable para no romper datos existentes):
unit_cost        = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
sale_price_retail    = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
sale_price_wholesale = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
tax_rate_pct     = DecimalField(max_digits=5,  decimal_places=2, null=True, blank=True)
currency         = CharField(max_length=3, default="COP")

# Nuevo modelo ProductPriceHistory (trazabilidad):
class ProductPriceHistory(BaseModel):
    product              = FK(Product, on_delete=PROTECT)
    changed_by           = FK(User, on_delete=PROTECT)
    field_changed        = CharField(max_length=64)  # "unit_cost" | "sale_price_retail" etc.
    old_value            = DecimalField(null=True)
    new_value            = DecimalField(null=True)
    currency             = CharField(max_length=3)
    effective_at         = DateTimeField(auto_now_add=True)
```

**Cambios en backend:**
- `catalog/services.py`: Función `update_product_prices(product_id, *, user, **price_fields)` que actualiza campos y registra `ProductPriceHistory`.
- Signal `post_save` en Product (o lógica en servicio) para registrar cambio de precios en historial.
- Validación: `sale_price_wholesale <= sale_price_retail` (o permitir inversión con advertencia).

**Cambios en API:**
- `ProductSerializer` expone nuevos campos (lectura).
- Nuevo endpoint `PATCH /api/v1/catalog/products/<id>/prices/` para actualización de precios (solo `administrador`).

**Nuevo evento de auditoría:**
- `PRODUCT_PRICE_UPDATED` en `AuditEventType`.

**Tests clave:**
- `test_product_price_fields_are_nullable_by_default`
- `test_update_price_creates_history_record`
- `test_price_history_tracks_old_and_new_value`
- `test_wholesale_price_can_differ_from_retail`

---

### FASE 2 — Snapshot de precio congelado en Movement

**Archivos afectados:**
- `apps/movements/models.py`
- `apps/movements/serializers.py`
- `apps/movements/services.py` (funciones `register_dispatch`, `dispatch_combo`)
- `apps/movements/migrations/0XXX_add_movement_pricing.py` (nueva)
- `apps/movements/tests/test_dispatch_pricing.py` (nuevo)

**Cambios en base de datos — Migration `movements/0XXX`:**
```python
# Agregar a Movement (todos nullable):
unit_price       = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
unit_cost        = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
discount_pct     = DecimalField(max_digits=5,  decimal_places=2, null=True, blank=True)
discount_amount  = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
subtotal         = DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
tax_rate_pct     = DecimalField(max_digits=5,  decimal_places=2, null=True, blank=True)
tax_amount       = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
total_amount     = DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
currency         = CharField(max_length=3, null=True, blank=True)
price_type       = CharField(max_length=20, null=True, blank=True)  # "retail"|"wholesale"|"cost"|"combo"
customer_snapshot = JSONField(null=True, blank=True)  # R-02: persiste customer_data
```

**Lógica de cálculo en `register_dispatch()`:**
```
1. Resolver precio según movement_type:
   - SALIDA_VENTA_MENOR → product.sale_price_retail
   - SALIDA_VENTA_MAYOR → product.sale_price_wholesale
   - SALIDA_DANO / SALIDA_VENCIMIENTO → product.unit_cost (costo contable)
2. Calcular:
   subtotal = unit_price * quantity
   discount_amount = subtotal * (discount_pct / 100)  [si aplica]
   tax_base = subtotal - discount_amount
   tax_amount = tax_base * (tax_rate_pct / 100)
   total_amount = tax_base + tax_amount
3. Congelar currency = product.currency
4. Persistir customer_snapshot = customer_data [para ventas mayores]
5. Si unit_price is None (producto sin precio configurado) → registrar con null + log warning
```

**Backward compatibility:** Todos los campos son nullable. Los movimientos históricos quedan con `null` en campos financieros. Los endpoints existentes siguen funcionando sin cambios.

**Cambios en serializers:**
- `MovementSerializer`: exponer todos los campos de precio (read-only).
- `DispatchCreateSerializer`: aceptar `discount_pct` y `price_override` (opcional, solo `administrador`).

**Tests clave:**
- `test_dispatch_retail_captures_sale_price_retail_as_unit_price`
- `test_dispatch_wholesale_captures_sale_price_wholesale`
- `test_dispatch_calculates_subtotal_tax_total_correctly`
- `test_dispatch_without_product_price_stores_null_gracefully`
- `test_customer_snapshot_persisted_on_wholesale_dispatch`
- `test_combo_dispatch_captures_price_per_component`
- `test_historical_price_immutable_after_product_price_change`

---

### FASE 3 — Modelo Invoice enriquecido y PDF completo

**Archivos afectados:**
- `apps/movements/models.py` (nuevo modelo `Invoice`)
- `apps/movements/services.py` (generate_invoice_pdf enriched)
- `apps/movements/serializers.py` (InvoiceSerializer)
- `apps/movements/views.py` (InvoiceDetailView)
- `apps/movements/migrations/0XXX_add_invoice_model.py`
- `apps/movements/tests/test_invoice.py`

**Nuevo modelo `Invoice`:**
```python
class Invoice(BaseModel):
    """Encabezado de factura — agrupa uno o varios Movements bajo un comprobante."""
    number        = CharField(max_length=20, unique=True)   # ICM-0001
    movements     = ManyToManyField(Movement, related_name="invoices")
    customer_name = CharField(max_length=255, blank=True)
    customer_email= EmailField(blank=True)
    customer_phone= CharField(max_length=50, blank=True)
    customer_address = TextField(blank=True)
    subtotal      = DecimalField(max_digits=14, decimal_places=4)
    discount_total= DecimalField(max_digits=12, decimal_places=4, default=0)
    tax_total     = DecimalField(max_digits=12, decimal_places=4, default=0)
    total_amount  = DecimalField(max_digits=14, decimal_places=4)
    currency      = CharField(max_length=3, default="COP")
    pdf           = FileField(upload_to="invoices/%Y/%m/", null=True, blank=True)
    issued_by     = FK(User, on_delete=PROTECT)
    issued_at     = DateTimeField(auto_now_add=True)
```

**Estrategia de migración del campo `invoice_number` existente:**
- El campo `Movement.invoice_number` se mantiene como referencia de compatibilidad.
- Al crear un nuevo despacho, se crea también un registro `Invoice` y se linkan los movements.
- Los movimientos históricos sin `Invoice` asociado se pueden migrar a `Invoice` sin precio (solo número y fecha).

**PDF enriquecido — `_try_build_invoice_pdf()`:**
El template HTML incluirá:
- Encabezado ICM con logo (si existe)
- Datos del cliente (customer_snapshot)
- Tabla de líneas: SKU | Nombre | Cantidad | Precio unitario | Descuento | Subtotal
- Resumen: Subtotal | Descuento | IVA | **TOTAL**
- Pie: número de factura, fecha, operador

**Cambios en API:**
- `GET /api/v1/movements/invoices/<number>/` → detalle de Invoice con todos los campos
- `GET /api/v1/movements/dispatches/<id>/invoice/` → sigue funcionando (FileResponse PDF)

**Tests clave:**
- `test_invoice_created_on_dispatch`
- `test_invoice_totals_match_sum_of_movements`
- `test_invoice_pdf_contains_price_and_tax`
- `test_invoice_pdf_contains_customer_data`
- `test_multilot_dispatch_creates_single_invoice_with_multiple_movements`

---

### FASE 4 — Precios en combos

**Archivos afectados:**
- `apps/catalog/models.py` (ProductCombo)
- `apps/catalog/migrations/0XXX_combo_pricing.py`
- `apps/movements/services.py` (dispatch_combo)
- `apps/movements/tests/test_combo_dispatch.py`

**Cambios en `ProductCombo`:**
```python
class PriceStrategy(models.TextChoices):
    DERIVED  = "derived",  "Derivado de componentes"   # sum(item.product.sale_price * qty)
    FIXED    = "fixed",    "Precio fijo del combo"

price_strategy     = CharField(max_length=20, choices=PriceStrategy.choices, default="derived")
fixed_price_retail = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
fixed_price_wholesale = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
```

**Lógica en `dispatch_combo()`:**
```
Si combo.price_strategy == "fixed":
    combo_price = combo.fixed_price_retail o fixed_price_wholesale según tipo
    Distribuir precio proporcionalmente entre componentes (por costo relativo)
Si combo.price_strategy == "derived":
    combo_price = sum(item.product.sale_price * item.quantity)
    Cada Movement de componente recibe su precio individual
```

**Tests clave:**
- `test_combo_fixed_price_used_on_dispatch`
- `test_combo_derived_price_sums_components`
- `test_combo_invoice_reflects_total_combo_price`

---

### FASE 5 — Reportes financieros y webhooks

**Archivos afectados:**
- `apps/reports/selectors.py`
- `apps/reports/views.py`
- `apps/reports/urls.py`
- `apps/movements/services.py` (add `queue_webhook_event` calls)
- `apps/audit/models.py` (new event types)
- `apps/reports/tests/test_financial_reports.py` (nuevo)

**Nuevos selectores en `reports/selectors.py`:**
```python
def sales_revenue_summary(*, start, end) -> dict:
    """Revenue por tipo de venta: mayor vs menor. Subtotales, impuestos, totales."""

def gross_margin_by_product(*, start, end) -> QuerySet:
    """Por SKU: revenue - COGS = margen bruto y margen %."""

def sales_by_customer(*, start, end) -> QuerySet:
    """Ventas mayores agrupadas por customer_snapshot.customer_name."""

def top_products_by_revenue(*, start, end, limit=10) -> QuerySet:
    """Top N productos por total_amount acumulado."""
```

**Nuevos endpoints:**
- `GET /api/v1/reports/revenue-summary/?start=&end=`
- `GET /api/v1/reports/margin-by-product/?start=&end=`
- `GET /api/v1/reports/sales-by-customer/?start=&end=`

**Webhooks — nuevos eventos emitidos desde `register_dispatch()`:**
```python
queue_webhook_event("dispatch.completed", {
    "movement_id": str(movement.id),
    "invoice_number": movement.invoice_number,
    "product_sku": product.sku,
    "quantity": movement.quantity,
    "unit_price": str(movement.unit_price),
    "total_amount": str(movement.total_amount),
    "currency": movement.currency,
    "movement_type": movement.movement_type,
    "customer": movement.customer_snapshot,
})
```

**Nuevos AuditEventType:**
- `PRODUCT_PRICE_UPDATED`
- `INVOICE_GENERATED`
- `DISPATCH_WITH_PRICE_COMPLETED`

**Tests clave:**
- `test_revenue_summary_returns_correct_totals`
- `test_gross_margin_correct_when_cost_and_price_set`
- `test_webhook_emitted_on_dispatch_with_price`
- `test_report_excludes_non_sale_movements`

---

## 5. Estrategia de pruebas end-to-end

### Por fase:
1. **Fase 1:** `pytest apps/catalog/tests/test_product_pricing.py` — validar campos, historial, serializers
2. **Fase 2:** `pytest apps/movements/tests/test_dispatch_pricing.py` — snapshot, cálculo, backward compat
3. **Fase 3:** `pytest apps/movements/tests/test_invoice.py` — Invoice model, PDF, agrupación multi-lote
4. **Fase 4:** `pytest apps/movements/tests/test_combo_dispatch.py` — pricing fijo y derivado
5. **Fase 5:** `pytest apps/reports/tests/test_financial_reports.py` — revenue, márgenes, webhooks

### Suite completa:
```
pytest --tb=short -q
```
Target: mantener los 814 tests actuales verdes + agregar las pruebas nuevas de precio/facturación sin romper los 12 skips legítimos.

### Smoke test manual:
1. Crear producto con precio retail/wholesale
2. Despacho retail → verificar Movement.unit_price y total_amount
3. Despacho mayorista con customer_data → verificar customer_snapshot persiste
4. Descargar PDF → verificar que incluye precios
5. Combo dispatch → verificar precio distribuido en Movements
6. Hit `/api/v1/reports/revenue-summary/` → verificar totales correctos

---

## 6. Estrategia de despliegue

### Orden seguro (sin downtime):
1. **Deploy Fase 1** — migrations catalog solo agregan columnas nullable → safe
2. **Deploy Fase 2** — migrations movements solo agregan columnas nullable → safe; register_dispatch actualizado con precios opcionales (si product sin precio → null, sin error)
3. **Deploy Fase 3** — Invoice model nuevo, PDF template actualizado → safe; invoice download existente sigue funcionando
4. **Deploy Fase 4** — Combo changes → safe; combo sin precio fijo sigue usando "derived"
5. **Deploy Fase 5** — Solo nuevos endpoints y webhooks → safe; no modifica existentes

### Rollback por fase:
Cada fase es independiente; revertir la migration de esa fase es suficiente (campos nullable no afectan datos existentes).

---

## 7. Módulos afectados — resumen

| App | Fases | Tipo de cambio |
|---|---|---|
| `apps/catalog` | 1, 4 | Nuevos campos en Product y ProductCombo, nuevo modelo PriceHistory |
| `apps/movements` | 2, 3 | Nuevos campos en Movement, nuevo modelo Invoice, PDF enriquecido |
| `apps/reports` | 5 | Nuevos selectores y endpoints financieros |
| `apps/audit` | 1, 5 | Nuevos AuditEventType |
| `apps/webhooks` | 5 | Integración con register_dispatch |
| `shared/exceptions` | 2 | Posible excepción `PriceMissingWarning` (no bloqueante) |

---

## 8. Compatibilidad hacia atrás

- Todos los campos nuevos en Movement y Product son **nullable** → APIs existentes no rompen.
- `DispatchCreateSerializer` mantiene todos los campos actuales; los nuevos (discount_pct, price_override) son opcionales.
- `MovementSerializer` agrega campos nuevos en respuesta → clientes que ignorar campos extra no se afectan.
- `GET /api/v1/movements/dispatches/<id>/invoice/` sigue retornando FileResponse sin cambio de ruta.
- Los 814 tests actuales deben pasar sin modificación.

---

## 9. Notas de arquitectura

- **No se crea un app de "billing" separada** — los cambios se distribuyen en las apps existentes siguiendo el patrón del proyecto (catalog, movements, reports).
- **Precio en Movement es snapshot inmutable** — si el precio del producto cambia mañana, los Movements históricos conservan el precio del momento del despacho.
- **`customer_snapshot`** reemplaza el actual comportamiento de `customer_data` (validado pero descartado) — ahora persiste en el Movement para reconstrucción de factura futura.
- **Decimales con 4 cifras** (`decimal_places=4`) para soportar precios por gramo/unidad fraccionaria de productos como medicamentos/ortopédicos sin pérdida de precisión.
- **Moneda ISO 4217** (`"COP"` por defecto) — base para futura extensión multi-moneda.
