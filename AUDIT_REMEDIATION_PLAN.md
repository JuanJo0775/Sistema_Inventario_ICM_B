# Plan de Remediación — Auditoría ICM

> Versión 2.0 — post-validación de 5 puntos críticos.
> Cada tarea verifica contra código real (commit `d71e377`).
> Filosofía: mínimo cambio, máximo impacto, cero nuevas capas.

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Cobertura actual | **47%** (46/97) |
| Cobertura bruta post-plan | **74%** (72/97) |
| Cobertura ajustada post-plan | **100%** (72/72 — solo operaciones que deben auditarse) |
| Nuevos event types | **7** (validados 1 a 1) |
| Nuevos event types | **7** (validados 1 a 1) |
| Nuevas columnas en BD | 0 |
| Nuevas capas/abstracciones | 0 |
| Archivos modificados | 12 |
| Días-hombre estimados | **6 días** (MVP) / **8 días** (recomendado) |
| Riesgo de regresión | 1 tarea Medio, el resto Bajo |

---

## 1. Validación cruzada contra código real

Todas las verificaciones hechas sobre la rama actual (commit `d71e377`). Ninguna línea se movió respecto a la auditoría inicial.

| Tarea | Archivo | Función | Línea | Validada |
|-------|---------|---------|-------|----------|
| 0.1 | `apps/movements/services.py` | `register_dispatch` | 488-796 | ✅ **NUEVA**: no emite MOVEMENT_CREATED |
| 1.1 | `apps/movements/services.py` | `create_invoice_from_movements` | 198-244 | ✅ additive tras return invoice |
| 1.2 | `apps/movements/services.py` | `register_dispatch` | 795 | ✅ additive entre webhook y return |
| 1.3 | `apps/reports/views.py` | `ReportDatasetView.get` | 620-812 | ✅ additive antes de return |
| 1.3b | `apps/reports/views.py` | `MovementHistoryReportView.get` | 268-274 | ✅ en bloques if export |
| 1.3c | `apps/reports/views.py` | `ExpiringProductsReportView.get` | 555-563 | ✅ en bloques if export |
| 1.3d | `apps/inventory/views.py` | `InventoryFullListView.get` | 145-172 | ✅ export blocks |
| 1.3e | `apps/alerts/views.py` | `AlertListView` | 125 | ✅ export blocks |
| 1.4 | `apps/audit/management/commands/archive_old_audit_logs.py` | `handle` | 40 | ✅ additive inicio/fin |
| 1.5 | `apps/inventory/management/commands/verify_stock_integrity.py` | `handle` | 73-76 | ✅ solo en `if options["fix"]` |
| 1.6 | `apps/inventory/services.py` | `ensure_stock_row_for_tests` | 80-94 | ✅ renombrar + guard |
| 2.1 | `apps/inventory/services.py` | `create_location` | 111-248 | ✅ additive antes de return |
| 2.2 | `apps/inventory/services.py` | `update_location` | 253-372 | ✅ PUNTO ÚNICO de LOCATION_MODIFIED |
| 2.3 | `apps/webhooks/views.py` | post/put/patch/delete | 58,104,123,144 | ✅ 4 puntos additive |
| 2.4 | `apps/inventory/views.py` | `StockThresholdView.patch` | 702-710 | ✅ additive tras row.save |
| 2.5 | `apps/purchasing/services.py` | `update_purchase_order` | 264-291 | ✅ additive antes de return |
| 2.6 | `apps/alerts/services.py` | `resolve_alert` | 472-488 | ✅ additive antes de return |
| 3.1 | `apps/webhooks/management/commands/deliver_webhooks.py` | `handle` | 19 | ✅ additive inicio/fin |
| 3.1b | `apps/alerts/management/commands/scan_alerts.py` | `handle` | 56 | ✅ additive inicio/fin |
| 3.2 | `apps/audit/models.py` | `AuditLogArchive.save` | 129-155 | ✅ mismo patrón que AuditLog |

