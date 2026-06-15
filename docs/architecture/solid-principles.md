# Principios SOLID — Sistema Inventario ICM

Análisis de la aplicación de los cinco principios SOLID en el backend Django del sistema ICM. Para cada principio se documenta la evidencia en el código, el beneficio obtenido y las áreas de mejora identificadas.

**Documentos relacionados:**
| | |
|---|---|
| [README_ARQUITECTURA.md](../README_ARQUITECTURA.md) | Contexto arquitectónico general; la §2.2 define la separación de capas que hace posible aplicar SOLID |
| [design-patterns.md](design-patterns.md) | Catálogo de patrones concretos que implementan estos principios (SRP→Service Layer, OCP→jerarquía de excepciones, etc.) |
| [architectural_constraints.md](architectural_constraints.md) | Restricciones estructurales que el SRP y el DIP deben satisfacer |
| [adr_relationships.md](adr_relationships.md) | ADR-002 (separación de responsabilidades) y ADR-007 (RBAC) formalizan SRP e ISP respectivamente |
| [docs/adr/README_ADR.md](../adr/README_ADR.md) | Decisiones arquitectónicas — ADR-002 es la base de la separación de responsabilidades |
| [docs/calidad_restricciones/INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md](../calidad_restricciones/INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md) | Informe de completitud KISS/DRY/YAGNI y atributos de calidad complementarios |

---

## Índice

