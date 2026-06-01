# Estados Operativos de Ubicación

## Definición de estados

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Activa | `active` | Operación normal; admite entrada y salida de stock. |
| Mantenimiento | `maintenance` | En reparación o limpieza; solo admite entradas, no salidas. |
| Restringida | `restricted` | Acceso limitado; solo admite entradas, bloquea salidas/despachos. |
| Bloqueada | `blocked` | Completamente bloqueada; ni entradas ni salidas. |
| Archivada | `archived` | Fuera de servicio permanente; ni entradas ni salidas. `is_active=False`. |

---

## Matriz de elegibilidad por operación

| Operación | active | maintenance | restricted | blocked | archived |
|-----------|--------|-------------|------------|---------|----------|
| Entrada (destino) | ✅ | ✅ | ✅ | ❌ | ❌ |
| Despacho (origen) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Traslado — origen | ✅ | ❌ | ❌ | ❌ | ❌ |
| Traslado — destino | ✅ | ✅ | ✅ | ❌ | ❌ |
| Devolución (destino) | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ajuste (↑ destino) | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ajuste (↓ origen) | ✅ | ❌ | ❌ | ❌ | ❌ |

> **Nota de diseño:** la capacidad relativa es **informativa**, no restrictiva. Ningún estado bloquea movimientos por capacidad llena; el bloqueo viene solo del estado operativo.

---

## Endpoint de transición

```
POST /api/v1/inventory/locations/{id}/state-transitions/
{
  "operational_status": "maintenance"   // o restricted, blocked, archived, active
}
```

- **Permiso:** Almacenista.
- No requiere payload adicional.
- Retorna la `Location` actualizada.
- Transición a `archived` fuerza `is_active=False`.
- Transición de `archived` a cualquier otro estado restaura `is_active=True`.

---

## Escenarios esperados

### LOC-STATE-S01 — Despacho bloqueado desde ubicación en mantenimiento

**Precondición:** ubicación en estado `maintenance` con stock disponible.  
**Acción:** `register_dispatch(...)` desde esa ubicación.  
**Resultado esperado:** `LocationStateNotAllowedError` (`LOCATION_STATE_NOT_ALLOWED`, HTTP 422).

---

### LOC-STATE-S02 — Entrada permitida a ubicación en mantenimiento

**Precondición:** ubicación en estado `maintenance`.  
**Acción:** `register_entry(...)` hacia esa ubicación.  
**Resultado esperado:** entrada registrada correctamente; stock incrementa.

---

### LOC-STATE-S03 — Despacho bloqueado desde ubicación archivada

**Precondición:** ubicación en estado `archived` con stock residual.  
**Acción:** `register_dispatch(...)` desde esa ubicación.  
**Resultado esperado:** `LocationStateNotAllowedError`.

> Este es el escenario más crítico de regresión: una ubicación archivada con stock residual no debe poder despachar ni recibir. El stock queda "congelado" hasta que se archive o audite.

---

### LOC-STATE-S04 — Entrada rechazada a ubicación archivada

**Precondición:** ubicación en estado `archived`.  
**Acción:** `register_entry(...)` hacia esa ubicación.  
**Resultado esperado:** `LocationStateNotAllowedError`.

---

### LOC-STATE-S05 — Despacho bloqueado desde ubicación restringida

**Precondición:** ubicación en estado `restricted`.  
**Acción:** `register_dispatch(...)` desde esa ubicación.  
**Resultado esperado:** `LocationStateNotAllowedError`.  
**Diferencia con maintenance:** semánticamente `restricted` implica acceso controlado, no físicamente en reparación.

---

### LOC-STATE-S06 — Entrada permitida a ubicación restringida

**Precondición:** ubicación en estado `restricted`.  
**Acción:** `register_entry(...)` hacia esa ubicación.  
**Resultado esperado:** entrada registrada correctamente.

---

### LOC-STATE-S07 — Traslado bloqueado cuando destino está bloqueado

**Precondición:** origen en `active`, destino en `blocked`. Hay stock en origen.  
**Acción:** `register_internal_transfer(...)` de origen a destino.  
**Resultado esperado:** `LocationStateNotAllowedError` por el destino.

---

### LOC-STATE-S08 — Devolución rechazada a ubicación bloqueada

**Precondición:** ubicación en estado `blocked`.  
**Acción:** `register_return(...)` hacia esa ubicación.  
**Resultado esperado:** `LocationStateNotAllowedError`.

---

### LOC-STATE-S09 — Devolución rechazada a ubicación archivada

**Precondición:** ubicación en estado `archived`.  
**Acción:** `register_return(...)` hacia esa ubicación.  
**Resultado esperado:** `LocationStateNotAllowedError`.

---

### LOC-STATE-S10 — Transición de estado via API

**Precondición:** ubicación activa.  
**Pasos:**
1. POST `/locations/{id}/state-transitions/` con `{"operational_status": "maintenance"}`.
2. Intentar despacho desde ella.

**Resultado esperado paso 1:** `200`, ubicación retorna `operational_status=maintenance`, `is_active=true`.  
**Resultado esperado paso 2:** `422 LocationStateNotAllowedError`.

---

### LOC-STATE-S11 — Archivado fuerza is_active=False

**Precondición:** ubicación activa.  
**Acción:** POST `/locations/{id}/state-transitions/` con `{"operational_status": "archived"}`.  
**Resultado esperado:** `is_active=false` en la respuesta.

---

## Impacto en reportes

- `GET /api/v1/reports/warehouse-utilization/` agrupa por `operational_status` en `by_operational_status`.
- El filtro `?operational_status=active` en `GET /api/v1/inventory/` retorna solo productos con stock en ubicaciones activas.
- El historial `GET /api/v1/reports/movements/history/?location_id={id}` incluye movimientos donde la ubicación fue origen o destino, independientemente del estado actual.
