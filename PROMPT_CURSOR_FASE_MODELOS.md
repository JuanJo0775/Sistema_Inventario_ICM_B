# PROMPT FASE 1 — Modelos del Sistema ICM (Import Corporal Medical)
> **Instrucción para Cursor**: Implementa los modelos Django de todo el sistema ICM siguiendo
> estrictamente la documentación del proyecto. Esta es la FASE 1: solo modelos (`models.py`).
> No implementes servicios, views, serializers ni lógica de negocio en esta fase.

---

## 📋 CONTEXTO OBLIGATORIO

Antes de escribir cualquier línea de código, **lee y estudia** la documentación completa del proyecto
ubicada en `docs/`. Esta documentación es la fuente de verdad del sistema. Los tres documentos son:

- `docs/README_ARQUITECTURA.md` → Arquitectura técnica, estructura de apps, reglas de implementación,
  patrones, decisiones de diseño, modelo de inventario Ledger+Stock y checklist de integridad.
- `docs/ERS_ICM_Requisitos.md` → 12 requisitos funcionales (RF-001 a RF-012) y 6 no funcionales
  con criterios de aceptación en formato Gherkin. Estos son los contratos del sistema.
- `docs/ICM_Informe_Elicitacion_v2_plus_docx.md` → Contexto del negocio, entidades del dominio,
  atributos detallados de cada entidad, reglas de negocio (BR-01 a BR-13) y actores del sistema.

**No asumas nada que no esté en estos documentos.**
Cuando un modelo soporte una regla de negocio, agrégala como comentario inline (`# BR-XX`).

---

## 🏗️ ARQUITECTURA DEL PROYECTO

El proyecto es un monolito modular Django con la siguiente estructura de apps (ya creada):

```
icm_backend/
├── apps/
│   ├── authentication/   # RF-001, RF-002 — Usuarios, roles, RBAC
│   ├── catalog/          # RF-003 — Productos, categorías, combos/kits
│   ├── inventory/        # RF-004 — Stock por ubicación, ubicaciones
│   ├── movements/        # RF-005 a RF-009 — Ledger de movimientos (NÚCLEO)
│   ├── reports/          # RF-010 — Solo lectura, sin modelos propios de negocio
│   ├── alerts/           # RF-011 — Alertas proactivas
│   └── audit/            # RF-012 — Log de auditoría inmutable
├── shared/
│   └── models.py         # BaseModel con campos comunes
└── docs/                 ← DOCUMENTACIÓN OBLIGATORIA (leer antes de implementar)
```

---

## 🎯 TU MISIÓN EN ESTA FASE

Implementar **únicamente los archivos `models.py`** de cada app, más el `shared/models.py`.
Los modelos deben ser la representación fiel del dominio, con:

- Constraints de base de datos correctos (no lógica de negocio).
- Campos con los tipos apropiados, `null`, `blank`, `default` bien definidos.
- Relaciones `ForeignKey` / `ManyToMany` con `related_name` descriptivos.
- `Meta` con índices, `ordering`, `verbose_name` y `verbose_name_plural`.
- Docstrings que referencian los RF y BR de la documentación.
- Comentarios `# BR-XX` en cada campo o constraint relacionado con una regla de negocio.
- `__str__` útil en cada modelo.
- **Sin ninguna lógica de negocio** — esa va en `services.py` (fase posterior).

---

## 📦 ESPECIFICACIÓN POR APP

### `shared/models.py` — Base reutilizable