---

## 2. Revisión de EventTypes — validación final uno a uno

### Punto 1: LOCATION_MODIFIED y metadata["_action"]

**Decisión**: SÍ, exigir `_action` obligatorio.

`LOCATION_MODIFIED` cubre 3 operaciones distintas semánticamente (update, deactivate, state_change). Sin `_action`, un consultor forense no podría distinguir "se cambió el nombre" de "se desactivó la ubicación" sin parsear `changed_fields` (que implementaremos después).

```python
detail = {
    "location_id": str(loc.id),
    "_entity_type": "Location",
    "_entity_id": str(loc.id),
    "_action": "updated" | "deactivated" | "state_changed",
    # Opcional en el futuro:
    # "changed_fields": { ... }
}
```

**Punto de emisión**: ÚNICAMENTE dentro de `update_location()` (línea 372). `deactivate_location()` y `transition_location_state()` llaman a `update_location()` internamente → el evento se dispara una sola vez con `_action` correcto según los datos pasados.

### Análisis completo de los 7 EventTypes definitivos

```python
LOCATION_CREATED = "LOCATION_CREATED", "Ubicación creada"
    # Obligatorio. Entidad de negocio. metadata obligatorio: _action.
    # Creado por create_location().

LOCATION_MODIFIED = "LOCATION_MODIFIED", "Ubicación modificada"
    # Obligatorio. metadata obligatorio: _action ∈ {updated, deactivated, state_changed}.
    # PUNTO ÚNICO DE EMISIÓN: update_location(). NO hay eventos separados
    # en deactivate_location() ni transition_location_state() porque ambas
    # delegan a update_location().

WEBHOOK_ENDPOINT_CHANGED = "WEBHOOK_ENDPOINT_CHANGED", "Endpoint webhook modificado"
    # Obligatorio. Seguridad: potencial vector de exfiltración.
    # metadata obligatorio: _action ∈ {created, updated, deactivated}.
    # Cubre los 4 métodos HTTP (post/put/patch/delete).

STOCK_THRESHOLD_UPDATED = "STOCK_THRESHOLD_UPDATED", "Umbral de stock actualizado"
    # Obligatorio. Afecta comportamiento de reorden. Operación única, no necesita _action.

ALERT_RESOLVED = "ALERT_RESOLVED", "Alerta resuelta"
    # Obligatorio. Accountability de resolución de alertas.
    # ALERT_ACKNOWLEDGED (existente) ≠ ALERT_RESOLVED: "visto" ≠ "arreglado".

PURCHASE_ORDER_UPDATED = "PURCHASE_ORDER_UPDATED", "Orden de compra actualizada"
    # Obligatorio. Ver punto 4 abajo — no hay solapamiento con CONFIRMED/CANCELLED.

BATCH_JOB_EXECUTED = "BATCH_JOB_EXECUTED", "Job batch ejecutado"
    # Obligatorio. metadata obligatorio: job_name.
    # metadata adicional: status ∈ {STARTED, COMPLETED, FAILED, DRY_RUN}.
```

**Total: 7** — cada uno resuelve una brecha concreta, ninguno es redundante.

---

## 3. Revisión de duplicidad — análisis de call chains

### Location: cadena completa verificada

```
create_location()
  └→ log_event(LOCATION_CREATED)  ✅ 1 evento único

update_location(data={"name": ..., "description": ...})
  └→ log_event(LOCATION_MODIFIED, _action="updated")  ✅ 1 evento

deactivate_location()
  └→ update_location({"is_active": False, "operational_status": "ARCHIVED"})
      └→ log_event(LOCATION_MODIFIED, _action="deactivated")  ✅ 1 evento (NO duplicado)

transition_location_state(new_status="MAINTENANCE")
  └→ update_location({"operational_status": "MAINTENANCE"})
      └→ log_event(LOCATION_MODIFIED, _action="state_changed")  ✅ 1 evento (NO duplicado)
```

