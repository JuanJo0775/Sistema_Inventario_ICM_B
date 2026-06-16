# Módulo de Alertas

## 1. Resumen

El módulo `alerts` gestiona alertas operativas generadas por el sistema: stock bajo, vencimientos, integridad de datos, cadena de frío y ubicaciones bloqueadas.

**RF-011** — Alertas de stock bajo y vencimiento según umbrales.
**BR-11** — Alerta por producto-ubicación con `effective_reorder_point`.

---

## 2. Tipos de alerta

| Tipo | Severidad | Categoría | Disparo |
|------|-----------|-----------|---------|
| `LOW_STOCK` | HIGH | STOCK | Stock total ≤ reorder_point |
| `EXPIRATION_30` | CRITICAL | EXPIRATION | Lote vence en ≤ 30 días |
| `EXPIRATION_60` | HIGH | EXPIRATION | Lote vence en 31-60 días |
| `LOT_EXPIRED` | CRITICAL | EXPIRATION | Lote ya vencido |
| `COLD_CHAIN_MISSING` | HIGH | LOCATION | Producto cold chain en ubicación no acondicionada |
| `LOCATION_BLOCKED_WITH_STOCK` | HIGH | LOCATION | Ubicación BLOCKED/ARCHIVED con stock > 0 |
| `STOCK_MISMATCH` | CRITICAL | INTEGRITY | Desincronización stock vs ledger |
| `STOCK_ZERO` | MEDIUM | STOCK | Producto activo sin stock en ninguna ubicación |

---

## 3. Modelo

### Alert

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BigAutoField (PK) | Identificador único |
| `alert_type` | CharField(64) | Tipo de alerta |
| `severity` | CharField(16) | CRITICAL / HIGH / MEDIUM / LOW / INFO |
| `category` | CharField(16) | STOCK / EXPIRATION / LOCATION / INTEGRITY / BUSINESS |
| `product` | FK -> Product | Producto asociado |
| `lot` | FK -> Lot (nullable) | Lote (si aplica, ej: vencimiento) |
| `location` | FK -> Location (nullable) | Ubicación (null = alerta global al producto) |
| `message` | TextField | Mensaje descriptivo |
| `is_resolved` | BooleanField(default=False) | Resuelta o activa |
| `resolved_at` | DateTimeField (nullable) | Cuándo se resolvió |
| `resolved_by` | FK -> User (nullable) | Quién resolvió |
| `created_at` | DateTimeField(auto_now_add) | Fecha de creación |

---

## 4. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `sync_stock_alerts_for_product(product_id)` | RF-011 | Alerta LOW_STOCK según Product.reorder_point global |
| `check_and_create_minimum_stock_alert(product, location)` | RF-011, BR-11 | LOW_STOCK por ubicación, usa effective_reorder_point |
| `sync_expiry_alerts_for_product(product_id)` | RF-011 | Alerts EXPIRATION_30/60 según lotes o Product.expiration_date |
| `sync_lot_expired_alerts(product_id)` | — | LOT_EXPIRED para lotes con expiration_date ya pasada |
| `sync_cold_chain_alerts(product, location)` | — | COLD_CHAIN_MISSING si producto frío en ubicación no acondicionada |
| `sync_stock_zero_alerts(product_id)` | — | STOCK_ZERO si producto activo con stock total = 0 |
| `sync_location_blocked_alerts_for_location(location)` | — | LOCATION_BLOCKED_WITH_STOCK por producto en ubicación bloqueada |
| `scan_all_expiry_alerts(dry_run)` | RF-011 | Escanea todos los productos activos, sincroniza alertas de vencimiento |
| `scan_all_stock_alerts(dry_run)` | RF-011 | Escanea todos los productos activos, sincroniza alertas de stock |
| `scan_all_location_alerts(dry_run)` | — | Escanea ubicaciones bloqueadas con stock; resuelve stale alerts |
| `resolve_alert(executor, alert_id)` | RF-011 | Marca alerta como resuelta (solo almacenista) |

### Flujo de resolución

```
resolve_alert(executor, alert_id)
  → Valida executor.role == almacenista
  → select_for_update() sobre Alert
  → is_resolved=True, resolved_at=now, resolved_by=executor
  → ALERT_RESOLVED en audit log
```

### Escaneo programado

Management command `scan_alerts` con soporte `--types expiry,stock,location`, `--dry-run`, `--strict`.

---

## 5. Endpoints

Bajo `/api/v1/alerts/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/` | Almacenista/Admin | Listar alertas activas (filtros, export CSV/XLSX) |
| GET | `poll/` | Autenticado | Polling de alertas desde timestamp (NEW-04) |
| GET | `history/` | Almacenista/Admin | Alertas resueltas (historial) |
| GET | `stats/` | Almacenista/Admin | Conteos por severidad y categoría |
| GET | `<pk>/` | Almacenista/Admin | Detalle de alerta |
| POST | `<pk>/resolve/` | Almacenista | Resolver alerta |

---

## 6. Escenarios esperados

**ALERT-S01:** Producto con stock ≤ reorder_point → LOW_STOCK creada automáticamente tras movimiento.
**ALERT-S02:** Reposición supera reorder_point → LOW_STOCK resuelta automáticamente.
**ALERT-S03:** Lote próximo a vencer (días ≤ 30) → EXPIRATION_30 + EXPIRATION_60 previa se resuelve.
**ALERT-S04:** Lote ya vencido → LOT_EXPIRED CRITICAL.
**ALERT-S05:** Producto cold chain en ubicación sin refrigeración → COLD_CHAIN_MISSING.
**ALERT-S06:** Ubicación bloqueada con stock → LOCATION_BLOCKED_WITH_STOCK.
**ALERT-S07:** Producto activo sin stock → STOCK_ZERO.
**ALERT-S08:** Almacenista resuelve alerta → is_resolved=True + ALERT_RESOLVED.
**ALERT-S09:** Escaneo programado (`scan_alerts`) idempotente, sin duplicados.
**ALERT-S10:** Ubicación desbloqueada → stale alerts resueltas automáticamente.
