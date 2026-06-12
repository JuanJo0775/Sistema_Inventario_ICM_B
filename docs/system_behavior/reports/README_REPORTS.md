# Módulo de Reportes

## 1. Resumen

El módulo `reports` proporciona 18 endpoints de solo lectura para reportes operativos, financieros y KPIs. Consume datos de `movements`, `inventory`, `catalog`, `alerts` y `dashboard`.

**RF-010** — Reportes operativos y KPIs para administradores y almacenistas.

---

## 2. Modelos

Sin modelos propios. Todos los datos provienen de otras apps mediante consultas de solo lectura.

---

## 3. Reportes disponibles

### 3.1 Inventario

| Endpoint | Función selectora | Descripción |
|----------|-------------------|-------------|
| `inventory/summary/` | `get_inventory_summary()` | Stock por categoría, productos sin stock, valor aproximado |
| `expiring/` | `get_expiring_products(days)` | Lotes próximos a vencer con ubicación y cantidad disponible |

### 3.2 Movimientos

| Endpoint | Función selectora | Descripción |
|----------|-------------------|-------------|
| `movements/summary/` | `movement_counts_by_period(start, end)` | Conteo por tipo de movimiento |
| `movements/report/` | `get_movement_report(start, end, filters)` | Agregados por tipo, producto y usuario |
| `movements/history/` | `movement_history(...)` | Historial filtrable (producto, usuario, ubicación, rango); export CSV/XLSX |

### 3.3 Reportes operativos

| Endpoint | Función selectora | Descripción |
|----------|-------------------|-------------|
| `warehouse-utilization/` | `get_warehouse_utilization()` | Ocupación por ubicación, tipo de almacenamiento, estado operativo |
| `quality-operational/` | `get_quality_operational_summary(period_days)` | Daños, devoluciones, descartes; breakdown por producto |
| `discard-operational/` | `get_discard_operational_summary(period_days)` | Solo descartes (excluye devoluciones) |
| `dispatch-operational/` | `get_dispatch_operational_summary(period_days)` | Despachos, facturación, top productos, ratio de facturación |
| `dispatch-operational/orders/` | `get_dispatch_order_samples(...)` | Muestras por pedido (invoice_number como proxy) |

### 3.4 Ventas y productos

| Endpoint | Función selectora | Descripción |
|----------|-------------------|-------------|
| `sales/summary/` | `sales_dispatch_totals(start, end)` | Ventas mayor y menor |
| `top-products/` | `get_top_dispatched_products(limit, period_days)` | Productos más despachados |
| `invoices/` | `get_invoice_history(filters)` | Movimientos con factura; paginado |

### 3.5 KPIs

| Endpoint | Función selectora | Descripción |
|----------|-------------------|-------------|
| `kpi/` | `get_kpi_dashboard()` | KPIs legacy: movements_today, low_stock_count, active_alerts, dispatches_this_month |

### 3.6 Financieros (Fase 5)

| Endpoint | Función selectora | Descripción |
|----------|-------------------|-------------|
| `revenue-summary/` | `sales_revenue_summary(start, end)` | Ingresos mayor/menor con qty, subtotal, descuento, impuesto, total |
| `margin-by-product/` | `gross_margin_by_product(start, end, limit)` | Margen bruto por SKU: revenue - (unit_cost × quantity) |
| `sales-by-customer/` | `sales_by_customer(start, end, limit)` | Ventas mayor agrupadas por cliente |

---

## 4. Prefijo base

Todos los endpoints bajo `/api/v1/reports/`. 18 rutas en total.

---

## 5. Endpoint unificado

`data/` — Contrato estable para frontend. Parámetro obligatorio `kind`:

Soporta todos los reportes anteriores. Retorna `{ report, generated_at, filters, data, suggested_filename }`. Audita REPORT_GENERATED.

---

## 6. Permisos

Todos los endpoints: `IsAuthenticated` + `IsAlmacenistaOrAdministrador` (lectura compartida). `auxiliar_despacho` no tiene acceso a reportes.

---

## 7. Exportación

Los endpoints `movements/history/` y `expiring/` soportan `?export=csv` y `?export=xlsx`.

---

## 8. Escenarios esperados

**REP-S01:** Inventory summary → stock por categoría + productos sin stock.
**REP-S02:** Expiring products → lotes con días restantes, ubicación, cantidad disponible.
**REP-S03:** Movement history filtrado por producto → historial completo.
**REP-S04:** Warehouse utilization → overall + by_location + by_storage_type + by_operational_status.
**REP-S05:** Quality operational → breakdown por tipo y producto con quality_index_pct.
**REP-S06:** Dispatch operational → shipments, invoice_linked_ratio, top_products.
**REP-S07:** Revenue summary → totales mayor/menor por período.
**REP-S08:** Gross margin by product → margen por SKU ordenado por revenue.
**REP-S09:** Sales by customer → revenue + units + orders por cliente mayorista.
**REP-S10:** Export CSV/XLSX → archivo descargable con headers definidos.
**REP-S11:** Data endpoint unificado → todos los reportes accesibles por kind.