Crea `BaseModel` como clase abstracta con:
- `id` como `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- `created_at = DateTimeField(auto_now_add=True)`.
- `updated_at = DateTimeField(auto_now=True)`.

> **Importante**: Los modelos que son inmutables por diseño (Movement, AuditLog) NO tendrán
> `updated_at`. Esto es intencional: si un modelo no puede ser modificado, no tiene sentido
> registrar una fecha de última modificación.

---

### `apps/authentication/models.py` — Usuarios y Roles

**Referencia**: RF-001, RF-002, BR-01, BR-02, BR-03. Leer secciones 3 y 3.1.1 de `README_ARQUITECTURA.md`.

Implementa `User` extendiendo `AbstractUser` de Django con:

- `role = CharField(choices=...)` con opciones: `almacenista`, `auxiliar_despacho`, `administrador`.
  - Este campo es el núcleo del RBAC. Ver roles y permisos en sección 3 del informe de elicitación.
- `is_active` (heredado) se usa para habilitar/deshabilitar cuentas (BR-02).
- `created_by = ForeignKey('self', null=True, blank=True, on_delete=SET_NULL)`:
  - Registra qué Almacenista creó esta cuenta (BR-01, BR-02).
- `phone = CharField(max_length=20, blank=True)`: contacto opcional.

**Restricciones a modelar como constantes/choices** (sin lógica de negocio):
- Definir un `enum` o `TextChoices` para `RoleChoices`: `ALMACENISTA`, `AUXILIAR_DESPACHO`, `ADMINISTRADOR`.

**Meta**: `verbose_name = "Usuario"`, ordering por `username`.

---

### `apps/catalog/models.py` — Catálogo de Productos

**Referencia**: RF-003, BR-04, BR-05, BR-12, BR-13. Leer sección 4 completa del informe de elicitación
y sección 3.1.2 de `README_ARQUITECTURA.md`.

#### Modelo `Category`

Representa las macrocategorías del catálogo ICM: Electroterapia, Manoterapia, Mesas de Fisioterapia.

Campos:
- `name = CharField(unique=True)`.
- `slug = SlugField(unique=True)`: para URLs y referencias internas.
- `requires_serial_number = BooleanField(default=False)`:
  - `True` para Electroterapia (BR-04). El services.py lo usará para validar entradas.
- `is_returnable = BooleanField(default=False)`:
  - `True` solo para Electroterapia/Electrónicos (BR-05). El services.py lo usará para validar devoluciones.
- `description = TextField(blank=True)`.

#### Modelo `Subcategory`

- `name = CharField`.
- `category = ForeignKey(Category, on_delete=CASCADE, related_name='subcategories')`.
- `slug = SlugField`.

#### Modelo `Product`

Es la entidad central del dominio. Ver atributos completos en sección 4.1 del informe de elicitación.

Campos obligatorios:
- `sku = CharField(max_length=100, unique=True)`:
  - Prefijo `CAN-` obligatorio para marca propia (BR-12). La validación irá en services, pero
    añade un comentario `# BR-12: validado en catalog/services.py::create_product`.
- `barcode = CharField(max_length=100, null=True, blank=True, unique=True)`:
  - Código de barras físico. Actúa como alias de escaneo (BR-13). Puede ser null si el producto
    no tiene código impreso aún. Debe tener `db_index=True`.
- `name = CharField(max_length=255)`.
- `category = ForeignKey(Category, on_delete=PROTECT, related_name='products')`.
- `subcategory = ForeignKey(Subcategory, on_delete=SET_NULL, null=True, blank=True)`.
- `brand = CharField(max_length=100, default='Can')`:
  - Marca del producto. Si es 'Can', el SKU debe tener prefijo CAN- (BR-12).
- `expiration_date = DateField(null=True, blank=True)`:
  - Fecha de vencimiento. Activa alertas a 30 y 60 días (RF-011). El campo puede ser null
    para productos que no vencen.
- `weight_grams = PositiveIntegerField(null=True, blank=True)`:
  - Peso en gramos. Usado para calcular capacidad de transporte en despachos.
- `requires_cold_chain = BooleanField(default=False)`:
  - Si True, el sistema muestra alerta visual persistente en picking (ver sección 4.1 del informe).
- `is_active = BooleanField(default=True)`:
  - Permite desactivar productos del catálogo sin eliminarlos.
- `notes = TextField(blank=True)`: observaciones adicionales.

**Meta**: `indexes` sobre `sku`, `barcode`, `category`. `ordering = ['name']`.

#### Modelo `ProductCombo` (Kit / Combo)

Permite agrupar múltiples SKUs bajo un identificador de combo (ver sección 4.1 del informe de elicitación).

