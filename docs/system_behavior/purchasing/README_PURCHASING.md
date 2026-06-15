# Módulo de Compras (Purchasing)

## 1. Resumen

El módulo `purchasing` gestiona el ciclo de vida de compras: proveedores, órdenes de compra (OC), recepciones de mercancía y distribución por lotes/ubicaciones.

**RF-005** — Recepción de mercancía confirma y actualiza inventario.
**BR-11** — Solo ubicaciones activas/restricted reciben mercancía.
**BR-04** — Serial obligatorio en Electroterapia.
**BR-14** — Location.operational_status debe ser active o restricted.

---

## 2. Modelos

### 2.1 Supplier

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `nombre_comercial` | CharField(200) | Nombre comercial |
| `razon_social` | CharField(200) | Razón social |
| `nit` | CharField(20, unique, nullable) | NIT con dígito de verificación |
| `pais` | CharField(100) | País |
| `correo` | EmailField | Correo electrónico |
| `telefono` | CharField(20) | Teléfono |
| `ciudad` | CharField(100) | Ciudad |
| `direccion` | CharField(300) | Dirección |
| `is_active` | BooleanField(default=True) | Proveedor activo/inactivo para nuevas OC |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel — eliminación lógica |
| `observaciones` | TextField | Notas |
| `created_by` | FK -> User (nullable) | Creador |
| `created_at` / `updated_at` | DateTimeField | Automáticos |

### 2.2 PurchaseOrder

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `number` | CharField(20, unique) | Secuencial OC-XXXX |
| `supplier` | FK -> Supplier | Proveedor |
| `status` | CharField(30) | borrador / pendiente / parcialmente_recibida / completada / cancelada |
| `expected_delivery` | DateField (nullable) | Fecha estimada de llegada |
| `notes` | TextField | Notas |
| `created_by` | FK -> User | Creador |
| `confirmed_by` / `confirmed_at` | FK -> User / DateTime (nullable) | Confirmación |
| `cancelled_by` / `cancelled_at` / `cancellation_reason` | Varios (nullable) | Cancelación |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

Propiedades: `is_editable` (solo BORRADOR), `is_receivable` (PENDIENTE o PARCIALMENTE_RECIBIDA).

### 2.3 PurchaseOrderItem

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `purchase_order` | FK -> PurchaseOrder | OC padre |
| `product` | FK -> Product | Producto |
| `quantity_ordered` | PositiveIntegerField | Cantidad solicitada |
| `unit_cost` | DecimalField(12,4) | Costo unitario acordado |
| `notes` | CharField(300) | Notas de línea |
| `quantity_received` | PositiveIntegerField(default=0) | Acumulado recibido |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

Propiedades: `quantity_pending`, `is_fully_received`.

### 2.4 Reception

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `purchase_order` | FK -> PurchaseOrder | OC asociada |
| `status` | CharField(15) | borrador / confirmada / cancelada |
| `destination_location` | FK -> Location | Ubicación destino |
| `received_by` | FK -> User | Quién recibió |
| `confirmed_at` | DateTime (nullable) | Fecha de confirmación |
| `notes` | TextField | Notas |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

Propiedades: `is_editable` (solo BORRADOR).

### 2.5 ReceptionItem

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `reception` | FK -> Reception | Recepción padre |
| `purchase_order_item` | FK -> PurchaseOrderItem | Item de OC |
| `quantity_received` | PositiveIntegerField | Cantidad recibida |
| `lot_code` | CharField(100) | Código de lote |
| `lot_expiration_date` | DateField (nullable) | Fecha de vencimiento |
| `serial_number` | CharField(100, nullable) | BR-04: Serial obligatorio si categoría lo exige |
| `discrepancy_note` | TextField | Nota si cantidad difiere |
| `movement` | OneToOneField -> Movement (nullable) | Movement ENTRADA generado |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

### 2.6 ReceptionItemAllocation

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `reception_item` | FK -> ReceptionItem | Item padre |
| `location` | FK -> Location | Ubicación destino de la porción |
| `quantity_received` | PositiveIntegerField | Cantidad de esta porción |
| `lot_code` | CharField(100, nullable) | Lote |
| `lot_expiration_date` | DateField (nullable) | Vencimiento |
| `serial_number` | CharField(100, nullable) | BR-04 |
| `movement` | OneToOneField -> Movement (nullable) | Movement ENTRADA generado |
| `created_at` / `updated_at` | DateTimeField | Automáticos (BaseModel) |

Permite distribuir una recepción entre múltiples ubicaciones/lotes.

---

