# Módulo de Auditoría

## 1. Resumen

El módulo `audit` proporciona el registro inmutable de todas las operaciones del sistema. Cada evento de negocio, intento de acceso y modificación de datos queda trazado en `AuditLog`.

**RF-012** — Registro de auditoría para todas las operaciones críticas.
**BR-10** — Inmutabilidad: los registros de auditoría no se modifican ni eliminan.
**RNF-003** — Registro de intentos de acceso no autorizado.

---

## 2. Modelos

### 2.1 AuditLog

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `event_type` | CharField(64) | Tipo de evento (58 valores posibles) |
| `user` | FK -> User (nullable) | Usuario que ejecutó la acción |
| `movement` | FK -> Movement (nullable) | Movimiento asociado (opcional) |
| `description` | TextField | Descripción del evento |
| `metadata` | JSONField(default=dict) | Metadatos adicionales (IP, datos afectados, etc.) |
| `ip_address` | GenericIPAddressField (nullable) | Dirección IP del cliente |
| `created_at` | DateTimeField(auto_now_add) | Marca de tiempo |

**Inmutable:** `save()` rechaza modificaciones de registros existentes con `ImmutableRecordError`.

### 2.2 AuditLogArchive

Misma estructura que AuditLog + `archived_at`. Almacena registros históricos movidos por el comando `archive_old_audit_logs`.

---

## 3. Eventos de auditoría (58 tipos)

| Categoría | Eventos |
|-----------|---------|
| **Autenticación** | LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, PASSWORD_CHANGED, PASSWORD_RESET_REQUESTED, PASSWORD_RESET_COMPLETED |
| **Usuarios** | USER_CREATED, USER_UPDATED, USER_DISABLED, USER_ENABLED, PERMISSION_CHANGED |
| **Movimientos** | MOVEMENT_CREATED, MOVEMENT_CORRECTED (BR-06), ADJUSTMENT_CREATED, RETURN_CREATED, RETURN_APPROVED, RETURN_REJECTED |
| **Productos** | PRODUCT_CREATED, PRODUCT_UPDATED, PRODUCT_DEACTIVATED, PRODUCT_ACTIVATED, PRODUCT_PRICE_UPDATED |
| **Catálogo** | CATEGORY_CREATED/UPDATED/DEACTIVATED/ACTIVATED, BRAND_CREATED/UPDATED/DEACTIVATED/ACTIVATED, SUBCATEGORY_CREATED/UPDATED/DEACTIVATED/ACTIVATED (legacy), COMBO_CREATED/UPDATED/DEACTIVATED/ACTIVATED |
| **Compras** | SUPPLIER_CREATED/UPDATED/DEACTIVATED/ACTIVATED, PURCHASE_ORDER_CREATED/UPDATED/CONFIRMED/CANCELLED, RECEPTION_CREATED/CONFIRMED/CANCELLED |
| **Stock** | STOCK_RECONSTRUCTED, STOCK_THRESHOLD_UPDATED |
| **Alertas** | ALERT_ACKNOWLEDGED, ALERT_RESOLVED |
| **Seguridad** | UNAUTHORIZED_ACCESS_ATTEMPT (RNF-003), MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD (BR-10) |
| **Facturación/Despacho** | INVOICE_GENERATED, DISPATCH_WITH_PRICE_COMPLETED |
| **Reportes** | REPORT_GENERATED |
| **Webhooks** | WEBHOOK_ENDPOINT_CHANGED |
| **Ubicaciones** | LOCATION_CREATED, LOCATION_MODIFIED |
| **Sistema** | BATCH_JOB_EXECUTED |

---

## 4. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `log_event(event_type, ...)` | RF-012 | Registro principal de auditoría |
| `audit_log_event(event_type, ...)` | RF-012 | Alias que no interrumpe flujo si falla |
| `log_unauthorized_access_attempt(...)` | RNF-003 | Registra intento de acceso no autorizado |
| `log_immutable_modification_attempt(...)` | BR-10, RF-012 | Intento de modificar registro inmutable |

---

## 5. Endpoints

Bajo `/api/v1/audit/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/` | Almacenista/Admin | Listar logs (filtros: event_type, user_id, start, end) |
| GET | `<pk>/` | Almacenista/Admin | Detalle de log; PUT/PATCH/DELETE → 405 + log inmutable |

**Permiso:** `IsAlmacenistaOrAdministrador` — solo lectura; escritura denegada por inmutabilidad.

---

## 6. Archivado

Management command `archive_old_audit_logs`:

```
python manage.py archive_old_audit_logs --older-than-days 365 --batch-size 1000
```

Mueve registros antiguos de `AuditLog` → `AuditLogArchive` en batches atómicos. Loggea BATCH_JOB_EXECUTED.

---

## 7. Escenarios esperados

**AUDIT-S01:** Login exitoso → LOGIN_SUCCESS con user, IP, metadata.
**AUDIT-S02:** Movimiento creado → MOVEMENT_CREATED con datos del movimiento.
**AUDIT-S03:** Intento PUT en /audit/<pk>/ → 405 + MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD.
**AUDIT-S04:** Acceso no autorizado (rol incorrecto) → UNAUTHORIZED_ACCESS_ATTEMPT.
**AUDIT-S05:** Consultar logs por rango de fechas → lista paginada filtrada.
**AUDIT-S06:** Consultar logs de un movimiento específico → eventos asociados.
**AUDIT-S07:** Archivado de logs antiguos → registros movidos a AuditLogArchive.