- `name = CharField(max_length=255)`.
- `sku = CharField(max_length=100, unique=True)`.
- `is_active = BooleanField(default=True)`.
- `products = ManyToManyField(Product, through='ComboItem')`.

#### Modelo `ComboItem` (tabla intermedia)

- `combo = ForeignKey(ProductCombo, on_delete=CASCADE)`.
- `product = ForeignKey(Product, on_delete=CASCADE)`.
- `quantity = PositiveIntegerField(default=1)`.

---

### `apps/inventory/models.py` — Ubicaciones y Stock Derivado

**Referencia**: RF-004, BR-11. Leer secciones 4.2 y 4.5 de `README_ARQUITECTURA.md` y
sección 4.2 del informe de elicitación.

#### Modelo `Location`

Las tres ubicaciones físicas del sistema: Vitrina, Bodega 1, Bodega 2.

- `code = CharField(max_length=50, unique=True)`:
  - Valores esperados: `'VITRINA'`, `'BODEGA_1'`, `'BODEGA_2'`.
  - Definir como `LocationChoices(TextChoices)` para usar en constraints y referencias.
- `name = CharField(max_length=100)`.
- `description = TextField(blank=True)`.
- `is_retail = BooleanField(default=False)`:
  - `True` solo para Vitrina. Define si es punto de venta minorista o mayorista.
- `is_active = BooleanField(default=True)`.

**Meta**: `verbose_name = "Ubicación"`.

#### Modelo `StockByLocation`

Caché derivado del stock actual. **NO es la fuente de verdad** — el Ledger (Movement) lo es.
Ver sección 4.2 y 4.3 de `README_ARQUITECTURA.md`.

- `product = ForeignKey('catalog.Product', on_delete=PROTECT, related_name='stock_by_location')`.
- `location = ForeignKey(Location, on_delete=PROTECT, related_name='stock_items')`.
- `current_stock = PositiveIntegerField(default=0)`:
  - `# BR-11: constraint CHECK current_stock >= 0 en BD`.
  - Añadir `CheckConstraint(check=Q(current_stock__gte=0), name='stock_non_negative')`.
- `last_movement_at = DateTimeField(null=True, blank=True)`:
  - Timestamp del último movimiento que alteró este stock. Ayuda a auditorías rápidas.

**Meta**:
- `unique_together = ('product', 'location')` → BR-11.
- `indexes` sobre `(product, location)` para consultas rápidas de stock.
- `verbose_name = "Stock por Ubicación"`.

---

### `apps/movements/models.py` — Ledger de Movimientos (NÚCLEO)

**Referencia**: RF-005, RF-006, RF-007, RF-008, RF-009, BR-01, BR-04, BR-06, BR-07, BR-08,
BR-09, BR-10, BR-11, BR-13. Leer secciones 4.1 a 4.4 completas de `README_ARQUITECTURA.md`.

> Este es el modelo más crítico del sistema. El ledger de movimientos es la fuente de verdad
> inmutable de todo el inventario. Lee con atención antes de implementar.

#### Modelo `Movement`

Cada registro representa un cambio atómico e inmutable en el inventario. Una vez creado, no
puede modificarse ni eliminarse (BR-10).

Implementa **exactamente** estos campos (consulta sección 4.1 de `README_ARQUITECTURA.md`
para la descripción completa de cada uno):