**Clave**: `update_location()` es el PUNTO ÚNICO de emisión de `LOCATION_MODIFIED`. Los llamadores (`deactivate_location`, `transition_location_state`) no agregan eventos propios.

### WebhookEndpoint

```
post() → log_event(WEBHOOK_ENDPOINT_CHANGED, _action="created")        ✅ 1 evento
put()  → log_event(WEBHOOK_ENDPOINT_CHANGED, _action="updated")        ✅ 1 evento
patch()→ log_event(WEBHOOK_ENDPOINT_CHANGED, _action="updated")        ✅ 1 evento
delete()→ log_event(WEBHOOK_ENDPOINT_CHANGED, _action="deactivated")   ✅ 1 evento
```

4 métodos HTTP, 4 eventos independientes, 1 event type. Sin duplicidad.

---

## 4. PURCHASE_ORDER_UPDATED — verificación de solapamiento

Revisión del código en `apps/purchasing/services.py`:

| Función | Estado permitido | Lo que hace | Evento existente |
|---------|-----------------|-------------|------------------|
| `create_purchase_order()` | — | Crea OC en BORRADOR | `PURCHASE_ORDER_CREATED` ✅ |
| `update_purchase_order()` | BORRADOR | Cambia `expected_delivery`, `notes`, reemplaza `items`. **NO cambia status** | **NINGUNO** — GAP |
| `confirm_purchase_order()` | BORRADOR | BORRADOR → PENDIENTE | `PURCHASE_ORDER_CONFIRMED` ✅ |
| `cancel_purchase_order()` | BORRADOR, PENDIENTE | → CANCELLED | `PURCHASE_ORDER_CANCELLED` ✅ |

**Conclusión**: No hay solapamiento. `update_purchase_order()` muta datos de una OC sin cambiar su estado lifecycle. Es una operación semánticamente diferente de confirmar o cancelar. Requiere su propio event type.

---

## 5. Cobertura final — matriz explícita de operaciones mutantes

### Leyenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Auditado (evento en producción) |
| 🔧 | Se agrega en este plan |
| ⬜ | Excluido deliberadamente (justificación abajo) |
| ❌ | No auditado y no se va a auditar (riesgo aceptado) |

### Catalog (17/17 ✅ — 100%)

| Operación | Evento | Estado |
|-----------|--------|--------|
| create_product | PRODUCT_CREATED | ✅ |
| update_product | PRODUCT_UPDATED | ✅ |
| deactivate_product | PRODUCT_DEACTIVATED | ✅ |
| activate_product | PRODUCT_ACTIVATED | ✅ |
| update_product_prices | PRODUCT_PRICE_UPDATED | ✅ |
| create_combo | COMBO_CREATED | ✅ |
| update_combo | COMBO_UPDATED | ✅ |
| deactivate_combo | COMBO_DEACTIVATED | ✅ |
| activate_combo | COMBO_ACTIVATED | ✅ |
| create_category | CATEGORY_CREATED | ✅ |
| update_category | CATEGORY_UPDATED | ✅ |
| deactivate_category | CATEGORY_DEACTIVATED | ✅ |
| activate_category | CATEGORY_ACTIVATED | ✅ |
| create_brand | BRAND_CREATED | ✅ |
| update_brand | BRAND_UPDATED | ✅ |
| deactivate_brand | BRAND_DEACTIVATED | ✅ |
| activate_brand | BRAND_ACTIVATED | ✅ |
| create_subcategory | SUBCATEGORY_CREATED | ✅ (legacy) |
| update_subcategory | SUBCATEGORY_UPDATED | ✅ (legacy) |
| deactivate_subcategory | SUBCATEGORY_DEACTIVATED | ✅ (legacy) |
| activate_subcategory | SUBCATEGORY_ACTIVATED | ✅ (legacy) |

### Authentication (9/9 ✅ — 100%)

