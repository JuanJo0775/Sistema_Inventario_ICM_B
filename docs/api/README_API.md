# README de API - Sistema Inventario ICM

Este documento consolida los estándares de la API REST del backend de ICM. Es la referencia operativa para construir, documentar y mantener los endpoints consumidos por el frontend.

## 1. Objetivo

Definir un contrato de API estable, versionado y documentado para la comunicación entre frontend y backend mediante HTTP/JSON, con autenticación JWT, control RBAC, trazabilidad de errores y documentación OpenAPI 3.

Este contrato se apoya en la arquitectura general del sistema y en los drivers descritos en [docs/architecture/architecture_drivers.md](../architecture/architecture_drivers.md) y [docs/architecture/utility_tree.md](../architecture/utility_tree.md).

## 2. Alcance

La API cubre los dominios funcionales del backend:

- autenticación y usuarios
- catálogo
- inventario
- movimientos
- dashboard operacional
- reportes (con exportación CSV/XLSX)
- alertas (con polling realtime)
- auditoría
- webhooks (notificaciones a sistemas externos)

> **Documentos relacionados:**
> - Referencia completa de endpoints con ejemplos: [REFERENCIA_ENDPOINTS.md](REFERENCIA_ENDPOINTS.md)
> - Matriz de permisos por rol: [README_MATRIZ_PERMISOS.md](README_MATRIZ_PERMISOS.md)

La comunicación con el frontend se realiza exclusivamente por API REST bajo el prefijo `/api/v1/`.

## 3. Base del contrato REST

### 3.1 Reglas generales

- Toda interacción frontend-backend usa HTTP/JSON.
- El frontend no accede directamente a base de datos, modelos ni servicios internos.
- Cada operación funcional debe exponerse como endpoint DRF.
- El contrato se documenta en OpenAPI 3 y se visualiza en Swagger UI y ReDoc.
- Cualquier cambio incompatible requiere un nuevo prefijo de versión, por ejemplo `/api/v2/`.

### 3.2 Convenciones de rutas

- Prefijo global: `/api/v1/`
- Recursos como sustantivos plurales.
- Acciones específicas en subrutas.
- Filtros y búsquedas por query params.

Ejemplos:

- `/api/v1/auth/login/`
- `/api/v1/catalog/products/`
- `/api/v1/inventory/stock/product/<id>/`
- `/api/v1/movements/entries/`
- `/api/v1/dashboard/overview/`
- `/api/v1/reports/movements/summary/`

### 3.3 Formato de mensajes

- Cuerpos de solicitud y respuesta en JSON UTF-8.
- Fechas en ISO-8601.
- Paginación por número de página.
- Errores con estructura uniforme.

## 4. Documentación OpenAPI

El proyecto usa drf-spectacular como generador OpenAPI 3.

Archivos de referencia:

- [shared/openapi.py](shared/openapi.py)
- [config/urls.py](config/urls.py)
- [config/settings/base.py](config/settings/base.py)

### 4.1 Endpoints de documentación

- `/api/schema/` — esquema OpenAPI
- `/api/docs/` — Swagger UI
- `/api/redoc/` — ReDoc

### 4.2 Tags oficiales

Los tags se definen centralmente en [shared/openapi.py](../../shared/openapi.py) y deben reutilizarse sin inventar nombres nuevos.

| Tag constante | Valor en OpenAPI | Descripción |
|---|---|---|
| `TAG_AUTH` | `auth` | Autenticación JWT y gestión de usuarios |
| `TAG_SYSTEM` | `system` | Verificación de disponibilidad |
| `TAG_CATALOG` | `catalog` | Categorías, productos y combos |
| `TAG_INVENTORY` | `inventory` | Ubicaciones y stock |
| `TAG_MOVEMENTS` | `movements` | Ledger de movimientos de inventario |
| `TAG_DASHBOARD` | `dashboard` | Read model operacional para UI ejecutiva |
| `TAG_REPORTS` | `reports` | Reportes históricos, exportación y datasets |
| `TAG_ALERTS` | `alerts` | Alertas operativas y polling |
| `TAG_AUDIT` | `audit` | Logs de auditoría inmutables |
| `webhooks` | `webhooks` | Gestión de webhooks (definido en `apps/webhooks/views.py`) |

