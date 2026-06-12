# Módulo de Dashboard

## 1. Resumen

El módulo `dashboard` proporciona un read model operacional para la UI ejecutiva. Agrega datos de múltiples dominios (movimientos, alertas, inventario) en endpoints compuestos con caché temporal.

Sin modelos propios — consume datos de `movements`, `inventory`, `catalog`, `alerts`.

---

## 2. Servicios

Todas las funciones usan caché con TTL configurable y revision stamp para invalidación.

| Función | TTL | Descripción |
|---------|-----|-------------|
| `build_dashboard_metrics(period_days=30)` | 120s | stock_total, dispatches_today, reorder_count, invoices_issued, invoice_range |
| `build_dashboard_alerts(period_days=30, expiring_days=30)` | 120s | active, reorder, expiring, returns |
| `build_dashboard_kpis(period_days=30)` | 120s | 6 KPIs: warehouse_utilization, damaged_rate, return_rate, dispatch_invoice_ratio, discard_rate, cold_chain_alerts |
| `build_dashboard_movements(period_days=30, limit=10)` | 60s | Movimientos recientes con tipo, producto, usuario, estado |
| `build_dashboard_overview(period_days=30, movements_limit=10)` | 60s | Composición completa: metrics + alerts + kpis + movements |
| `build_legacy_kpi_panel()` | Sin caché | KPIs legacy para panel administrativo |

### KPIs calculados

| KPI | Precisión | Descripción |
|-----|-----------|-------------|
| warehouse_utilization | real | % ocupación según capacidad configurada |
| damaged_rate | partial | Unidades dañadas / total calidad |
| return_rate | partial | Unidades devueltas / total calidad |
| dispatch_invoice_ratio | partial | Despachos con factura / total despachos |
| discard_rate | partial | Unidades descartadas / total calidad |
| cold_chain_alerts | future | Conteo de alertas COLD_CHAIN_MISSING activas |

---

## 3. Endpoints

Bajo `/api/v1/dashboard/`. Solo almacenistas.

| Método | Ruta | Response | Descripción |
|--------|------|----------|-------------|
| GET | `overview/` | DashboardOverviewSerializer | Resumen completo: metrics, alerts, kpis, movements |
| GET | `metrics/` | DashboardMetricSummarySerializer | Métricas operativas |
| GET | `alerts/` | DashboardAlertSummarySerializer | Resumen de alertas |
| GET | `kpis/` | DashboardKPISummarySerializer | KPIs con precisión y umbrales |
| GET | `movements/` | DashboardMovementSerializer(many=True) | Movimientos recientes |

---

## 4. Estrategia de caché

- **Revision stamp**: combina `max(created_at, updated_at)` de Movement, Alert, Product, Location, StockByLocation.
- **Cache key**: `dashboard:{prefix}:{params}:{revision}`.
- **TTL**: 60-120s según el endpoint.
- **Invalidación**: Al cambiar cualquiera de las tablas fuente, el revision stamp cambia y la caché se invalida.

---

## 5. Escenarios esperados

**DASH-S01:** Dashboard overview → 200 con metrics, alerts, kpis, movements, generated_at.
**DASH-S02:** Dashboard con base de datos vacía → ceros y listas vacías (sin error).
**DASH-S03:** Métricas reflejan stock actual → stock_total = suma StockByLocation.
**DASH-S04:** KPI warehouse_utilization refleja capacidad real de ubicaciones.
**DASH-S05:** Acceso de administrador → 403 (solo almacenista).
**DASH-S06:** Caché funciona → segunda llamada rápida (sin recálculo).