```
Identificación:
- id: UUIDField (primary_key, auto-generado)
- movement_type: CharField con choices (ver MovementType abajo)

Producto y ubicaciones:
- product: ForeignKey catalog.Product (PROTECT)
- origin_location: ForeignKey inventory.Location (null, para entradas no hay origen)
- destination_location: ForeignKey inventory.Location (null, para salidas no hay destino)

Cantidad y snapshots de stock (BR-11):
- quantity: PositiveIntegerField
- stock_previo_origen: PositiveIntegerField (null=True — null para entradas)
- stock_resultante_origen: PositiveIntegerField (null=True — null para entradas)
- stock_previo_destino: PositiveIntegerField (null=True — solo traslados/entradas)
- stock_resultante_destino: PositiveIntegerField (null=True — solo traslados/entradas)

Atributos de validación por regla de negocio:
- serial_number: CharField(max_length=100, null, blank) — BR-04: obligatorio en Electroterapia
- quantity_invoiced: PositiveIntegerField(null) — BR-09: cantidad en factura del proveedor
- discrepancy_note: TextField(null, blank) — BR-09: nota si qty != qty_invoiced
- justification: TextField(null, blank) — BR-07: obligatorio en AJUSTE

Validación cruzada en despacho (BR-08):
- scanned_code: CharField(max_length=100, null, blank) — código físicamente escaneado
- order_sku: CharField(max_length=100, null, blank) — SKU esperado de la orden

Facturación (BR-13):
- invoice_number: CharField(max_length=20, unique=True, null, blank) — formato ICM-0001
- invoice_pdf: FileField(upload_to, null, blank) — archivo PDF generado

Auditoría y trazabilidad (BR-01, BR-10):
- executed_by: ForeignKey authentication.User (PROTECT) — quién ejecutó
- created_at: DateTimeField(auto_now_add=True) — timestamp UTC inmutable

Vínculos para correcciones (BR-06):
- related_movement: ForeignKey('self', null, blank, on_delete=SET_NULL) — movimiento referenciado
```

**Tipos de movimiento** — Definir `MovementType(TextChoices)`:
- `ENTRADA` → Recepción de mercancía (RF-005).
- `SALIDA_VENTA_MAYOR` → Despacho a cliente mayorista (RF-006).
- `SALIDA_VENTA_MENOR` → Despacho minorista en vitrina (RF-006).
- `SALIDA_DANO` → Baja por producto dañado (RF-009).
- `SALIDA_VENCIMIENTO` → Baja por vencimiento (RF-011).
- `TRASLADO` → Movimiento interno entre ubicaciones, sin cambio de stock global (RF-007, BR-11).
- `AJUSTE` → Corrección con justificación, solo Almacenista (RF-009, BR-07).
- `DEVOLUCION` → Reingreso de producto, solo Electroterapia/Electrónicos (RF-008, BR-05).

**Meta** (crítico para rendimiento — ver checklist sección 13 de `README_ARQUITECTURA.md`):
- `indexes`:
  - `(product, movement_type, created_at)` — consultas por tipo de movimiento por producto.
  - `(executed_by, created_at)` — trazabilidad por usuario.
  - `(origin_location, created_at)` — reporte por ubicación.
  - `(destination_location, created_at)` — idem.
  - `(invoice_number,)` — búsqueda de facturas.
- `ordering = ['-created_at']`.
- `verbose_name = "Movimiento"`.

**Importante**: NO agregues `updated_at` — este modelo es inmutable por diseño (BR-10).
**No agregues** `save()` override, signals, ni lógica. Todo va en `movements/services.py`.

#### Modelo `InvoiceCounter`

Modelo auxiliar para la numeración secuencial atómica de facturas (BR-13).
Evita race conditions al generar el número de factura ICM-XXXX.

- `last_number = PositiveIntegerField(default=0)`.
- Es un singleton: siempre existirá exactamente un registro.

> El services.py usará `select_for_update()` sobre este modelo para generar el siguiente número
> de forma atómica. Esto garantiza que no haya duplicados incluso con concurrencia.

---

### `apps/alerts/models.py` — Alertas Proactivas

**Referencia**: RF-011, BR-04, BR-11. Leer sección RF-011 completa de `ERS_ICM_Requisitos.md`.

#### Modelo `Alert`

Registra alertas operativas generadas por el sistema: stock mínimo, vencimientos próximos,
descalibración del stock derivado vs. ledger.

- `alert_type = CharField(choices=AlertType)`.
  - Definir `AlertType(TextChoices)`:
    - `LOW_STOCK` → Stock por debajo del mínimo definido (BR-11).
    - `EXPIRATION_30` → Producto vence en 30 días.
    - `EXPIRATION_60` → Producto vence en 60 días.
    - `COLD_CHAIN_MISSING` → Producto requiere cadena de frío y hay irregularidad.
    - `STOCK_MISMATCH` → Desincronización entre StockByLocation y ledger.