> **Nota:** El tag `webhooks` aún no está en `shared/openapi.py`. Cuando se formalice, debe registrarse allí.

### 4.3 Frontera de dashboard y reportes

- `dashboard` es un read model operacional orientado a UI ejecutiva y pertenece al rol `almacenista`.
- `dashboard` expone contratos composables como `overview`, `metrics`, `alerts`, `kpis` y `movements`.
- `reports` conserva reportes históricos, exportación y datasets analíticos de lectura.
- El dashboard no debe usarse como BI genérico ni como zona de exportaciones; si el producto necesita analítica pesada, esa evolución debe vivir en una frontera futura separada.

Regla:

- Todo endpoint nuevo debe declarar `tags=[...]` con uno de esos valores.
- Las vistas basadas en `APIView` deben documentar `request`, `responses` y, cuando aplique, `parameters`.

## 5. Autenticación y autorización

### 5.1 JWT

La autenticación se realiza con JWT Bearer.

Flujo habitual:

1. `POST /api/v1/auth/login/`
2. El cliente recibe `access` y `refresh`.
3. El frontend envía `Authorization: Bearer <access>` en cada request protegido.
4. `POST /api/v1/auth/token/refresh/` renueva el access token.

### 5.2 Swagger y JWT

En Swagger UI, el token se debe ingresar con el prefijo literal `Bearer `.

### 5.3 RBAC

Roles esperados:

- `almacenista`
- `auxiliar_despacho`
- `administrador`

La autorización se aplica mediante permisos DRF y reglas de negocio por endpoint.

### 5.4 Restricción horaria

Los usuarios con rol `auxiliar_despacho` solo pueden autenticarse y operar dentro de las franjas definidas por el negocio. La validación debe existir tanto en login como en permisos por request.

## 6. Estándares de implementación de endpoints

### 6.1 Vistas y serializers

- Prefiere `APIView` o clases genéricas DRF según el caso.
- Toda entrada debe validarse con serializers.
- La lógica de negocio no debe vivir en `views.py`.

### 6.2 Documentación obligatoria

Todo endpoint nuevo o modificado debe incluir:

- `summary`
- `description`
- `tags`
- `request`
- `responses`
- `parameters`, si aplica
- `auth=[]` en rutas públicas cuando Swagger no deba exigir Bearer

### 6.3 Seguridad en el esquema

- Endpoints protegidos heredan BearerAuth del esquema global.
- Endpoints públicos como login o health deben declararse sin autenticación en la documentación cuando aplique.

### 6.4 Componentes OpenAPI

Si la respuesta no encaja en un serializer clásico, usar componentes explícitos o serializers dedicados para evitar colisiones de nombres.

## 7. Estándares de respuesta

### 7.1 Éxito

- `200` para consultas o actualizaciones exitosas.
- `201` para creación.
- `204` para operaciones sin cuerpo de respuesta.

### 7.2 Error

Forma uniforme:

```json
{
  "error": "codigo_maquina",
  "message": "Mensaje legible",
  "detail": {}
}
```

Semántica recomendada:

#### Uso correcto de códigos HTTP

##### Respuestas exitosas

- `200 OK`: solicitud exitosa con respuesta estándar.
- `201 Created`: recurso creado correctamente.
- `202 Accepted`: solicitud aceptada para procesamiento posterior.
- `204 No Content`: operación exitosa sin contenido de retorno.

##### Errores del cliente (4xx)

- `400 Bad Request`: solicitud inválida, datos faltantes, formato incorrecto o validación fallida.
- `401 Unauthorized`: falta autenticación, token ausente, inválido o expirado.
- `403 Forbidden`: usuario autenticado pero sin permisos.
- `404 Not Found`: recurso inexistente.
- `405 Method Not Allowed`: método HTTP no permitido.
- `406 Not Acceptable`: formato solicitado no soportado.
- `408 Request Timeout`: timeout de solicitud si aplica.
- `409 Conflict`: conflicto de negocio o recurso duplicado.
- `410 Gone`: recurso eliminado permanentemente si aplica.
- `412 Precondition Failed`: precondiciones incumplidas.
- `413 Payload Too Large`: carga excede límites permitidos.
- `415 Unsupported Media Type`: tipo de contenido no soportado.
- `422 Unprocessable Entity`: validación semántica fallida.
- `429 Too Many Requests`: límite de solicitudes excedido.