1. [S — Single Responsibility Principle (SRP)](#1-s--single-responsibility-principle-srp)
2. [O — Open/Closed Principle (OCP)](#2-o--openclosed-principle-ocp)
3. [L — Liskov Substitution Principle (LSP)](#3-l--liskov-substitution-principle-lsp)
4. [I — Interface Segregation Principle (ISP)](#4-i--interface-segregation-principle-isp)
5. [D — Dependency Inversion Principle (DIP)](#5-d--dependency-inversion-principle-dip)

---

## 1. S — Single Responsibility Principle (SRP)

> *Una clase (o módulo) debe tener una única razón para cambiar.*

### Descripción

El SRP se aplica mediante la separación rígida de capas en la arquitectura Django del proyecto. Cada capa tiene una responsabilidad exclusiva y una única razón para cambiar.

### Evidencia en el proyecto

#### Separación de capas

| Archivo / Módulo | Única responsabilidad |
|------------------|----------------------|
| `apps/*/views.py` | Orquestar la request HTTP: autenticación, permisos, delegación a servicios, formatear la Response |
| `apps/*/serializers.py` | Validar y transformar datos de entrada/salida (I/O boundary) |
| `apps/*/services.py` | Ejecutar lógica de negocio y transacciones de dominio |
| `apps/*/selectors.py` | Consultas de solo lectura sin efectos secundarios |
| `apps/*/models.py` | Definir la estructura y restricciones de la persistencia |
| `apps/*/permissions.py` | Evaluar si un usuario tiene acceso a una operación |

#### Ejemplo concreto: módulo de movimientos

```
apps/movements/
├── models.py       # Modelos Movement, MovementType, Invoice, InvoiceCounter
├── serializers.py  # MovementSerializer (I/O)
├── services.py     # register_entry(), register_dispatch(), dispatch_combo()...
├── views.py        # MovementListView, MovementCreateView...
└── tests/
    ├── test_services.py    # pruebas de servicios (sin HTTP)
    └── test_views.py       # pruebas de endpoints (con APIClient)
```

#### `shared/models.py` — responsabilidades separadas en dos clases abstractas

```python
class BaseModel(models.Model):
    """Exclusivamente: identificador UUID y timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Exclusivamente: eliminación lógica (soft delete)."""
    deleted_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True

    def soft_delete(self) -> None: ...
    def restore(self) -> None: ...
```

Separar `BaseModel` de `SoftDeleteModel` permite que entidades como `Movement` hereden solo de `models.Model` directamente (son inmutables y no necesitan soft delete), mientras que `Product`, `Category` o `Location` heredan de ambos.

#### `shared/exceptions.py` — jerarquía de responsabilidades de error

Cada excepción encapsula un único concepto de error de dominio:

```python
class ICMBaseException(Exception):           # raíz: código + mensaje + HTTP status
class AuthenticationError(ICMBaseException)  # fallo de autenticación (401)
class AuthorizationError(ICMBaseException)   # denegación de acceso (403)
class DomainValidationError(ICMBaseException)# validación de reglas de negocio (422)
class SerialNumberRequiredError(DomainValidationError)  # solo BR-04
class InsufficientStockError(InventoryError)            # solo BR-11
```

#### `config/exception_handler.py` — responsabilidad única: traducir excepciones a JSON

```python
def custom_exception_handler(exc, context) -> Response | None:
    """Única razón para cambiar: el contrato de respuesta de error { error, message, detail }."""
```

### Beneficio obtenido

- Los tests de servicios no necesitan instanciar vistas ni serializers.
- Un cambio en el formato de error de la API solo toca `exception_handler.py`.
- Un cambio en la política de permisos solo toca el archivo `permissions.py` correspondiente.

### Oportunidades de mejora

- Algunos `views.py` en módulos más antiguos construyen manualmente diccionarios de respuesta en lugar de delegar a serializers. Se puede mejorar extrayendo esa lógica al serializer correspondiente.

---

## 2. O — Open/Closed Principle (OCP)

> *El software debe estar abierto para extensión y cerrado para modificación.*

### Descripción

El proyecto aplica OCP principalmente a través de jerarquías de clases abiertas a extensión y a composición de permisos.

### Evidencia en el proyecto

#### Jerarquía de excepciones

La jerarquía de `ICMBaseException` permite añadir nuevos tipos de error de dominio **sin modificar** el handler ni las views existentes:

```python
# shared/exceptions.py — extender es agregar una subclase, nunca modificar el handler

class DomainValidationError(ICMBaseException): ...

# Extensión: nuevas reglas de negocio agregan subclases
class SerialNumberRequiredError(DomainValidationError):  # BR-04
    default_code = "SERIAL_NUMBER_REQUIRED"

class CrossValidationFailedError(DomainValidationError):  # BR-08
    default_code = "CROSS_VALIDATION_FAILED"

class AlertAcknowledgementRequiredError(DomainValidationError):  # RF-011
    default_code = "ALERT_ACKNOWLEDGEMENT_REQUIRED"
```

El `custom_exception_handler` detecta `ICMBaseException` y usa `exc.status_code` y `exc.default_code` polimórficamente, sin necesitar `isinstance` para cada subtipo concreto:

```python
def custom_exception_handler(exc, context):
    if isinstance(exc, ICMBaseException):
        # Comportamiento genérico: no importa qué subclase sea
        return Response(
            {"error": exc.default_code, "message": exc.message, "detail": exc.detail_payload},
            status=exc.status_code,
        )
```

#### Sistema de permisos

Añadir un nuevo rol no requiere modificar los permisos existentes; se crea una nueva clase:

```python
# shared/permissions.py — cerrado para modificación

class IsAlmacenista(BasePermission): ...
class IsAuxiliarDespacho(BasePermission): ...
class IsWithinOperatingHours(BasePermission): ...

# Extensión: nuevo permiso sin tocar los existentes
class IsReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.method in SAFE_METHODS)
```

#### Modelos abstractos

Agregar una nueva entidad al sistema que necesite UUID + timestamps + soft delete es extender, no modificar:

```python
# Nueva entidad: solo heredar, sin cambiar shared/models.py
class Alert(BaseModel, SoftDeleteModel):
    ...
```

#### `MovementType` como enumeración extensible

```python
# apps/movements/models.py
class MovementType(models.TextChoices):
    ENTRADA = "ENTRADA"
    SALIDA_VENTA_MAYOR = "SALIDA_VENTA_MAYOR"
    SALIDA_COMBO = "SALIDA_COMBO"
    # Nuevo tipo: agregar valor aquí y un servicio nuevo; los existentes no cambian
```

#### `shared/openapi.py` — tags oficiales como constantes

```python
TAG_AUTH = "auth"
TAG_CATALOG = "catalog"
TAG_MOVEMENTS = "movements"
# Nuevo módulo: agregar TAG_xxx sin modificar los existentes
```

### Beneficio obtenido

- Las reglas de negocio nuevas (BR-N) se añaden como subclases de excepción o como nuevas funciones en `services.py` sin abrir archivos ya probados.
- El sistema de webhooks puede recibir nuevos tipos de evento (`event_type`) sin cambiar la lógica de entrega.

### Oportunidades de mejora

- La lógica de pricing en `dispatch_combo()` contiene condicionales `if price_strategy == "derived" / "fixed"`. Un refactor hacia una clase `PriceStrategy` abstracta con implementaciones `DerivedPriceStrategy` y `FixedPriceStrategy` haría esta decisión más extensible.

---

## 3. L — Liskov Substitution Principle (LSP)

> *Los objetos de una clase derivada deben poder sustituir a los de la clase base sin alterar el comportamiento correcto del programa.*

### Descripción

El LSP se verifica en dos jerarquías principales: la jerarquía de excepciones y la jerarquía de permisos. En ambas, las subclases son sustitutos válidos de sus clases base.

### Evidencia en el proyecto

#### Jerarquía de excepciones — sustitución garantizada

El `custom_exception_handler` recibe cualquier subclase de `ICMBaseException` y la trata uniformemente. Las subclases no rompen el contrato de la clase base:

```python
class ICMBaseException(Exception):
    default_message: str
    default_code: str
    status_code: int = HTTP_400_BAD_REQUEST

    def __init__(self, message=None, *, detail=None):
        self.message = message or self.default_message
        self.detail_payload = detail or {}


# Subclase: cumple el mismo contrato — tiene message, default_code, status_code
class OutsideOperatingHoursError(AuthorizationError):
    default_message = "Acceso no permitido fuera del horario operativo."
    default_code = "OUTSIDE_OPERATING_HOURS"
    # status_code heredado de AuthorizationError → HTTP_403_FORBIDDEN


# CorrectionWindowClosedError extiende ImmutableRecordError pero sobreescribe status_code
# de forma válida (409 es más específico que 405 para este caso de negocio)
class CorrectionWindowClosedError(ImmutableRecordError):
    default_code = "CORRECTION_WINDOW_CLOSED"
    status_code = HTTP_409_CONFLICT  # override justificado: semántica de conflicto de estado
```

Cualquier código que maneje `ImmutableRecordError` también maneja `CorrectionWindowClosedError` correctamente: tiene `.message`, `.default_code` y `.status_code`.

#### Permisos — sustitución en `permission_classes`

Las vistas usan `permission_classes = [IsAlmacenista]` o `[IsAlmacenistaOrAdministrador]`; ambas son intercambiables desde la perspectiva del framework DRF, que llama `.has_permission(request, view)` en cualquiera:

```python
class IsAlmacenista(BasePermission):
    def has_permission(self, request, view) -> bool: ...

class IsAlmacenistaOrAdministrador(BasePermission):
    def has_permission(self, request, view) -> bool: ...

# DRF trata ambas como BasePermission: llama has_permission() sin saber qué subclase es
```

#### `BaseModel` y `SoftDeleteModel` — mixin composition

Las entidades que usan ambos abstractos (`Category(BaseModel, SoftDeleteModel)`) satisfacen el contrato de ambas bases: tienen `.id`, `.created_at`, `.soft_delete()` e `.is_deleted`. Cualquier código que espere un `SoftDeleteModel` puede recibir un `Category`.

### Beneficio obtenido

- El `custom_exception_handler` nunca necesita conocer el subtipo concreto de excepción para funcionar correctamente.
- DRF puede componer permisos en listas y evaluarlos en orden sin importar qué implementación específica use cada elemento.

### Oportunidades de mejora

- `ProductNotReturnableError` es un alias retrocompatible de `ReturnNotAllowedError` (BR-05). Se debería marcar como `deprecated` y planificar su eliminación para evitar dos rutas de herencia que representan el mismo concepto.

---

## 4. I — Interface Segregation Principle (ISP)

> *Los clientes no deben depender de interfaces que no usan.*

### Descripción

El ISP se aplica creando permisos pequeños y específicos, serializers distintos por operación (lectura vs. escritura) y acceso directo a la capa correcta según la operación.

### Evidencia en el proyecto

#### Permisos granulares en lugar de uno monolítico

En lugar de un único permiso `HasAccess(role, hours)`, el sistema define clases específicas que las vistas combinan solo cuando las necesitan:

```python
# shared/permissions.py — interfaz mínima por clase

class IsAlmacenista(BasePermission):
    # Solo se usa en vistas que requieren este rol exacto
    def has_permission(self, request, view) -> bool: ...

class IsWithinOperatingHours(BasePermission):
    # Solo se añade a vistas donde la franja horaria aplica (auxiliar_despacho)
    def has_permission(self, request, view) -> bool: ...

# Vista que solo necesita almacenista:
class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAlmacenista]

# Vista que necesita horario además del rol:
class MovementCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAlmacenistaOrAuxiliar, IsWithinOperatingHours]
```

#### Serializers específicos por operación — `apps/purchasing/serializers.py`

En lugar de un único `PurchaseOrderSerializer` con todos los campos para todas las operaciones, el módulo define serializers por caso de uso:

| Clase | Uso |
|-------|-----|
| `PurchaseOrderSerializer` | Listado y lectura |
| `PurchaseOrderCreateSerializer` | Creación |
| `PurchaseOrderUpdateSerializer` | Edición parcial |
| `POCancelSerializer` | Cancelación |
| `ReceptionCreateSerializer` | Crear recepción |
| `ReceptionConfirmSerializer` | Confirmar recepción |

```python
# apps/purchasing/views.py — cada view usa solo el serializer que necesita
class PurchaseOrderListCreateView(APIView):
    def get(self, request):
        serializer = PurchaseOrderSerializer(queryset, many=True)
        ...
    def post(self, request):
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        ...

class PurchaseOrderCancelView(APIView):
    def post(self, request, pk):
        serializer = POCancelSerializer(data=request.data)  # solo el campo de motivo
        ...
```

#### `shared/openapi.py` — `standard_error_responses()` con parámetros opcionales

La función helper para documentación OpenAPI expone solo los códigos de error relevantes por endpoint, en lugar de incluir todos siempre:

```python
def standard_error_responses(
    *,
    include_400: bool = True,
    include_401: bool = True,
    include_403: bool = False,   # desactivado por defecto
    include_404: bool = False,   # desactivado por defecto
    include_405: bool = False,
    include_409: bool = False,
    include_422: bool = True,
    ...
) -> dict[int, OpenApiResponse]:
```

#### Selectores por módulo — acceso solo a lo necesario

Cada módulo expone solo las consultas que sus clientes requieren:

```python
# apps/inventory/selectors.py  → solo consultas de stock
# apps/audit/selectors.py      → solo filtrado de eventos de auditoría
# apps/reports/selectors.py    → solo queries de KPI y reportes financieros
```

Ningún módulo de negocio importa selectores de un módulo ajeno directamente; la coordinación ocurre a nivel de service o view.

### Beneficio obtenido

- Las vistas de lectura no cargan la lógica de escritura; los serializers de creación no incluyen campos de solo lectura.
- Los permisos se componen solo donde se necesitan, sin que una view cargue validaciones irrelevantes.
- Menor acoplamiento entre módulos: `catalog` no depende de la interfaz completa de `purchasing`.

### Oportunidades de mejora

- Algunos serializers de listado (`MovementSerializer`) incluyen campos de precio que solo son relevantes para despachos. Un refactor a `MovementListSerializer` y `MovementDetailSerializer` alinearía mejor el ISP en este módulo.

---

## 5. D — Dependency Inversion Principle (DIP)

> *Los módulos de alto nivel no deben depender de módulos de bajo nivel. Ambos deben depender de abstracciones.*

### Descripción

El DIP se aplica a través de tres mecanismos: dependencia en abstracciones del dominio (excepciones, modelos), inyección de dependencias en servicios (reciben entidades en lugar de IDs cuando es práctico), y el handler de excepciones que depende de la abstracción `ICMBaseException` y no de tipos concretos.

### Evidencia en el proyecto

#### `custom_exception_handler` depende de la abstracción `ICMBaseException`

```python
# config/exception_handler.py

from shared.exceptions import ICMBaseException, AuthenticationError, AuthorizationError

def custom_exception_handler(exc, context):
    if isinstance(exc, ICMBaseException):          # abstracción de alto nivel
        return Response(
            {"error": exc.default_code, ...},      # usa atributos del contrato base
            status=exc.status_code,
        )
    # Fallback al handler de DRF (abstracción del framework)
    response = drf_exception_handler(exc, context)
```

El handler **no depende** de `SerialNumberRequiredError`, `InsufficientStockError` ni ningún tipo concreto. Depende del contrato de `ICMBaseException`.

#### Los servicios reciben abstracciones del dominio, no detalles HTTP

Los servicios no reciben `request` ni trabajan con `HttpRequest`. Reciben el `user` como una entidad del dominio y los IDs como `UUID`:

```python
# apps/movements/services.py — interface del servicio

@transaction.atomic
def register_entry(
    user: Any,            # entidad de dominio (User), no request
    product_id: UUID,     # identificador abstracto, no un objeto HTTP
    location_id: UUID,
    quantity: int,
    ...
) -> Movement:
```

Las vistas actúan como adaptadores que extraen datos del `request` y llaman al servicio:

```python
# apps/movements/views.py — adaptador HTTP → dominio
class MovementCreateView(APIView):
    def post(self, request):
        ser = MovementCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        movement = register_entry(
            user=request.user,          # extrae del request
            product_id=ser.validated_data["product_id"],
            ...
        )
```

#### `get_for_update_or_404` depende de la abstracción QuerySet, no de modelos concretos

```python
# shared/utils/db.py

def get_for_update_or_404(queryset: Any, *, pk: object) -> Any:
    """
    Acepta cualquier QuerySet — no depende de Product, Location ni ningún modelo concreto.
    """
    try:
        return queryset.select_for_update().get(pk=pk)
    except queryset.model.DoesNotExist:
        raise ResourceNotFoundError(...)
```

Todos los servicios del proyecto pueden usar la misma función con cualquier modelo.

#### `audit.services.log_event` depende de abstracciones con `TYPE_CHECKING`

```python
# apps/audit/services.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.authentication.models import User
    from apps.movements.models import Movement


def log_event(
    event_type: str,
    *,
    user: "User | None" = None,
    movement: "Movement | None" = None,
    ...
) -> AuditLog:
```

El uso de `TYPE_CHECKING` evita importaciones circulares en tiempo de ejecución: el servicio de auditoría no depende de los módulos de autenticación o movimientos en runtime, solo en tiempo de análisis estático.

#### Inyección implícita a través de `settings` de Django

Los servicios no instancian clases de infraestructura directamente. El almacenamiento de archivos (`MEDIA_ROOT`, `DEFAULT_FILE_STORAGE`), la base de datos (`DATABASES`) y el correo (`EMAIL_BACKEND`) se configuran en `config/settings/` y se inyectan por Django al sistema:

```python
# apps/movements/models.py
invoice_pdf = models.FileField(upload_to="invoices/%Y/%m/")
# No instancia StorageBackend; depende de la abstracción de Django FILE_STORAGE
```

### Beneficio obtenido

- Es posible cambiar el backend de almacenamiento (S3, FileSystem) sin modificar ningún servicio.
- Los tests pueden usar `override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')` sin tocar código de producción.
- Los servicios son reutilizables desde management commands, tasks asíncronos o scripts de seed, porque no dependen del protocolo HTTP.

### Oportunidades de mejora

- Algunos servicios importan directamente modelos de otros módulos (`from apps.catalog.models import Product`). En una arquitectura estrictamente hexagonal, estas dependencias cruzadas pasarían por puertos/interfaces. Para el tamaño actual del proyecto, el acoplamiento es aceptable, pero documentarlo es útil para decisiones de escalado futuras.
- `apps/webhooks/services.py` usa `urllib.request` directamente. Extraer la entrega HTTP a un protocolo (interfaz abstracta) facilitaría reemplazarlo por `httpx` o un cliente con reintentos gestionados, sin cambiar la lógica de negocio del módulo.

---

## Resumen de cumplimiento

| Principio | Nivel de cumplimiento | Evidencia principal |
|-----------|----------------------|---------------------|
| **SRP** | Alto | Separación rígida en 5 capas; `BaseModel`/`SoftDeleteModel` separados; cada excepción = un concepto |
| **OCP** | Alto | Jerarquía de excepciones extensible; permisos como clases independientes; `MovementType` como enum |
| **LSP** | Alto | Handler polimórfico sobre `ICMBaseException`; permisos sustituibles en `permission_classes` |
| **ISP** | Medio-Alto | Serializers por operación; permisos granulares; `standard_error_responses` con flags opcionales |
| **DIP** | Medio-Alto | Servicios sin dependencia HTTP; `get_for_update_or_404` genérico; `TYPE_CHECKING` para evitar ciclos |

El área con mayor margen de mejora es **ISP** en la capa de serializers de los módulos de movements y catalog, donde algunos serializers de listado incluyen campos propios de operaciones de escritura.