- `product = ForeignKey('catalog.Product', on_delete=CASCADE, related_name='alerts')`.
- `location = ForeignKey('inventory.Location', on_delete=CASCADE, null=True, blank=True)`:
  - Null si la alerta es global (por ejemplo, vencimiento de producto sin importar ubicación).
- `message = TextField()`: descripción legible para el usuario.
- `is_resolved = BooleanField(default=False)`.
- `resolved_at = DateTimeField(null=True, blank=True)`.
- `resolved_by = ForeignKey('authentication.User', null=True, blank=True, on_delete=SET_NULL)`.
- `created_at = DateTimeField(auto_now_add=True)`.

**Meta**: `ordering = ['-created_at']`. Index sobre `(is_resolved, alert_type)`.

---

### `apps/audit/models.py` — Log de Auditoría Inmutable

**Referencia**: RF-012, BR-01, BR-06, BR-07, BR-10. Leer sección 3.1.4 de `README_ARQUITECTURA.md`
y criterios de aceptación de RF-012 en `ERS_ICM_Requisitos.md`.

#### Modelo `AuditLog`

Registro inmutable de cada evento significativo del sistema (BR-10). Como Movement, no tiene
`updated_at` y no debe exponerse a ningún endpoint de escritura.

Eventos auditados mínimamente (ver sección 3.1.4 de `README_ARQUITECTURA.md`):
autenticación, gestión de usuarios, movimientos, ajustes, reportes, cambios de permisos.

Campos:
- `id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- `event_type = CharField(choices=AuditEventType)`.
  - Definir `AuditEventType(TextChoices)`:
    - `LOGIN_SUCCESS`, `LOGIN_FAILED`.
    - `LOGOUT`.
    - `USER_CREATED`, `USER_UPDATED`, `USER_DISABLED`.
    - `MOVEMENT_CREATED` (con referencia al movimiento).
    - `ADJUSTMENT_CREATED`.
    - `RETURN_CREATED`.
    - `REPORT_GENERATED`.
    - `PERMISSION_CHANGED`.
    - `STOCK_RECONSTRUCTED` → cuando se reconstruye el stock desde el ledger.
- `user = ForeignKey('authentication.User', on_delete=PROTECT, null=True)`:
  - Null solo para eventos de sistema (no iniciados por un usuario). En auth failures puede
    no haber user autenticado todavía.
- `movement = ForeignKey('movements.Movement', on_delete=SET_NULL, null=True, blank=True)`:
  - Referencia opcional al movimiento asociado.
- `description = TextField()`: descripción legible del evento.
- `metadata = JSONField(default=dict, blank=True)`:
  - Datos adicionales del evento (IP, user agent, valores anteriores/nuevos, etc.).
- `ip_address = GenericIPAddressField(null=True, blank=True)`.
- `created_at = DateTimeField(auto_now_add=True)`.

**Meta**:
- `ordering = ['-created_at']`.
- `indexes` sobre `(user, created_at)`, `(event_type, created_at)`.
- `verbose_name = "Log de Auditoría"`.
- **NO agregar `updated_at`** — inmutable por diseño (BR-10).

---

## ✅ CRITERIOS DE CALIDAD PARA ESTA FASE

Antes de considerar completa la implementación, verifica cada punto:

### Estructura y Organización
- [ ] Cada `models.py` importa solo lo que necesita (no hay imports circulares).
- [ ] `shared/models.py` exporta `BaseModel` correctamente.
- [ ] Cada app usa `BaseModel` donde corresponde (excepto Movement y AuditLog que omiten `updated_at`).
- [ ] Todos los `ForeignKey` tienen `related_name` descriptivo.
- [ ] Todos los `on_delete` son los correctos para cada relación del dominio.

### Comentarios y Trazabilidad
- [ ] Cada modelo tiene docstring con referencia a RF y BR.
- [ ] Cada campo relacionado con una regla de negocio tiene `# BR-XX`.
- [ ] Los constraints de BD están comentados explicando qué regla de negocio protegen.