##### Errores del servidor (5xx)

- `500 Internal Server Error`: error inesperado del servidor.
- `501 Not Implemented`: funcionalidad no implementada.
- `502 Bad Gateway`: error de gateway/proxy si aplica.
- `503 Service Unavailable`: servicio temporalmente no disponible.
- `504 Gateway Timeout`: timeout de gateway si aplica.

## 8. Paginación, filtros y búsqueda

### 8.1 Paginación

Se usa paginación por número de página con soporte para `page_size`.

### 8.2 Filtros

- Usar `django-filter` para filtros de dominio.
- Usar `SearchFilter` para búsquedas por texto.

### 8.3 Rendimiento

- Para listados y búsquedas, evitar N+1 con `select_related` y `prefetch_related`.
- Para stock consolidado, preferir agregaciones en base de datos.

## 9. Seguridad y CORS

### 9.1 JWT y expiración

El backend usa `djangorestframework-simplejwt` con rotación de refresh tokens y blacklist.

### 9.2 CORS

- Desarrollo: orígenes amplios o controlados según el entorno local.
- Producción: lista restringida por variable de entorno.

### 9.3 Transporte y protección

- En producción se fuerza HTTPS.
- Las rutas protegidas deben exigir autenticación.
- El backend no debe exponer trazas internas al cliente final.

## 10. Contratos por módulo

Para el catálogo completo con ejemplos request/response, ver [REFERENCIA_ENDPOINTS.md](REFERENCIA_ENDPOINTS.md).

### 10.1 Autenticación (`/api/v1/auth/`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/auth/health/` | Verificación de servicio (sin auth) |
| `POST` | `/auth/login/` | Obtener tokens JWT |
| `POST` | `/auth/token/refresh/` | Renovar access token |
| `POST` | `/auth/logout/` | Invalidar refresh token |
| `GET` | `/auth/me/` | Perfil del usuario autenticado |
| `GET/POST` | `/auth/users/` | Listar / crear usuarios |
| `GET/PUT/PATCH` | `/auth/users/<uuid:pk>/` | Detalle / actualizar usuario |
| `POST` | `/auth/users/<uuid:pk>/disable/` | Deshabilitar cuenta |

### 10.2 Catálogo (`/api/v1/catalog/`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET/POST` | `/catalog/categories/` | Categorías |
| `GET/PUT/PATCH` | `/catalog/categories/<uuid:pk>/` | Detalle categoría |
| `GET/POST` | `/catalog/subcategories/` | Subcategorías |
| `GET/PUT/PATCH` | `/catalog/subcategories/<uuid:pk>/` | Detalle subcategoría |
| `GET/POST` | `/catalog/products/` | Productos |
| `GET/PUT/PATCH` | `/catalog/products/<uuid:pk>/` | Detalle producto |
| `GET` | `/catalog/products/<uuid:pk>/barcode/` | Payload de código de barras (SVG, Data URI) |
| `GET` | `/catalog/resolve/` | Resolución por SKU, barcode o nombre |
| `GET/POST` | `/catalog/combos/` | Combos (kits de productos) |
| `GET` | `/catalog/combos/<uuid:pk>/` | Detalle combo |

> El detalle de producto expone `barcode`, `barcode_type`, `barcode_payload`, `barcode_svg` y `barcode_svg_data_uri` para impresión de etiquetas.