| Operación | Evento | Estado |
|-----------|--------|--------|
| authenticate_user (success) | LOGIN_SUCCESS | ✅ |
| authenticate_user (failure) | LOGIN_FAILED | ✅ |
| logout | LOGOUT | ✅ |
| create_user | USER_CREATED | ✅ |
| update_user | USER_UPDATED | ✅ |
| disable_user | USER_DISABLED | ✅ |
| enable_user | USER_ENABLED | ✅ |
| update_user_password | USER_UPDATED | ✅ |
| create/update schedule | PERMISSION_CHANGED | ✅ |
| grant temporary permit | PERMISSION_CHANGED | ✅ |
| revoke temporary permit | PERMISSION_CHANGED | ✅ |

### Movements (8/9 🔧 — 89% → 100% post-plan)

| Operación | Evento | Estado | Nota |
|-----------|--------|--------|------|
| register_entry | MOVEMENT_CREATED | ✅ | |
| **register_dispatch** | **MOVEMENT_CREATED** | **🔧** | **GAP CRÍTICO: no se emite** |
| register_internal_transfer | MOVEMENT_CREATED | ✅ | |
| register_return | RETURN_CREATED | ✅ | |
| register_adjustment | ADJUSTMENT_CREATED | ✅ | |
| correct_movement_within_window | MOVEMENT_CORRECTED | ✅ | |
| dispatch_combo | MOVEMENT_CREATED | ✅ | |
| **create_invoice_from_movements** | **INVOICE_GENERATED** | **🔧** | **GAP: definido pero no emitido** |
| **register_dispatch (con precio)** | **DISPATCH_WITH_PRICE_COMPLETED** | **🔧** | **GAP: definido pero no emitido** |
| _reverse_* (internos) | — | ⬜ | Cubierto por MOVEMENT_CORRECTED |
| _lock_stock (interno) | — | ⬜ | Helper sin semántica de negocio |
| _next_invoice_number (interno) | — | ⬜ | Contador atómico interno |

### Purchasing (10/11 ✅ + 🔧 → 100% post-plan)

| Operación | Evento | Estado |
|-----------|--------|--------|
| create_supplier | SUPPLIER_CREATED | ✅ |
| update_supplier | SUPPLIER_UPDATED | ✅ |
| deactivate_supplier | SUPPLIER_DEACTIVATED | ✅ |
| activate_supplier | SUPPLIER_ACTIVATED | ✅ |
| create_purchase_order | PURCHASE_ORDER_CREATED | ✅ |
| **update_purchase_order** | **PURCHASE_ORDER_UPDATED** | **🔧** |
| confirm_purchase_order | PURCHASE_ORDER_CONFIRMED | ✅ |
| cancel_purchase_order | PURCHASE_ORDER_CANCELLED | ✅ |
| create_reception | RECEPTION_CREATED | ✅ |
| confirm_reception | RECEPTION_CONFIRMED | ✅ |
| cancel_reception | RECEPTION_CANCELLED | ✅ |
| _next_po_number (interno) | — | ⬜ |
| _update_po_status (interno) | — | ⬜ |

### Inventory Locations (0/4 ❌ → 4/4 🔧 100% post-plan)

| Operación | Evento | Estado |
|-----------|--------|--------|
| **create_location** | **LOCATION_CREATED** | **🔧** |
| **update_location** | **LOCATION_MODIFIED** | **🔧** |
| **deactivate_location** | (cubierto por update_location) | **🔧** |
| **transition_location_state** | (cubierto por update_location) | **🔧** |

### Inventory Others (3/4 ✅ → 100% post-plan)

| Operación | Evento | Estado |
|-----------|--------|--------|
| trigger_stock_reconstruction | STOCK_RECONSTRUCTED | ✅ |
| **StockThreshold patch** | **STOCK_THRESHOLD_UPDATED** | **🔧** |
| **verify_stock_integrity --fix** | **STOCK_RECONSTRUCTED** | **🔧** |
| ensure_stock_row_for_tests | — | ⬜ Protegida con guard DEBUG |
| StorageType CRUD (3 ops) | — | ❌ Config, cambios infrecuentes. Location valida storage activo. |
| StorageTemplate CRUD (3 ops) | — | ❌ Config. Misma justificación. |

