# README de API - Sistema Inventario ICM

Este documento consolida los estándares de la API REST del backend de ICM. Es la referencia operativa para construir, documentar y mantener los endpoints consumidos por el frontend.

## 1. Objetivo

Definir un contrato de API estable, versionado y documentado para la comunicación entre frontend y backend mediante HTTP/JSON, con autenticación JWT, control RBAC, trazabilidad de errores y documentación OpenAPI 3.

## 2. Alcance

La API cubre los dominios funcionales del backend:

- autenticación y usuarios
- catálogo
- inventario
- movimientos
- reportes
- alertas
- auditoría

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

Los tags se definen centralmente en [shared/openapi.py](shared/openapi.py) y deben reutilizarse sin inventar nombres nuevos.

- `Autenticación`
- `Sistema`
- `Catálogo`
- `Inventario`
- `Movimientos`
- `Reportes`
- `Alertas`
- `Auditoría`

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

- `400` validación o regla de negocio.
- `401` no autenticado.
- `403` prohibido.
- `404` no encontrado.
- `409` conflicto.
- `5xx` error interno.

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

### 10.1 Autenticación

- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/logout/`
- `GET /api/v1/auth/me/`
- `POST /api/v1/auth/users/`
- `PATCH /api/v1/auth/users/<id>/`
- `POST /api/v1/auth/users/<id>/disable/`

### 10.2 Catálogo

- categorías
- subcategorías
- productos
- combos
- resolución de identificadores por SKU, barcode o nombre

### 10.3 Inventario

- consulta de stock por producto
- consulta de stock por ubicación
- búsqueda de productos

### 10.4 Movimientos

- entradas
- salidas
- traslados
- devoluciones
- ajustes
- correcciones dentro de ventana

### 10.5 Reportes

- resumen de movimientos
- resumen de ventas
- historial de movimientos

### 10.6 Alertas

- alertas activas
- alertas de stock mínimo
- alertas de vencimiento

### 10.7 Auditoría

- consulta de eventos de auditoría

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

## 13. Referencias

- [ERS_ICM_Requisitos.md](ERS_ICM_Requisitos.md)
- [Inicial_ICM_Backend_Base.md](Inicial_ICM_Backend_Base.md)
- [README_ARQUITECTURA.md](README_ARQUITECTURA.md)
- [shared/openapi.py](shared/openapi.py)
- [config/urls.py](config/urls.py)