### 10.3 Inventario (`/api/v1/inventory/`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/inventory/` | Inventario consolidado por producto. Soporta `?export=csv\|xlsx` |
| `GET/POST` | `/inventory/locations/` | Listar / crear ubicaciones |
| `GET/PUT/PATCH/DELETE` | `/inventory/locations/<uuid:pk>/` | Detalle / actualizar / desactivar |
| `POST` | `/inventory/locations/<uuid:pk>/state-transitions/` | Cambiar estado operativo |
| `GET/POST` | `/inventory/storage-types/` | Tipos de almacenamiento |
| `GET/PUT/PATCH/DELETE` | `/inventory/storage-types/<uuid:pk>/` | Detalle tipo almacenamiento |
| `GET/POST` | `/inventory/storage-templates/` | Plantillas de ubicación |
| `GET/PUT/PATCH/DELETE` | `/inventory/storage-templates/<uuid:pk>/` | Detalle plantilla |
| `POST` | `/inventory/reconstruct/` | Reconstruir stock desde ledger |
| `GET` | `/inventory/products/<uuid:product_id>/stock/` | Stock por producto (alias) |
| `GET` | `/inventory/stock/product/<uuid:product_id>/` | Stock por producto |
| `GET` | `/inventory/stock/location/<uuid:location_id>/` | Stock por ubicación |
| `PATCH` | `/inventory/stock/<uuid:pk>/threshold/` | **[NUEVO]** Actualizar umbral de reorden por ubicación |
| `GET` | `/inventory/search/` | Búsqueda de productos (`?q=`, `?category=`, `?subcategory=`) |

**Exportación de inventario consolidado:** `GET /inventory/?export=csv` o `?export=xlsx` devuelve el inventario en el formato indicado con filas aplanadas por producto/ubicación.

**Umbral de stock por ubicación:** `PATCH /inventory/stock/<pk>/threshold/` con `{"location_reorder_point": 5}` o `null` para volver al umbral global del producto. La respuesta incluye `effective_reorder_point`.

### 10.4 Movimientos (`/api/v1/movements/`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/movements/` | Ledger completo (paginado) |
| `GET` | `/movements/<uuid:pk>/` | Detalle de un movimiento |
| `POST` | `/movements/<uuid:pk>/corrections/` | Corrección dentro de ventana BR-06 |
| `GET/POST` | `/movements/entries/` | Entradas de mercancía |
| `GET` | `/movements/entries/<uuid:pk>/` | Detalle entrada |
| `GET/POST` | `/movements/dispatches/` | Despachos (venta mayor/menor) |
| `GET` | `/movements/dispatches/<uuid:pk>/` | Detalle despacho |
| `GET` | `/movements/dispatches/<uuid:pk>/invoice/` | Descarga PDF de factura |
| `GET/POST` | `/movements/transfers/` | Traslados internos |
| `GET/POST` | `/movements/returns/` | Devoluciones |
| `GET/POST` | `/movements/adjustments/` | Ajustes de inventario |
| `POST` | `/movements/adjustments/correct/` | Corrección de ajuste |
| `POST` | `/movements/combo-dispatch/` | Despacho de combo completo |

**Corrección BR-06:** Disponible para `TRASLADO`, `ENTRADA`, `SALIDA_VENTA_MAYOR`, `SALIDA_VENTA_MENOR`. Ventana de 5 minutos desde la creación. Solo el autor puede corregir.

### 10.5 Dashboard (`/api/v1/dashboard/`)