### Webhooks (0/4 ✅ → 4/4 🔧 100% post-plan)

| Operación | Evento | Estado |
|-----------|--------|--------|
| **Endpoint create** | **WEBHOOK_ENDPOINT_CHANGED** | **🔧** |
| **Endpoint update (put)** | **WEBHOOK_ENDPOINT_CHANGED** | **🔧** |
| **Endpoint update (patch)** | **WEBHOOK_ENDPOINT_CHANGED** | **🔧** |
| **Endpoint delete (soft)** | **WEBHOOK_ENDPOINT_CHANGED** | **🔧** |
| queue_webhook_event | — | ⬜ Delivery es detalle de implementación |
| deliver_pending_webhooks | — | ⬜ Se audita via BATCH_JOB_EXECUTED del comando |
| _attempt_delivery | — | ⬜ Idem |

### Alerts (0/1 ✅ → 1/1 🔧 100% post-plan para operaciones manuales)

| Operación | Evento | Estado | Nota |
|-----------|--------|--------|------|
| **resolve_alert** | **ALERT_RESOLVED** | **🔧** | Accountability: quién resolvió |
| alert auto-creation (12 funciones) | — | ❌ | Automático, no manual. No genera accountability adicional. |
| scan_alerts batch | BATCH_JOB_EXECUTED | 🔧 | Se audita via comando |

### Reports (0/5 ✅ → 5/5 🔧 100% post-plan para exports y datasets)

| Operación | Evento | Estado | Nota |
|-----------|--------|--------|------|
| **ReportDatasetView get** | **REPORT_GENERATED** | **🔧** | Solo datasets, no dashboards |
| **MovementHistory export** | **REPORT_GENERATED** | **🔧** | Solo cuando export=csv/xlsx |
| **ExpiringProducts export** | **REPORT_GENERATED** | **🔧** | Idem |
| **InventoryFullList export** | **REPORT_GENERATED** | **🔧** | Idem |
| **AlertList export** | **REPORT_GENERATED** | **🔧** | Idem |
| Consultas visuales/dashboards | — | ⬜ Excluidas para evitar ruido |
| Dashboard KPI views | — | ⬜ Sólo lectura, frecuencia alta |

### Batch Jobs (0/4 ✅ → 4/4 🔧 100% post-plan)

| Operación | Evento | Estado |
|-----------|--------|--------|
| **archive_old_audit_logs** | **BATCH_JOB_EXECUTED** | **🔧** |
| **verify_stock_integrity** | **STOCK_RECONSTRUCTED** | **🔧** |
| **deliver_webhooks** | **BATCH_JOB_EXECUTED** | **🔧** |
| **scan_alerts** | **BATCH_JOB_EXECUTED** | **🔧** |
| create_almacenista | — | ⬜ Ya tiene USER_CREATED. Se ejecuta 1 vez. |

### Resumen de cobertura

| Categoría | Total ops | Auditadas hoy | Post-plan | Excluidas |
|-----------|-----------|---------------|-----------|-----------|
| Catalog | 17 | 17 (100%) | 17 (100%) | 0 |
| Authentication | 11 | 11 (100%) | 11 (100%) | 0 |
| Movements | 12 | 7 (58%) | 11 (92%) | 1 (_lock_stock interno) |
| Purchasing | 13 | 10 (77%) | 11 (85%) | 2 (contadores internos) |
| Inventory Locations | 4 | 0 (0%) | 4 (100%) | 0 |
| Inventory Others | 10 | 1 (10%) | 3 (30%) | 7 (3 StorageType, 3 StorageTemplate, 1 ensure_stock protegido) |
| Webhooks | 7 | 0 (0%) | 4 (57%) | 3 (delivery internos) |
| Alerts | 14 | 0 (0%) | 2 (14%) | 12 (auto-creación) |
| Reports | 5 | 0 (0%) | 5 (100%) | 0 |
| Batch Jobs | 4 | 0 (0%) | 4 (100%) | 0 |
| **Total** | **97** | **46 (47%)** | **72 (74%)** | **25 (26%)** |