### Constraints de Base de Datos
- [ ] `StockByLocation` tiene `CheckConstraint` para `current_stock >= 0` (BR-11).
- [ ] `StockByLocation` tiene `unique_together = ('product', 'location')` (BR-11).
- [ ] `Movement.invoice_number` es único cuando no es null (BR-13).
- [ ] Los índices de `Movement` cubren los patrones de consulta del sistema (ver checklist sección 13).

### Dominio
- [ ] `Category.requires_serial_number` existe y está comentado con BR-04.
- [ ] `Category.is_returnable` existe y está comentado con BR-05.
- [ ] `Product.barcode` tiene `db_index=True` y es `null=True` (alias de escaneo — BR-13).
- [ ] `Movement` tiene todos los snapshots de stock (`stock_previo_*`, `stock_resultante_*`).
- [ ] `Movement` tiene `executed_by` como campo no nulo (BR-01).
- [ ] `Movement` NO tiene `updated_at` (inmutable — BR-10).
- [ ] `AuditLog` NO tiene `updated_at` (inmutable — BR-10).
- [ ] `InvoiceCounter` existe como modelo singleton para numeración atómica (BR-13).

### Ausencia de Lógica de Negocio
- [ ] Ningún `models.py` contiene métodos de negocio (no `save()` override con validaciones,
  no `clean()` con reglas, no signals en este archivo).
- [ ] Los validators de campo son solo de formato/tipo, no de reglas de negocio.
- [ ] No hay imports de `services.py` en `models.py`.

---

## ⚠️ REGLAS ESTRICTAS

1. **Lógica de negocio = CERO en modelos.** Los modelos son estructura de datos y constraints de BD.
   Las 13 reglas de negocio (BR-01 a BR-13) se implementan en `services.py` (fase posterior).

2. **Inmutabilidad como diseño, no como código.** `Movement` y `AuditLog` son inmutables porque
   las views y services no expondrán endpoints de modificación. No sobreescribas `save()` ni
   uses signals para esto ahora.

3. **Consulta la documentación antes de inventar campos.** Si tienes duda sobre un atributo,
   búscalo en `docs/ICM_Informe_Elicitacion_v2_plus_docx.md` sección 4 (entidades del sistema).

4. **Sé fiel al dominio, pero no te limites a lo mínimo.** Si identificas campos que la
   documentación implica pero no lista explícitamente (por ejemplo, `minimum_stock_threshold`
   en `StockByLocation` para alertas de stock bajo — RF-011), agrégalos con sentido.
   Documenta cualquier decisión que no sea directa de los docs.

5. **No crees datos iniciales (fixtures) en esta fase.** Solo modelos y migraciones.

6. **Usa `settings.AUTH_USER_MODEL`** en lugar de importar `User` directamente para los
   ForeignKey hacia el modelo de usuario.

---

## 📎 REFERENCIAS RÁPIDAS

| App | Modelos principales | RFs cubiertos | BRs clave |
|-----|---------------------|---------------|-----------|
| `shared` | `BaseModel` | Transversal | — |
| `authentication` | `User` | RF-001, RF-002 | BR-01, BR-02, BR-03 |
| `catalog` | `Category`, `Subcategory`, `Product`, `ProductCombo`, `ComboItem` | RF-003 | BR-04, BR-05, BR-12, BR-13 |
| `inventory` | `Location`, `StockByLocation` | RF-004 | BR-11 |
| `movements` | `Movement`, `InvoiceCounter` | RF-005–RF-009 | BR-01, BR-06–BR-11, BR-13 |
| `alerts` | `Alert` | RF-011 | BR-04, BR-11 |
| `audit` | `AuditLog` | RF-012 | BR-01, BR-06, BR-07, BR-10 |

---

> **Nota final**: Esta es la FASE 1. Una vez que los modelos estén completos y las migraciones
> Mantén los modelos limpios: son el contrato que services respetará.