> Solo disponible para `almacenista`. Read model operacional para UI ejecutiva.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/dashboard/overview/` | Resumen general del inventario |
| `GET` | `/dashboard/metrics/` | Métricas de movimientos del día |
| `GET` | `/dashboard/alerts/` | Resumen de alertas críticas |
| `GET` | `/dashboard/kpis/` | KPIs operativos con valores numéricos |
| `GET` | `/dashboard/movements/` | Movimientos recientes para UI |

Todos los endpoints aceptan `?period_days=N` (1–365) y algunos `?expiring_days=N`.

### 10.6 Reportes (`/api/v1/reports/`)

> Disponible para `almacenista` y `administrador`.

| Método | Ruta | Descripción | Exportación |
|---|---|---|---|
| `GET` | `/reports/inventory/summary/` | Resumen de inventario por categoría | — |
| `GET` | `/reports/movements/summary/` | Resumen de movimientos (rango obligatorio) | — |
| `GET` | `/reports/movements/report/` | Reporte detallado de movimientos | — |
| `GET` | `/reports/movements/history/` | Historial filtrable (máx. 200 registros) | `?export=csv\|xlsx` |
| `GET` | `/reports/sales/summary/` | Totales de ventas por período | — |
| `GET` | `/reports/top-products/` | Top productos más despachados | — |
| `GET` | `/reports/invoices/` | Historial de facturas | — |
| `GET` | `/reports/expiring/` | Lotes próximos a vencer (`?days=N`) | `?export=csv\|xlsx` |
| `GET` | `/reports/warehouse-utilization/` | Utilización de almacén por capacidad | — |
| `GET` | `/reports/quality-operational/` | Resumen operativo de calidad | — |
| `GET` | `/reports/discard-operational/` | Resumen operativo de descartes | — |
| `GET` | `/reports/dispatch-operational/` | Resumen operativo de despachos | — |
| `GET` | `/reports/dispatch-operational/orders/` | Órdenes de despacho con filtros | — |
| `GET` | `/reports/kpi/` | Panel KPI (delegado al servicio de dashboard) | — |
| `GET` | `/reports/data/` | Dataset unificado exportable | — |

**Cómo exportar:** Agregar `?export=csv` o `?export=xlsx` a los endpoints que lo soportan. El archivo se descarga directamente. Los CSV usan `StreamingHttpResponse` (seguros para grandes datasets). Los XLSX tienen límite de 10 000 filas; si se supera, se incluye una advertencia en la última fila y el header `X-Export-Truncated: true`.

### 10.7 Alertas (`/api/v1/alerts/`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/alerts/` | Alertas activas (con filtros). Soporta `?export=csv\|xlsx` |
| `GET` | `/alerts/poll/` | **[NUEVO]** Polling de alertas nuevas desde un timestamp |
| `GET` | `/alerts/history/` | Historial de alertas resueltas |
| `GET` | `/alerts/stats/` | Conteos de alertas activas por severidad y categoría |
| `GET` | `/alerts/<pk>/` | Detalle de una alerta |
| `POST` | `/alerts/<pk>/resolve/` | Marcar alerta como resuelta |

**Polling de alertas:** `GET /alerts/poll/?since=<ISO-8601>&severity=CRITICAL,HIGH`
- `since`: timestamp ISO-8601 (UTC). Si se omite, retorna las últimas 24 h.
- `severity`: filtro opcional separado por coma (CRITICAL, HIGH, MEDIUM, LOW, INFO).
- Respuesta incluye `server_timestamp` para usar como próximo `since`.
- Retorna máximo 50 alertas por request, ordenadas por `created_at` descendente.

Ejemplo de respuesta:
```json
{
  "server_timestamp": "2026-05-31T14:00:00.000000+00:00",
  "count": 3,
  "results": [{ "id": 1, "alert_type": "LOW_STOCK", ... }]
}
```

Patrón de polling recomendado:
```js
// Inicializar
let since = new Date().toISOString();
// Cada 30 segundos:
const res = await fetch(`/api/v1/alerts/poll/?since=${since}`);
const data = await res.json();
since = data.server_timestamp;  // usar el timestamp del servidor
```

### 10.8 Auditoría (`/api/v1/audit/`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/audit/` | Lista de logs de auditoría (paginado) |
| `GET` | `/audit/<uuid:pk>/` | Detalle de un log |

Disponible para `almacenista` y `administrador`. Los logs son inmutables (sin endpoints de escritura).

### 10.9 Webhooks (`/api/v1/webhooks/`) — NUEVO

> Solo disponible para `almacenista` (rol rector del sistema, `IsAlmacenista`).
> El rol `administrador` es de solo lectura y **no puede** gestionar webhooks.

| Método | Ruta | Descripción |
|---|---|---|
| `GET/POST` | `/webhooks/endpoints/` | Listar / crear endpoints suscritos |
| `GET/PATCH/DELETE` | `/webhooks/endpoints/<uuid:pk>/` | Detalle / actualizar / desactivar |
| `POST` | `/webhooks/endpoints/<uuid:pk>/test/` | Enviar payload de prueba al endpoint |
| `GET` | `/webhooks/deliveries/` | Historial de entregas (paginado) |
| `GET` | `/webhooks/stats/` | Métricas: pendientes, entregados, fallidos |