**Cobertura ajustada** (excluyendo deliberadamente excluidas): **72 / (97−25) = 72 / 72 = 100%** de las operaciones que DEBEN ser auditadas.

**Cobertura bruta** (todo incluido): **72 / 97 = 74%**

**Cobertura ajustada** (excluyendo lo deliberadamente excluido): **100%** (72/72)

### Justificación de exclusiones

| Excluido | Razón |
|----------|-------|
| StorageType/Template CRUD (6 ops) | Entidades de configuración. Cambio infrecuente (<1 vez/trimestre). Location ya valida storage_type activo (esa validación SÍ está en código auditado). |
| Alert auto-creación (12 ops) | Proceso automático sin intervención humana. Accountability no aplica. El `scan_alerts` batch job se audita con BATCH_JOB_EXECUTED. |
| Webhook delivery interno (3 ops) | Detalle de implementación de la cola de webhooks. La creación del endpoint y la ejecución del job `deliver_webhooks` ya están auditados. |
| Lock stock / next counter / reverse helpers (3 ops) | Helpers internos sin semántica de negocio. La operación de negocio que los invoca ya está auditada. |
| ensure_stock_row_for_tests (1 op) | Se protege con guard DEBUG. No es una operación de negocio. |
| Dashboard / consultas visuales | Sólo lectura. Frecuencia alta. Sería ruido puro. |

---

## 6. Punto 2: BATCH_JOB_EXECUTED — metadata["job_name"]

**Decisión**: SÍ, exigir `job_name` obligatorio.

```python
detail = {
    "job_name": "archive_old_audit_logs",  # obligatorio
    "status": "COMPLETED",                  # STARTED | COMPLETED | FAILED | DRY_RUN
    "_origin": "BATCH",
    # Opcionales por job:
    "archived_count": 1500,
    "elapsed_seconds": 3.2,
    "delivered": 10,
    "failed": 0,
    "errors": [],
}
```

Validación: cualquier nuevo job batch debe incluir `job_name` en el `detail`.

---

## 7. Punto 3: REPORT_GENERATED — formalización de alcance

**Regla**: Solo se auditan:

1. Exportaciones a CSV o XLSX (cuando `export=csv` o `export=xlsx` en query params)
2. `ReportDatasetView.get()` cuando devuelve un dataset con `kind` específico

NO se auditan:
- Consultas visuales de dashboard (`KpiDashboardReportView`, `InventorySummaryReportView`)
- Listados paginados sin exportación
- Refrescos de UI

```python
detail = {
    "kind": "movements-history",  # obligatorio
    "format": "csv",              # "csv" | "xlsx" | "json" (solo dataset)
    "filters": { ... },           # filtros aplicados
    "_origin": "API",
}
```

---

## 8. Punto 4: PURCHASE_ORDER_UPDATED — no solapamiento

**Confirmado**: `update_purchase_order()` modifica datos de una OC en estado BORRADOR sin cambiar su status lifecycle:

- Cambia `expected_delivery` y `notes`
- Reemplaza ítems (borra y recrea `PurchaseOrderItem`)
- **No cambia a CONFIRMED ni CANCELLED**

`PURCHASE_ORDER_CONFIRMED` (BORRADOR → PENDIENTE) y `PURCHASE_ORDER_CANCELLED` (→ CANCELLED) cubren transiciones de estado diferentes. No hay solapamiento semántico.

---

## 9. Cambios en EventTypes — definitivo

