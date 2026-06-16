# Patrones de Diseño — Sistema Inventario ICM

Documento de referencia para desarrolladores. Describe los patrones de diseño aplicados en el backend Django, su ubicación exacta en el código y el motivo de cada decisión.

**Documentos relacionados:**
| | |
|---|---|
| [README_ARQUITECTURA.md](../README_ARQUITECTURA.md) | Contexto arquitectónico general; la §2.2 explica la separación de capas que da origen a estos patrones |
| [solid-principles.md](solid-principles.md) | Análisis SOLID complementario — los principios que justifican por qué se eligieron estos patrones |
| [architectural_constraints.md](architectural_constraints.md) | Restricciones formales que algunos patrones satisfacen (inmutabilidad, no stock negativo, concurrencia) |
| [adr_relationships.md](adr_relationships.md) | Trazabilidad de las decisiones arquitectónicas que formalizan estos patrones |
| [docs/adr/README_ADR.md](../adr/README_ADR.md) | ADR-002 (capas), ADR-005 (ledger), ADR-007 (RBAC) — base de varias de las decisiones de patrón |
| [system_behavior/index.md](../system_behavior/index.md) | Índice de módulos donde estos patrones se aplican en concreto |

---

## Índice

1. [Service Layer (Capa de Servicios)](#1-service-layer)
2. [Selector / Query Object](#2-selector--query-object)
3. [Template Method via Abstract Base Classes](#3-template-method-via-abstract-base-classes)
4. [Strategy (Permisos RBAC)](#4-strategy-permisos-rbac)
5. [Observer / Pub-Sub (Webhooks)](#5-observer--pub-sub-webhooks)
6. [Chain of Responsibility (Manejo de Excepciones)](#6-chain-of-responsibility-manejo-de-excepciones)
7. [Singleton (Contadores Atómicos)](#7-singleton-contadores-atómicos)
8. [Factory (Datos de Prueba)](#8-factory-datos-de-prueba)
9. [Facade (Utilidades de BD)](#9-facade-utilidades-de-bd)
10. [Composite (ProductCombo)](#10-composite-productcombo)

---

## 1. Service Layer

### Descripción

Concentra toda la lógica de negocio en una capa de servicios separada de la capa HTTP (views) y de la capa de persistencia (models). Las vistas delegan en servicios; los servicios no conocen HTTP.

### Ubicación

| Archivo | Responsabilidad |
|---------|----------------|
| `apps/movements/services.py` | Ledger: entradas, despachos, traslados, devoluciones, ajustes, correcciones |
| `apps/catalog/services.py` | CRUD de productos, combos, categorías, precios |
| `apps/inventory/services.py` | Gestión de ubicaciones y tipos de almacenamiento |
| `apps/purchasing/services.py` | Órdenes de compra y recepciones |
| `apps/alerts/services.py` | Generación y resolución de alertas operativas |
| `apps/audit/services.py` | Registro de eventos de auditoría |
| `apps/webhooks/services.py` | Encolado y entrega de webhooks |

### Implementación concreta

Los servicios son **funciones libres** (no clases), marcadas con `@transaction.atomic` cuando escriben en base de datos. Los helpers privados llevan prefijo `_`.

```python
# apps/movements/services.py

@transaction.atomic
def register_entry(
    user: Any,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
    *,
    serial_number: str | None = None,
    ...
) -> Movement:
    """RF-005 — Entrada de mercancía. Valida BR-04 y BR-09."""
    product = get_for_update_or_404(
        Product.objects.select_related("category"), pk=product_id
    )
    location = get_for_update_or_404(Location.objects, pk=location_id)
    _ensure_location_allows_destination(location, "entry")
    _validate_serial_required(product, serial_number)
    ...
```

### Motivo de la decisión

- **Testabilidad**: los servicios son funciones puras que se pueden invocar directamente en tests sin levantar un servidor HTTP.
- **Desacoplamiento**: las views solo orquestan request/response; la lógica de negocio no depende de `HttpRequest`.
- **Trazabilidad**: cada servicio documenta los RF/BR/RNF que implementa en su docstring.
- **Transaccionalidad**: `@transaction.atomic` garantiza consistencia entre el ledger (`Movement`) y el stock derivado (`StockByLocation`).

### Beneficios

- Separación de responsabilidades entre capas Django (view → serializer → service → model).
- El mismo servicio puede ser invocado desde una view REST, un management command o un script de seed sin duplicar lógica.
- Tests unitarios sin mock HTTP.

---

## 2. Selector / Query Object

### Descripción

Las consultas complejas de solo lectura se extraen a módulos `selectors.py`. Un selector lee datos y retorna DTOs o QuerySets; nunca tiene efectos secundarios.

### Ubicación

| Archivo | Responsabilidad |
|---------|----------------|
| `apps/inventory/selectors.py` | Stock por producto y ubicación, reconstrucción de ledger |
| `apps/audit/selectors.py` | Filtrado paginado de eventos de auditoría |
| `apps/reports/selectors.py` | Consultas de KPI y reportes financieros |
| `apps/authentication/selectors.py` | Verificación de franja horaria del auxiliar |

### Implementación concreta

```python
# apps/inventory/selectors.py

def get_stock_by_product(product_id: UUID) -> dict[str, Any]:
    """RF-004 — Stock por ubicación y total consolidado para un producto."""
    product = Product.objects.filter(pk=product_id).only("id", "name", "sku").first()
    rows = (
        StockByLocation.objects
        .filter(product_id=product_id)
        .select_related("location", "location__storage_type")
        .order_by("location__code")
    )
    by_location = [
        {
            "location_id": str(r.location_id),
            "location_code": r.location.code,
            "quantity": r.current_stock,
            ...
        }
        for r in rows
    ]
    total = sum(item["quantity"] for item in by_location)
    return {"product_id": str(product_id), "by_location": by_location, "total": total}
```

### Motivo de la decisión

- Evita que las views acumulen consultas ORM complejas, manteniendo las views limpias.
- Los selectores son deterministas y sin efectos secundarios: fáciles de testear y de cachear.
- Permite optimizar queries (prefetch, aggregation, índices) sin afectar la capa de presentación.

### Beneficios

- Legibilidad: la lógica de lectura está en un lugar conocido.
- Mantenibilidad: cambios en el esquema de consulta no tocan views ni serializers.
- Rendimiento: `select_related`, `prefetch_related` y agregaciones se aplican en un único lugar.

---

## 3. Template Method via Abstract Base Classes

### Descripción

`shared/models.py` define modelos abstractos que establecen la estructura común (identificadores, timestamps, soft delete) para todas las entidades del sistema. Los modelos concretos heredan y extienden sin reimplementar la infraestructura base.

### Ubicación

- `shared/models.py` — `BaseModel`, `SoftDeleteModel`
- Usado por: `apps/catalog/models.py`, `apps/inventory/models.py`, `apps/purchasing/models.py`, `apps/alerts/models.py`, `apps/webhooks/models.py`

### Implementación concreta

```python
# shared/models.py

class BaseModel(models.Model):
    """Base para entidades mutables con identificador UUID (RNF-005)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class SoftDeleteModel(models.Model):
    """Soft delete: deleted_at = NULL → activo; not-NULL → eliminado lógicamente."""
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


# apps/catalog/models.py
class Category(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=128, unique=True)
    requires_serial_number = models.BooleanField(default=False)
    ...
```

### Motivo de la decisión

- **Consistencia**: todas las entidades tienen UUID como PK (en lugar de auto-incremento), evitando colisiones en migraciones y entornos distribuidos.
- **DRY**: el comportamiento de soft delete y timestamps se define una sola vez.
- **Extensibilidad**: nuevas entidades adoptan la convención heredando de `BaseModel` o de ambos abstractos, sin duplicar código.

### Beneficios

- Cambios de convención (ej. timestamp format) se propagan a todas las entidades automáticamente.
- Los tests pueden hacer `assert isinstance(entity.id, UUID)` de forma uniforme.
- `SoftDeleteModel.is_deleted` unifica la lógica de verificación de archivado.

---

## 4. Strategy (Permisos RBAC)

### Descripción

El acceso por rol se implementa como clases de permiso intercambiables (Strategy). Cada `BasePermission` encapsula una política; las vistas componen varias políticas según su contrato.

### Ubicación

- `shared/permissions.py` — permisos globales RBAC
- `apps/purchasing/permissions.py` — permisos específicos del módulo de compras
- `apps/reports/permissions.py` — permisos de reportes

### Implementación concreta

```python
# shared/permissions.py

class IsAlmacenista(BasePermission):
    """BR-02 — Rol rector: permisos operativos y administrativos principales."""
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", None) == "almacenista")


class IsWithinOperatingHours(BasePermission):
    """BR-03 — Auxiliares de despacho solo operan en franjas permitidas."""
    def has_permission(self, request, view) -> bool:
        if getattr(request.user, "role", None) != "auxiliar_despacho":
            return True
        from apps.authentication.selectors import check_user_access
        return check_user_access(request.user)


# Composición en una view:
class MovementCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAlmacenistaOrAuxiliar, IsWithinOperatingHours]
```

### Permisos disponibles

| Clase | Política |
|-------|---------|
| `IsAlmacenista` | Solo rol `almacenista` |
| `IsAuxiliarDespacho` | Solo rol `auxiliar_despacho` |
| `IsAdministrador` | Solo rol `administrador` (solo lectura de reportes) |
| `IsAlmacenistaOrAuxiliar` | Operaciones de almacén o despacho |
| `IsAlmacenistaOrAdministrador` | Lectura compartida de reportes |
| `IsWithinOperatingHours` | Valida franja horaria BR-03 (07:00–12:00 / 14:00–17:00 America/Bogota) |
| `IsReadOnly` | Solo métodos seguros (GET, HEAD, OPTIONS) |

### Motivo de la decisión

- **OCP**: agregar un nuevo rol o política no modifica los permisos existentes; se crea una nueva clase.
- **Composición**: `permission_classes` en cada view combina permisos independientes sin herencia compleja.
- **Testabilidad**: cada permiso se testea en aislamiento con un request mock.

---

## 5. Observer / Pub-Sub (Webhooks)

### Descripción

El sistema de webhooks implementa un patrón Publicador-Suscriptor: los servicios de dominio publican eventos (`queue_webhook_event`); los endpoints registrados son los suscriptores. La entrega es asíncrona con reintentos y backoff.

### Ubicación

- `apps/webhooks/services.py` — `queue_webhook_event()`, `deliver_pending_webhooks()`
- `apps/webhooks/models.py` — `WebhookEndpoint`, `WebhookDelivery`

### Implementación concreta

```python
# apps/webhooks/services.py

def queue_webhook_event(event_type: str, payload: dict) -> int:
    """Encola un evento para todos los endpoints activos suscritos."""
    endpoints = [
        ep
        for ep in WebhookEndpoint.objects.filter(is_active=True)
        if event_type in (ep.events or [])
    ]
    deliveries = [
        WebhookDelivery(
            endpoint=ep,
            event_type=event_type,
            payload=payload,
            status=WebhookDelivery.Status.PENDING,
            next_retry_at=now,
        )
        for ep in endpoints
    ]
    WebhookDelivery.objects.bulk_create(deliveries)
    return len(deliveries)
```

Los servicios de dominio (movements, alerts, etc.) llaman a `queue_webhook_event` al completar una operación, sin conocer quiénes están suscritos. La entrega se procesa mediante `deliver_pending_webhooks()` con `select_for_update(skip_locked=True)` para permitir ejecución paralela sin doble entrega.

### Motivo de la decisión

- **Desacoplamiento**: los servicios de negocio no dependen de los endpoints HTTP externos.
- **Resiliencia**: la entrega asíncrona con retry y backoff exponencial (`[1, 5, 30]` minutos) tolera fallos transitorios.
- **Escalabilidad**: múltiples instancias del cron pueden procesar entregas en paralelo sin colisiones.

---

## 6. Chain of Responsibility (Manejo de Excepciones)

### Descripción

Un handler centralizado intercepta excepciones del dominio ICM y las convierte en respuestas JSON uniformes `{ error, message, detail }`. La cadena evalúa el tipo de excepción en orden de especificidad y delega al handler de DRF para casos no cubiertos.

### Ubicación

- `config/exception_handler.py` — `custom_exception_handler()`
- `shared/exceptions.py` — jerarquía `ICMBaseException`

### Implementación concreta

```python
# config/exception_handler.py

def custom_exception_handler(exc: BaseException, context: dict) -> Response | None:
    if isinstance(exc, ICMBaseException):
        code = exc.status_code
        if isinstance(exc, AuthenticationError):
            code = HTTP_401_UNAUTHORIZED
        elif isinstance(exc, AuthorizationError):
            code = HTTP_403_FORBIDDEN
        elif isinstance(exc, ImmutableRecordError):
            code = HTTP_405_METHOD_NOT_ALLOWED
        return Response(
            {"error": exc.default_code, "message": exc.message, "detail": exc.detail_payload},
            status=code,
        )

    # Delega al handler estándar de DRF para el resto
    response = drf_exception_handler(exc, context)
    if response is not None:
        # Uniforma el formato DRF al contrato ICM
        response.data = {"error": ..., "message": ..., "detail": ...}
        return response
    ...
```

### Motivo de la decisión

- **Contrato uniforme**: todos los errores de la API tienen el mismo formato, independientemente del origen.
- **Centralización**: las views no manejan excepciones individualmente; la lógica de traducción está en un único punto.
- **Extensibilidad**: agregar un nuevo tipo de excepción solo requiere añadir una rama `isinstance` o una subclase.

---

## 7. Singleton (Contadores Atómicos)

### Descripción

Los modelos `PurchaseOrderCounter` e `InvoiceCounter` implementan el patrón Singleton a nivel de base de datos: existe exactamente una fila en la tabla que actúa como contador secuencial atómico para la numeración de documentos.

### Ubicación

- `apps/purchasing/models.py` — `PurchaseOrderCounter`
- `apps/movements/models.py` — `InvoiceCounter`

### Implementación concreta

```python
# apps/purchasing/models.py

class PurchaseOrderCounter(models.Model):
    """Singleton para numeración secuencial atómica de OC (igual que InvoiceCounter)."""
    last_number = models.PositiveIntegerField(default=0)
```

Los servicios obtienen el siguiente número con `select_for_update()` dentro de una transacción atómica, garantizando unicidad bajo concurrencia sin recurrir a secuencias de BD explícitas.

### Motivo de la decisión

- **Atomicidad**: `select_for_update()` bloquea la fila durante la transacción, evitando números duplicados bajo carga concurrente.
- **Portabilidad**: funciona con PostgreSQL y SQLite (para tests), sin depender de secuencias o auto-increment específicos del motor.
- **Auditabilidad**: el número queda almacenado en el registro del documento, facilitando trazabilidad.

---

## 8. Factory (Datos de Prueba)

### Descripción

`tests/factories.py` centraliza la creación de objetos de prueba mediante `factory_boy`. Cada factory encapsula los valores por defecto válidos de un modelo, permitiendo tests concisos y legibles.

### Ubicación

- `tests/factories.py` — factories principales
- Clases: `UserFactory`, `AlmacenistaFactory`, `CategoryFactory`, `ElectroCategoryFactory`, `ProductFactory`, `LocationFactory`, `LotFactory`

### Implementación concreta

```python
# tests/factories.py

class ElectroCategoryFactory(factory.django.DjangoModelFactory):
    """Categoría con serial obligatorio y retornable — simula Electroterapia (BR-04)."""
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Electroterapia-{n}")
    requires_serial_number = True
    is_returnable = True


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    sku = factory.Sequence(lambda n: f"PRD-{n:04d}")
    name = factory.Sequence(lambda n: f"Producto {n}")
    category = factory.SubFactory(CategoryFactory)
```

### Motivo de la decisión

- **DRY en tests**: elimina la repetición de `Product.objects.create(sku=..., name=..., ...)` en cada test.
- **Casos especiales**: `ElectroCategoryFactory` pre-configura las flags `requires_serial_number=True` para tests de BR-04, sin hardcodear valores en cada test.
- **Mantenibilidad**: si el modelo cambia (nuevo campo obligatorio), solo se actualiza la factory.

---

## 9. Facade (Utilidades de BD)

### Descripción

`shared/utils/db.py` expone una función de alto nivel que combina `select_for_update()`, manejo de `DoesNotExist` y lanzamiento de la excepción de dominio correcta (`ResourceNotFoundError`), ocultando la complejidad del ORM a los servicios.

### Ubicación

- `shared/utils/db.py` — `get_for_update_or_404()`
- Usado en: todos los `services.py` del proyecto

### Implementación concreta

```python
# shared/utils/db.py

def get_for_update_or_404(queryset: Any, *, pk: object, detail: str | None = None) -> Any:
    """
    Obtiene un objeto con lock de fila o lanza ResourceNotFoundError (404).
    Uso típico dentro de servicios @transaction.atomic.
    """
    try:
        return queryset.select_for_update().get(pk=pk)
    except queryset.model.DoesNotExist:
        model_name = queryset.model._meta.verbose_name or queryset.model.__name__
        msg = detail or f"{model_name} con ID {pk} no encontrado."
        raise ResourceNotFoundError(msg)


# Uso en un servicio:
product = get_for_update_or_404(
    Product.objects.select_related("category"), pk=product_id
)
```

### Motivo de la decisión

- **Simplifica los servicios**: sin este facade, cada servicio repetiría el bloque `try/except DoesNotExist + select_for_update`.
- **Consistencia**: el mismo mensaje de error y el mismo tipo de excepción en toda la base de código.
- **Concurrencia**: garantiza que el lock de fila siempre se aplica antes de operar sobre un recurso, previniendo condiciones de carrera.

---

## 10. Composite (ProductCombo)

### Descripción

`ProductCombo` es un objeto compuesto formado por varios `Product` mediante la relación intermedia `ComboItem` (M2M with through). El combo puede tratarse como un ítem único de despacho, pero se descompone internamente en sus productos individuales para actualizar el ledger.

### Ubicación

- `apps/catalog/models.py` — `ProductCombo`, `ComboItem`
- `apps/movements/services.py` — `dispatch_combo()`

### Implementación concreta

```python
# apps/catalog/models.py

class ProductCombo(BaseModel, SoftDeleteModel):
    """Kit o combo: varios SKUs bajo un identificador (RF-003)."""

    class PriceStrategy(models.TextChoices):
        DERIVED = "derived", "Derivado de componentes"
        FIXED = "fixed", "Precio fijo del combo"

    sku = models.CharField(max_length=100, unique=True)
    products = models.ManyToManyField(Product, through="ComboItem")
    price_strategy = models.CharField(max_length=20, choices=PriceStrategy.choices)
    fixed_price_retail = models.DecimalField(...)


class ComboItem(BaseModel):
    combo = models.ForeignKey(ProductCombo, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
```

`dispatch_combo()` en `services.py` itera los `ComboItem`, valida stock individual y crea un `Movement` de tipo `SALIDA_COMBO` por cada componente, manteniendo la atomicidad.

### Motivo de la decisión

- **Flexibilidad de precios**: la estrategia `DERIVED` calcula el precio como suma de componentes; `FIXED` usa un precio propio, sin modificar los modelos de `Product`.
- **Integridad del ledger**: el despacho de un combo genera movimientos individuales por producto, manteniendo la trazabilidad de stock por SKU.
- **Extensibilidad**: agregar un nuevo componente a un combo no requiere migración en el modelo `Movement`.