**Cómo funcionan:**
1. El administrador crea un `WebhookEndpoint` con `url`, `secret` y lista de `events` suscritos.
2. Cuando el sistema genera una alerta de los eventos suscritos, se encola una `WebhookDelivery`.
3. El cron `deliver_webhooks` (cada 1-2 min) envía los webhooks pendientes como `POST` al endpoint externo.
4. Cada entrega incluye el header `X-ICM-Signature: sha256=<HMAC-SHA256>` para que el receptor verifique la autenticidad.

**Eventos disponibles para suscripción:**

| Evento | Cuándo se dispara |
|---|---|
| `LOW_STOCK` | Cuando el stock de un producto cae al nivel o por debajo del umbral de reorden |
| `STOCK_INTEGRITY_DIVERGENCE` | Cuando `verify_stock_integrity` detecta divergencia entre caché y ledger |

**Cómo verificar la firma (receptor):**
```python
import hashlib, hmac
expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
assert expected == request.headers["X-ICM-Signature"]
```

**Política de reintentos:** Backoff exponencial (1 min → 5 min → 30 min). Después de `max_retries` intentos fallidos, el delivery queda en estado `FAILED`. No se desactiva el endpoint automáticamente.

## 11. Trazabilidad con el resto de la arquitectura

Documentos relacionados:

- [README_ARQUITECTURA.md](README_ARQUITECTURA.md)
- [README.md](README.md)
- [shared/openapi.py](shared/openapi.py)
- [shared/exceptions.py](shared/exceptions.py)
- [shared/permissions.py](shared/permissions.py)

Regla operativa:

- Cualquier cambio de contrato API debe actualizar este documento, el esquema OpenAPI y las pruebas asociadas.

## 12. Checklist antes de publicar un cambio de API

- El endpoint está versionado bajo `/api/v1/`.
- El serializer de entrada y salida está definido.
- La operación tiene `@extend_schema`.
- Los tags coinciden con [shared/openapi.py](shared/openapi.py).
- Los permisos reflejan el ERS.
- Los errores tienen forma uniforme.
- Existe prueba de servicio o vista que cubra el caso.
- El cambio no rompe el contrato existente.


## 14. Módulo de Precios y Facturación (RF-013)

> Este módulo es **completamente opcional y no bloqueante**. El sistema funciona con normalidad sin precios configurados. La integración con el frontend puede hacerse de forma incremental.

### 14.1 ¿Qué hace este módulo?

Añade una capa financiera sobre el ledger de movimientos existente:

- Los productos tienen campos de precio opcionales (`unit_cost`, `sale_price_retail`, `sale_price_wholesale`, `tax_rate_pct`, `currency`). Por defecto son `null`.
- Al despachar, si el producto tiene precio, el sistema congela el snapshot financiero en el Movement (BR-16). Si no tiene precio, los campos quedan `null` y el despacho se completa igual.
- Cada despacho genera un modelo `Invoice` con totales consolidados, incluso si los totales son `0`.
- Cada cambio de precio queda en `ProductPriceHistory` (BR-17).

### 14.2 Campos nuevos en respuestas existentes

Estos campos aparecen en los responses actuales. Son informativos, siempre `null` hasta configurar precios y **no rompen ningún contrato existente**.

**Movement (despachos):**
```json
{
  "unit_price": null,       "unit_cost": null,
  "discount_pct": null,     "discount_amount": null,
  "subtotal": null,         "tax_rate_pct": null,
  "tax_amount": null,       "total_amount": null,
  "currency": "COP",        "price_type": null,
  "customer_snapshot": null
}
```

**Product:**
```json
{ "unit_cost": null, "sale_price_retail": null, "sale_price_wholesale": null, "tax_rate_pct": null, "currency": "COP" }
```