```python
# Ubicaciones — entidad de negocio con operaciones protegidas
LOCATION_CREATED = "LOCATION_CREATED", "Ubicación creada"
LOCATION_MODIFIED = "LOCATION_MODIFIED", "Ubicación modificada"
    # metadata obligatorio: _action ∈ {updated, deactivated, state_changed}
    # PUNTO ÚNICO DE EMISIÓN: update_location()

# Webhook endpoints — seguridad: vector de exfiltración
WEBHOOK_ENDPOINT_CHANGED = "WEBHOOK_ENDPOINT_CHANGED", "Endpoint webhook modificado"
    # metadata obligatorio: _action ∈ {created, updated, deactivated}

# Umbrales de reorden — afecta comportamiento operativo
STOCK_THRESHOLD_UPDATED = "STOCK_THRESHOLD_UPDATED", "Umbral de stock actualizado"

# Alertas — accountability de resolución
ALERT_RESOLVED = "ALERT_RESOLVED", "Alerta resuelta"

# Órdenes de compra — documento financiero
PURCHASE_ORDER_UPDATED = "PURCHASE_ORDER_UPDATED", "Orden de compra actualizada"

# Procesos batch — accountability de jobs automáticos
BATCH_JOB_EXECUTED = "BATCH_JOB_EXECUTED", "Job batch ejecutado"
    # metadata obligatorio: job_name
    # metadata adicional: status ∈ {STARTED, COMPLETED, FAILED, DRY_RUN}
```

**Total: 7** (vs 15 originales). Ninguno es redundante. Todos resuelven brechas demostradas en la auditoría.

---

## 10. Plan de Implementación

### Día 1: Event types + Brecha crítica en register_dispatch

- [ ] Agregar 7 nuevos `AuditEventType` en `apps/audit/models.py`
- [ ] `apps/movements/services.py:register_dispatch` (línea ~744): agregar `log_event(MOVEMENT_CREATED)` después del bucle de creación de movements. **Evento faltante crítico descubierto en la validación.**

### Día 1-2: Brechas críticas (H-01 a H-05)

- [ ] `movements/services.py:create_invoice_from_movements` (línea 244): `log_event(INVOICE_GENERATED)`
- [ ] `movements/services.py:register_dispatch` (línea 795): `log_event(DISPATCH_WITH_PRICE_COMPLETED)` si todos tienen precio
- [ ] `reports/views.py:ReportDatasetView.get` (línea ~811): `log_event(REPORT_GENERATED)`
- [ ] `reports/views.py:MovementHistoryReportView.get` (línea 269-274): `log_event(REPORT_GENERATED)` en exports
- [ ] `reports/views.py:ExpiringProductsReportView.get` (línea 555-563): `log_event(REPORT_GENERATED)` en exports
- [ ] `inventory/views.py:InventoryFullListView.get` (línea 145-172): `log_event(REPORT_GENERATED)` en exports
- [ ] `alerts/views.py:AlertListView` (línea 125): `log_event(REPORT_GENERATED)` en exports

### Día 2-3: Protección + Brechas operativas

- [ ] `audit/management/commands/archive_old_audit_logs.py`: `log_event(BATCH_JOB_EXECUTED)` inicio/fin
- [ ] `inventory/management/commands/verify_stock_integrity.py`: `log_event(STOCK_RECONSTRUCTED)` en --fix
- [ ] `inventory/services.py:ensure_stock_row_for_tests`: renombrar a `_ensure_stock_row_for_tests` + guard DEBUG
- [ ] Buscar y actualizar todas las referencias a `ensure_stock_row_for_tests`
- [ ] `audit/models.py:AuditLogArchive`: agregar `save()` blocker

### Día 3-4: Cobertura funcional (Inventory)

- [ ] `inventory/services.py:create_location` (línea ~246): `log_event(LOCATION_CREATED)`
- [ ] `inventory/services.py:update_location` (línea 372): `log_event(LOCATION_MODIFIED)` — **PUNTO ÚNICO**
  - Si `data` contiene `is_active=False` o `operational_status=ARCHIVED`: `_action="deactivated"`
  - Si `data` contiene `operational_status` distinto de ARCHIVED: `_action="state_changed"`
  - Si ninguna de las anteriores: `_action="updated"`
