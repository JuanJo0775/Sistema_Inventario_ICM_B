# Sistema Inventario ICM — Backend

Backend del sistema de gestión de inventario y operaciones de Import Corporal Medical (ICM), construido con Django y Django REST Framework.

Este repositorio contiene la estructura del proyecto (arquitectura, configuración, dependencias y contenedorización), preparada para evolucionar la API de forma consistente y documentada.

## Contenido

1. [Propósito del proyecto](#proposito-del-proyecto)
2. [Índice de documentación](#indice-de-documentacion)
3. [Stack tecnológico](#stack-tecnologico)
4. [Configuración por variables de entorno](#configuracion-por-variables-de-entorno)
5. [Inicio rápido](#inicio-rapido)
6. [API REST (OpenAPI y Swagger)](#api-rest-openapi-y-swagger)
7. [README de API](README_API.md)
8. [Trabajo en equipo y buenas prácticas](#trabajo-en-equipo-y-buenas-practicas)
9. [Estado actual](#estado-actual)

## Propósito del proyecto

El sistema busca mejorar la trazabilidad de inventario, la consistencia de stock por ubicación y la seguridad operativa en procesos de recepción, despacho, traslados y auditoría.

En esta fase, el objetivo principal es tener una base técnica completa:

- Estructura modular por dominios.
- Configuración centralizada por entorno.
- Dependencias y herramientas de desarrollo listas.
- API versionada con contrato OpenAPI explícito y documentación en Swagger UI.

## Índice de documentación

Documentación funcional y arquitectónica disponible en el repositorio:

- [ERS_ICM_Requisitos.md](ERS_ICM_Requisitos.md): requisitos funcionales, no funcionales y reglas de negocio.
- [Inicial_ICM_Backend_Base.md](Inicial_ICM_Backend_Base.md): lineamientos de arquitectura base del backend.
- [README_ARQUITECTURA.md](README_ARQUITECTURA.md): arquitectura técnica consolidada (estructura, desacoplamiento, inventario, Docker, testing, SOLID y patrones).
- [ICM_Informe_Elicitacion_v2_plus.docx.md](ICM_Informe_Elicitacion_v2_plus.docx.md): contexto de levantamiento y análisis del dominio.

## Stack tecnológico

- Python 3.11+
- Django 4.2+ (rango declarado en `requirements/base.txt`)
- Django REST Framework
- PostgreSQL
- JWT con djangorestframework-simplejwt
- OpenAPI 3 con **drf-spectacular** (Swagger UI y ReDoc)
- pytest + pytest-django
- Docker + Docker Compose

## Configuración por variables de entorno

### Principio clave

La configuración del sistema se maneja desde variables de entorno. Para desarrollo, el archivo local `.env` es la fuente operativa de configuración para cada equipo.

Flujo recomendado:

1. Copiar `.env.example` como `.env`.
2. Ajustar los valores según el entorno local de cada persona.
3. No editar credenciales en archivos Python de settings.

Esto permite que cada integrante use credenciales distintas (usuario, contraseña, host, puertos) sin tocar código ni generar conflictos al bajar cambios.

### Variables mínimas importantes

### API REST (OpenAPI y Swagger)

La documentación completa de la API, sus estándares de codificación, contrato REST, autenticación JWT, reglas de versión y checklist de validación quedó separada en [README_API.md](README_API.md).

Resumen:

- Esquema OpenAPI 3 generado por código.
- Swagger UI y ReDoc disponibles en `/api/docs/` y `/api/redoc/`.
- Base path de la API en `/api/v1/`.
- Comunicación frontend-backend exclusivamente por API REST.
- Estándares obligatorios de endpoints, tags, errores, paginación y seguridad documentados en el archivo dedicado.

2. **Vistas basadas en `APIView`**  
   drf-spectacular no infiere el cuerpo de respuesta. Debe documentarse explícitamente con **`@extend_schema`** (o `@extend_schema_view` en vistas basadas en clases), incluyendo como mínimo:
   - `request=` cuando haya cuerpo de entrada (serializers)
   - `responses=` para **todos** los códigos relevantes (incluido `204` sin cuerpo si aplica)
   - `parameters=` para query/path cuando no se deduzcan de serializers

3. **Tags**  
   Usar **solo** las constantes definidas en `shared/openapi.py` (`TAG_AUTH`, `TAG_CATALOG`, `TAG_INVENTORY`, etc.) en `tags=[...]` para que coincidan con las descripciones agrupadas del documento y Swagger UI permanezca ordenado.

4. **Seguridad en el esquema**  
   - Endpoints que exijan JWT heredan el esquema global **BearerAuth**.  
   - Rutas **públicas** (por ejemplo login u health) deben declarar `auth=[]` en el `extend_schema` correspondiente para que Swagger no exija Bearer de forma incorrecta.

5. **Serializers como contrato**  
   Preferir serializers DRF para request/response en el esquema. Si la respuesta es un diccionario dinámico, usar serializers explícitos o `inline_serializer` / componentes con nombre único (`@extend_schema_serializer(component_name="...")`) para **no colisionar** nombres en OpenAPI.

6. **Permisos y reglas de negocio**  
   Alinear `permission_classes` con lo que el ERS exige; documentar en la descripción de la operación (summary/description en `extend_schema`) cualquier prerequisito no obvio (roles, horario operativo, etc.).

7. **Pruebas**  
   Añadir o actualizar pruebas (servicios y/o vistas) según las convenciones del repositorio; la documentación no sustituye tests.

### Archivos de referencia (API)

| Archivo | Rol |
|---------|-----|
| `config/urls.py` | Montaje de rutas `api/v1/*` y URLs de Swagger/ReDoc/schema |
| `config/settings/base.py` | `REST_FRAMEWORK`, `SPECTACULAR_SETTINGS`, JWT |
| `shared/openapi.py` | Metadatos OpenAPI, tags, seguridad Bearer, textos globales |
| `shared/pagination.py` | Paginación por defecto |
| `shared/exceptions.py` | Forma de errores y excepciones de dominio |

La lista exhaustiva de operaciones, parámetros y esquemas JSON está en **`/api/docs/`** y en **`/api/schema/`**; el README no duplica ese contrato para no desincronizarse.

## Trabajo en equipo y buenas prácticas

- `.env` no se versiona (está ignorado en `.gitignore`).
- `.env.example` sí se versiona y define el contrato compartido de variables.
- Si se agrega una nueva variable en settings, también debe agregarse en `.env.example` y documentarse.
- No guardar secretos reales en el repositorio.
- Cualquier cambio en la API debe cumplir lo definido en [README_API.md](README_API.md).

## Estado actual

- Estructura modular de apps y carpeta `shared`.
- Settings por entorno (`base`, `development`, `production`, `test`).
- Configuración por variables de entorno.
- API bajo `/api/v1/` con documentación **OpenAPI 3** y **Swagger UI**; el contrato detallado vive en [README_API.md](README_API.md).
- Setup de Docker y dependencias; tests automatizados con pytest.