**ProductCombo:**
```json
{ "price_strategy": "derived", "fixed_price_retail": null, "fixed_price_wholesale": null }
```

### 14.3 Configurar precios (almacenista)

El **único** endpoint que modifica precios es `PATCH /catalog/products/<id>/prices/`. El `PUT/PATCH /catalog/products/<id>/` general ignora cualquier campo de precio.

```http
PATCH /api/v1/catalog/products/<uuid>/prices/
Authorization: Bearer <token>

{ "unit_cost": "5000.0000", "sale_price_retail": "12000.0000", "tax_rate_pct": "19.00" }
```

Consultar historial:
```http
GET /api/v1/catalog/products/<uuid>/prices/
```

### 14.4 Despacho con descuento (opcional)

```json
POST /api/v1/movements/dispatches/
{ "product_id": "...", "location_id": "...", "quantity": 3, "movement_type": "SALIDA_VENTA_MENOR", "discount_pct": "10.00" }
```

`discount_pct` puede omitirse. Si el producto no tiene precio, el campo se ignora sin error.

### 14.5 Facturas comerciales

```http
GET  /api/v1/movements/invoices/ICM-0001/       → detalle con totales
GET  /api/v1/movements/invoices/ICM-0001/pdf/   → PDF enriquecido con precios
GET  /api/v1/movements/dispatches/<uuid>/invoice/ → PDF legacy (solo SKU y cantidad, sin precio)
```

Los totales son `0` cuando el producto no tenía precio. La factura se crea igualmente.

### 14.6 Reportes financieros

Requieren `?start=<ISO-8601>&end=<ISO-8601>`. Período default: últimos 30 días.

| Endpoint | Descripción |
|----------|-------------|
| `GET /reports/revenue-summary/` | Revenue total por tipo de venta (mayor/menor/combinado) |
| `GET /reports/margin-by-product/` | Revenue, COGS, margen bruto y margen % por SKU |
| `GET /reports/sales-by-customer/` | Revenue y órdenes por cliente de venta mayor |

Estos reportes solo incluyen movimientos con precio. Si no hay precios, retornan `0` o lista vacía — **nunca un error**.

### 14.7 Combos con precio fijo

Al crear o actualizar un combo se puede especificar `price_strategy: "fixed"` y los precios fijos. Por defecto es `"derived"` (suma de precios individuales de componentes). Campos opcionales:

```json
{ "price_strategy": "fixed", "fixed_price_retail": "50000.0000", "fixed_price_wholesale": "40000.0000" }
```

### 14.8 Reglas de negocio asociadas

| Regla | Implementación |
|-------|---------------|
| BR-16 — Precio congelado en despacho | `movements/services._resolve_price_snapshot()` — el precio del producto al momento del despacho queda inmutable en el Movement |
| BR-17 — Historial auditado de precios | `catalog/services.update_product_prices()` — registra cada cambio en `ProductPriceHistory` |

### 14.9 Compatibilidad hacia atrás

| Endpoint | ¿Cambió el contrato? | Detalle |
|----------|----------------------|---------|
| `POST /movements/dispatches/` | No | `discount_pct` opcional nuevo. Si se omite, comportamiento idéntico. |
| `GET /movements/dispatches/` | No* | Nuevos campos `null` en respuesta. |
| `POST /catalog/products/` | No | Sin campos requeridos nuevos. |
| `PUT/PATCH /catalog/products/<id>/` | No | Los campos de precio son ignorados aquí. |
| `POST /catalog/combos/` | No | `price_strategy` opcional, default `"derived"`. |
| `POST /movements/combo-dispatch/` | No | Comportamiento idéntico. |

*Los campos adicionales en respuestas JSON no rompen clientes REST que ignoran propiedades desconocidas.

---

## 13. Referencias

- [ERS_ICM_Requisitos.md](ERS_ICM_Requisitos.md)
- [Inicial_ICM_Backend_Base.md](Inicial_ICM_Backend_Base.md)
- [README_ARQUITECTURA.md](README_ARQUITECTURA.md)
- [shared/openapi.py](shared/openapi.py)
- [config/urls.py](config/urls.py)
