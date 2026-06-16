# ProductSerial — Unidades serializadas (BR-04)

## 1. Propósito

`ProductSerial` modela una unidad individual serializada. Se comporta como "lotes de 1": cada unidad tiene su propio número de serie que la identifica unívocamente dentro del inventario.

## 2. Modelo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `product` | FK -> Product (PROTECT) | Producto al que pertenece |
| `serial_number` | CharField(100) | Número de serie expandido (único por producto) |
| `status` | CharField(20) | `available`, `dispatched`, `damaged`, `adjusted` |
| `current_location` | FK -> Location (PROTECT, nullable) | Ubicación actual |
| `last_movement` | FK -> Movement (SET_NULL, nullable) | Último movimiento que lo afectó |

Constraint: `uniq_product_serial_per_product` (product + serial_number unique together).

## 3. Expansión batch en entrada

Cuando se registra una entrada con `serial_number` y `quantity=N`, el sistema crea automáticamente N registros `ProductSerial` siguiendo el formato:

```
<serial_base>-<batch_prefix>-<NNN>
```

### Componentes

| Componente | Descripción | Ejemplo |
|------------|-------------|---------|
| `serial_base` | Lo que digitó el usuario en la entrada | `SN-CEL-001` |
| `batch_prefix` | 2 caracteres hex del UUID del movimiento de entrada, agrupa ítems de la misma entrada | `a7` |
| `NNN` | Secuencial de 3 dígitos por unidad (001, 002, ..., N) | `001` |

### Ejemplo

Entrada: `product_id=X, quantity=10, serial_number="SN-CEL-001"`

```
Movement.serial_number = "SN-CEL-001"
ProductSerial creados:
  - SN-CEL-001-a7-001  (available, location=Entrada)
  - SN-CEL-001-a7-002  (available, location=Entrada)
  - ...
  - SN-CEL-001-a7-010  (available, location=Entrada)
```

### Reglas

- El `Movement.serial_number` guarda el serial base (lo que digitó el usuario)
- Los `ProductSerial` guardan los seriales expandidos individuales
- La expansión aplica **siempre** que se provea `serial_number`, incluso con `quantity=1`
- Si la categoría no requiere serial pero el usuario provee uno, igual se crean los `ProductSerial`
- El batch prefix es único por movimiento (derivado del UUID), evitando colisiones entre distintas entradas del mismo producto

## 4. Ciclo de vida del ProductSerial

```
ENTRADA → [AVAILABLE] → DESPACHO → [DISPATCHED]
                      → TRASLADO  → [AVAILABLE] (cambia ubicación)
                      → AJUSTE    → [ADJUSTED]
                      → DAÑO      → [DAMAGED]

DEVOLUCIÓN → [DISPATCHED] → [AVAILABLE] (reactiva)
```

### 4.1 Entrada (creación)

Se crean N `ProductSerial` con `status=AVAILABLE` en la ubicación de destino.

### 4.2 Despacho (consumo)

- Si se provee `serial_id`: se valida que exista, esté `AVAILABLE` y en la ubicación origen
- Si no se provee y la categoría requiere serial: el sistema auto-asigna el primer `ProductSerial` disponible (FIFO por `created_at`)
- Si no hay seriales disponibles → `InsufficientStockError`

### 4.3 Traslado (cambio de ubicación)

Similar al despacho, pero la ubicación destino cambia. El serial mantiene `status=AVAILABLE` durante el traslado.

### 4.4 Devolución (reactivación)

- El usuario debe digitar el **serial completo expandido** (impreso en el equipo), ej: `SN-CEL-001-a7-003`
- El sistema resuelve el string al UUID del `ProductSerial` y lo reactiva a `AVAILABLE` en la ubicación de devolución

### 4.5 Ajuste (baja)

- Cambia el serial a `ADJUSTED`
- Requiere `serial_id` si la categoría tiene `requires_serial_number=True`

## 5. Auto-asignación en despacho/traslado

Cuando no se provee `serial_id` en un despacho o traslado y la categoría requiere serial:

```python
ProductSerial.objects.filter(
    product=product,
    status=ProductSerial.Status.AVAILABLE,
    current_location_id=location_id,
).order_by("created_at").first()
```

Si no hay disponibles → `InsufficientStockError` con detalle del producto y ubicación.

## 6. Serial en el ledger (Movement)

El campo `Movement.serial_number` almacena el serial base (lo que digitó el usuario en entrada) o el serial expandido (en devolución). Es un campo informativo/de auditoría; la fuente de verdad para el estado actual es `ProductSerial`.

## 7. Limitaciones conocidas

- La entrada solo acepta **un** `serial_number` por llamada. Si se necesitan 10 unidades con seriales diferentes, se requieren 10 llamadas. La expansión batch con prefijo resuelve este escenario común: el usuario digita un serial base y el sistema genera N variantes únicas.
- No hay un endpoint para crear `ProductSerial` manualmente (solo se crean via entrada).
