# StorageType — Tipos de Almacenamiento

## Ciclo de vida

```
Creación (POST /api/v1/inventory/storage-types/)
    │
    ▼
is_active = True  ──── asignable a ubicaciones
    │
    │  PATCH/DELETE (soft)
    ▼
is_active = False ──── NO asignable; ubicaciones existentes NO se afectan
```

La desactivación es **soft**: el tipo queda en base de datos para no romper FKs existentes, pero no puede asignarse a nuevas ubicaciones ni a ubicaciones existentes via PATCH.

---

## Endpoints

| Método | URL | Permiso |
|--------|-----|---------|
| GET | `/api/v1/inventory/storage-types/` | Autenticado |
| POST | `/api/v1/inventory/storage-types/` | Almacenista |
| GET | `/api/v1/inventory/storage-types/{id}/` | Autenticado |
| PUT / PATCH | `/api/v1/inventory/storage-types/{id}/` | Almacenista |
| DELETE | `/api/v1/inventory/storage-types/{id}/` | Almacenista (soft) |

---

## Escenarios esperados

### STOR-TYPE-S01 — Crear tipo y asignarlo a ubicación

**Precondición:** usuario almacenista autenticado.  
**Pasos:**
1. POST `/storage-types/` con `code=bodega-grande`, `name=Bodega Grande`, `category=warehouse`.
2. POST `/locations/` con `name=Bodega Norte`, `storage_type_id=<id_del_paso_1>`.

**Resultado esperado:**
- `201` en ambas peticiones.
- La ubicación retorna `storage_type_code=bodega-grande` en la respuesta.

---

### STOR-TYPE-S02 — Tipo inactivo no asignable a nueva ubicación

**Precondición:** existe `StorageType` con `is_active=False`.  
**Pasos:**
1. DELETE `/storage-types/{id}/` (desactiva).
2. POST `/locations/` con `storage_type_id={id}`.

**Resultado esperado:** `400` o `422` con mensaje `"No se puede asignar un tipo de almacenamiento inactivo."`.

---

### STOR-TYPE-S03 — Tipo inactivo no asignable via PATCH de ubicación

**Precondición:** existe ubicación activa y `StorageType` inactivo.  
**Pasos:**
1. PATCH `/locations/{id}/` con `storage_type_id={id_inactivo}`.

**Resultado esperado:** `400` o `422`.

---

### STOR-TYPE-S04 — Desactivación no afecta ubicaciones ya asignadas

**Precondición:** ubicación con `storage_type` activo y con stock.  
**Pasos:**
1. DELETE `/storage-types/{id}/` (soft delete).
2. GET `/locations/{location_id}/` y GET `/reports/warehouse-utilization/`.

**Resultado esperado:**
- `storage_type_code` sigue presente en la ubicación.
- `by_storage_type` en utilización sigue agrupando esa ubicación.
- Los movimientos desde/hacia la ubicación no se bloquean.

---

### STOR-TYPE-S05 — Filtro de inventario por storage_type_id

**Precondición:** dos ubicaciones con distintos `StorageType`, con stock en ambas.  
**Pasos:**
1. GET `/api/v1/inventory/?storage_type_id={id_tipo_A}`.

**Resultado esperado:** solo aparecen productos con stock en ubicaciones del tipo A.

---

## Integración con reports

`GET /api/v1/reports/warehouse-utilization/` devuelve:
```json
{
  "by_storage_type": [
    {
      "storage_type_code": "bodega-grande",
      "storage_type_name": "Bodega Grande",
      "locations": 3,
      "occupied_units": 120
    }
  ]
}
```
Ubicaciones sin tipo aparecen bajo `"storage_type_code": "untyped"`.