- [ ] `inventory/views.py:StockThresholdView.patch` (línea 708): `log_event(STOCK_THRESHOLD_UPDATED)` — capturar old_value ANTES de la asignación

### Día 4-5: Webhooks, Purchasing, Alerts

- [ ] `webhooks/views.py:WebhookEndpointListCreateView.post`: `log_event(WEBHOOK_ENDPOINT_CHANGED, _action="created")`
- [ ] `webhooks/views.py:WebhookEndpointDetailView.put`: `log_event(WEBHOOK_ENDPOINT_CHANGED, _action="updated")`
- [ ] `webhooks/views.py:WebhookEndpointDetailView.patch`: `log_event(WEBHOOK_ENDPOINT_CHANGED, _action="updated")`
- [ ] `webhooks/views.py:WebhookEndpointDetailView.delete`: `log_event(WEBHOOK_ENDPOINT_CHANGED, _action="deactivated")`
- [ ] `purchasing/services.py:update_purchase_order` (línea 291): `log_event(PURCHASE_ORDER_UPDATED)`
- [ ] `alerts/services.py:resolve_alert` (línea 488): `log_event(ALERT_RESOLVED)`

### Día 5-6: Jobs batch + Tests

- [ ] `webhooks/management/commands/deliver_webhooks.py`: `log_event(BATCH_JOB_EXECUTED)` inicio/fin
- [ ] `alerts/management/commands/scan_alerts.py`: `log_event(BATCH_JOB_EXECUTED)` inicio/fin
- [ ] Extender tests existentes en cada módulo
- [ ] `pytest apps/` — verificar que todo pasa
- [ ] Verificar que imports y event types nuevos no rompen nada

---

## 11. Estimación

| Componente | Días |
|------------|------|
| Fase 1: Event types + register_dispatch gap | 1 |
| Fase 2: Brechas críticas (H-01 a H-05 + exports) | 1.5 |
| Fase 3: Protección + Archive/Verify | 1 |
| Fase 4: Inventory Locations + StockThreshold | 1 |
| Fase 5: Webhooks + Purchasing + Alerts | 1 |
| Fase 6: Jobs batch + Tests | 0.5 |
| **Total** | **6 días** |

---

## 12. Riesgos

| Tarea | Riesgo | Justificación |
|-------|--------|---------------|
| register_dispatch MOVEMENT_CREATED | **Bajo** | Additive tras creación de movements. No toca lógica de negocio. |
| update_location audit (punto único) | **Bajo** | La lógica ya existe. Solo se agrega log_event antes de return. |
| Protection ensure_stock rename | **Medio** | Cambia nombre de función pública. Buscar referencias con `grep -r` y actualizar en el mismo commit. |
| Todas las demás | **Bajo** | Cambios additive, no alteran flujos. |

---

## 13. Fuera de Alcance (explícito)

1. **StorageType/Template CRUD** — Configuración, cambios infrecuentes, bajo impacto.
2. **Alertas automáticas** — Procesos automáticos sin accountability humana.
3. **Webhook delivery interno** — Detalle de implementación.
4. **Helpers internos** (`_lock_stock`, `_reverse_*`, `_next_invoice_number`, etc.)
5. **Dashboard** — Sólo lectura, frecuencia alta.
6. **Consultas GET sin exportación** — No se auditan.
7. **`@auditable` en código existente** — Para código nuevo únicamente.
8. **`changed_fields`** — Mejora futura, no necesaria para cerrar brechas.
9. **Nuevas columnas en BD** — metadata JSON es suficiente.
10. **Middleware / trace_id / correlation_id** — Sin necesidad real demostrada.
11. **Particionamiento de BD** — Cuando existan millones de registros.