## 3. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `create_supplier(created_by, data)` | — | Registra proveedor, valida NIT único |
| `update_supplier(executor, supplier_id, data)` | — | Actualiza datos, lock con select_for_update |
| `deactivate_supplier(executor, supplier_id)` | — | is_active=False, no afecta OC existentes |
| `activate_supplier(executor, supplier_id)` | — | Reactiva proveedor |
| `soft_delete_supplier(executor, supplier_id)` | SoftDelete | Eliminación lógica + `is_active=False` |
| `restore_supplier(executor, supplier_id)` | SoftDelete | Restauración lógica + `is_active=True` |
| `create_purchase_order(created_by, data)` | — | Crea OC en BORRADOR con items, número secuencial atómico |
| `update_purchase_order(executor, po_id, data)` | — | Solo BORRADOR; recrea items si cambian |
| `confirm_purchase_order(executor, po_id)` | — | BORRADOR → PENDIENTE, bloquea edición |
| `cancel_purchase_order(executor, po_id, reason)` | — | Solo BORRADOR/PENDIENTE; valida sin recepciones confirmadas |
| `create_reception(received_by, po_id, data)` | RF-005, BR-11 | Crea recepción BORRADOR, valida PO receivable, ubicación activa/restricted |
| `confirm_reception(executor, reception_id)` | RF-005, BR-11, BR-14 | BORRADOR → CONFIRMADA; delega a register_entry() por item/allocation; actualiza PO.status |
| `cancel_reception(executor, reception_id)` | — | Cancela recepción en BORRADOR, sin efecto en inventario |

### Flujo de confirmación de recepción

```
confirm_reception()
  → Valida status BORRADOR
  → Lock PO con select_for_update()
  → Valida items con quantity > 0
  → Valida discrepancy_note si aplica
  → Valida Location.operational_status in (active, restricted)
  → Por cada item/allocation:
      → movements.services.register_entry(
           serial_number=item.serial_number or allocation.serial_number,
           ...)
       (BR-04: si la categoría exige serial y es None,
        register_entry() lanza SerialNumberRequiredError)
      → Enlaza movement a ReceptionItem / ReceptionItemAllocation
  → Actualiza PurchaseOrderItem.quantity_received
  → Reception.status = CONFIRMADA
  → Recalcula PO.status (completada/parcialmente_recibida)
```

---

## 4. Endpoints

Todas bajo `/api/v1/purchasing/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET/POST | `suppliers/` | Viewer/Operator | Listar / crear proveedores |
| GET/PUT/PATCH/DELETE | `suppliers/<pk>/` | Viewer/Operator | Detalle / actualizar / desactivar |
| POST | `suppliers/<pk>/deactivate/` | Operator | Desactivar proveedor |
| POST | `suppliers/<pk>/activate/` | Operator | Reactivar proveedor |
| GET/POST | `purchase-orders/` | Viewer/Operator | Listar / crear OC |
| GET/PUT/PATCH | `purchase-orders/<pk>/` | Viewer/Operator | Detalle / editar OC |
| POST | `purchase-orders/<pk>/confirm/` | Operator | Confirmar OC |
| POST | `purchase-orders/<pk>/cancel/` | Operator | Cancelar OC |
| GET/POST | `receptions/` | Viewer/Operator | Listar / crear recepciones |
| GET | `receptions/<pk>/` | Viewer | Detalle recepción |
| POST | `receptions/<pk>/confirm/` | Operator | Confirmar recepción |
| POST | `receptions/<pk>/cancel/` | Operator | Cancelar recepción |

**Permisos:** Viewer = almacenista + administrador; Operator = almacenista.

---

## 5. Flujo OC → Recepción

```
Proveedor → OC (BORRADOR)
  → Confirmar (PENDIENTE)
    → Crear Recepción (BORRADOR)
      → Confirmar Recepción (CONFIRMADA)
        → register_entry() por cada ítem → Movement ENTRADA + StockByLocation
        → OC se actualiza a (PARCIALMENTE_RECIBIDA | COMPLETADA)
```

---

## 6. Escenarios esperados

**PURCH-S01:** Crear OC con items → 201 + PURCHASE_ORDER_CREATED.
**PURCH-S02:** Confirmar OC → status PENDIENTE, bloqueada para edición.
**PURCH-S03:** Editar OC en BORRADOR → cambios permitidos; en PENDIENTE → 400 PurchaseOrderImmutableError.
**PURCH-S04:** Cancelar OC sin recepciones → status CANCELADA.
**PURCH-S05:** Cancelar OC con recepciones confirmadas → 400 POHasConfirmedReceptionsError.
**PURCH-S06:** Crear recepción con cantidad > pendiente → 400 POItemQuantityExceededError.
**PURCH-S07:** Confirmar recepción → Movement ENTRADA creado + StockByLocation actualizado + PO.status recalculado.
**PURCH-S08:** Confirmar recepción con discrepancy → obliga discrepancy_note.
**PURCH-S09:** Confirmar recepción en ubicación BLOCKED → 400 LocationStateNotAllowedError.
**PURCH-S10:** Modo avanzado con allocations → múltiples Movements por ubicación/lote.
