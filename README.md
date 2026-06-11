# Sistema Inventario ICM — Backend

> **🚀 ¿Eres nuevo en el proyecto?** Empieza por aquí: **[Guía de Onboarding](docs/GUIA_ONBOARDING.md)** para levantar el entorno y conocer los comandos principales.

> **⚙️ Operación CI/CD:** guía completa en **[README_CICD.md](docs/CI/README_CICD.md)**.

Backend del sistema de gestión de inventario y operaciones de Import Corporal Medical (ICM), construido con Django y Django REST Framework.

Este repositorio contiene la estructura del proyecto (arquitectura, configuración, dependencias y contenedorización), preparada para evolucionar la API de forma consistente y documentada.

## Contenido

- [Guía de Onboarding](docs/GUIA_ONBOARDING.md)
- [Guía CI/CD Operativa](docs/CI/README_CICD.md)
- [Propósito del proyecto](#proposito-del-proyecto)
- [Índice de documentación](#indice-de-documentacion)
- [Stack tecnológico](#stack-tecnologico)
- [Configuración por variables de entorno](#configuracion-por-variables-de-entorno)
- [Inicio rápido](#inicio-rapido)
- [API REST (OpenAPI y Swagger)](#api-rest-openapi-y-swagger)
- [Trabajo en equipo y buenas prácticas](#trabajo-en-equipo-y-buenas-practicas)
- [Estado actual](#estado-actual)

## Propósito del proyecto

El sistema busca mejorar la trazabilidad de inventario, la consistencia de stock por ubicación y la seguridad operativa en procesos de recepción, despacho, traslados y auditoría.

En esta fase, el objetivo principal es tener una base técnica completa:

- Estructura modular por dominios.
- Configuración centralizada por entorno.
- Dependencias y herramientas de desarrollo listas.
- API versionada con contrato OpenAPI explícito y documentación en Swagger UI.

## Índice de documentación

Documentación funcional y arquitectónica disponible en el repositorio:

- [GUIA_ONBOARDING.md](docs/GUIA_ONBOARDING.md): comandos rápidos y paso a paso para configurar tu entorno local y levantar el proyecto.
- [README_API.md](docs/api/README_API.md): especificación y checklist de la API (OpenAPI, endpoints, tags y estándares).
- [README_ARQUITECTURA.md](docs/README_ARQUITECTURA.md): arquitectura técnica consolidada (estructura, desacoplamiento, inventario, Docker, testing, SOLID y patrones).
- [README_RESTRICCIONES.md](docs/calidad_restricciones/README_RESTRICCIONES.md): catálogo consolidado de restricciones arquitectónicas, operativas, tecnológicas y de despliegue.
- [README_ATRIBUTOS_CALIDAD.md](docs/calidad_restricciones/README_ATRIBUTOS_CALIDAD.md): inventario de atributos de calidad, evidencia y recomendaciones.
- [INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md](docs/calidad_restricciones/INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md): informe defendible de completitud para KISS, DRY, YAGNI y atributos priorizados.
- [architecture_drivers.md](docs/architecture/architecture_drivers.md): drivers funcionales y arquitectónicos priorizados.
- [utility_tree.md](docs/architecture/utility_tree.md): Utility Tree del proyecto con escenarios e impacto.
- [architectural_constraints.md](docs/architecture/architectural_constraints.md): restricciones formales que condicionan el diseño.
- [adr_relationships.md](docs/architecture/adr_relationships.md): trazabilidad drivers → problema → decisión → ADR.
- [ERS_ICM_Requisitos.md](docs/requisitos/ERS_ICM_Requisitos.md): requisitos funcionales, no funcionales y reglas de negocio.
- [ICM_Informe_Elicitacion_v2_plus.docx.md](docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md): contexto de levantamiento y análisis del dominio.
- [AGENTS.md](AGENTS.md): instrucciones y reglas para asistentes de código del proyecto.
- [README_ADR.md](docs/adr/README_ADR.md): índice y trazabilidad de decisiones arquitectónicas.
- [README_TEST.md](docs/test/README_TEST.md): estrategia de testing, tipos de pruebas, convenciones y ejemplos de escenarios Gherkin automatizados.
- [README_CICD.md](docs/CI/README_CICD.md): runbook operativo de CI/CD (gates, deploy, promoción, backup, rollback, seguridad y secretos).
- **[REFERENCIA_ENDPOINTS.md](docs/api/REFERENCIA_ENDPOINTS.md)**: referencia completa de endpoints con ejemplos request/response para el equipo de frontend.
- [README_MATRIZ_PERMISOS.md](docs/api/README_MATRIZ_PERMISOS.md): matriz de permisos por rol para todos los endpoints.
- **[ENV_GUIDE.md](docs/guias/ENV_GUIDE.md)**: guía de variables de entorno — desarrollo, email (Mailtrap), producción y token de recuperación.

## Stack tecnológico

- Python 3.11+
- Django 4.2+ (rango declarado en `requirements/base.txt`)
- Django REST Framework
- PostgreSQL 15
- JWT con djangorestframework-simplejwt (rotación + blacklist)
- OpenAPI 3 con **drf-spectacular** (Swagger UI y ReDoc)
- pytest + pytest-django (736+ tests — suite completa con recuperación de contraseña)
- Docker + Docker Compose
- openpyxl (exportación XLSX)
- WeasyPrint (facturas PDF)

## Configuración por variables de entorno

### Principio clave

La configuración del sistema se maneja desde variables de entorno. Para desarrollo, el archivo local `.env` es la fuente operativa de configuración para cada equipo.

Flujo recomendado:

1. Copiar `.env.example` como `.env`.
2. Ajustar los valores según el entorno local de cada persona.
3. No editar credenciales en archivos Python de settings.

Esto permite que cada integrante use credenciales distintas (usuario, contraseña, host, puertos) sin tocar código ni generar conflictos al bajar cambios.

### Variables mínimas importantes

Para una referencia completa de cada variable, entornos (Mailtrap, Gmail, producción) y ejemplos listos para copiar, ver la guía dedicada:

**[docs/guias/ENV_GUIDE.md](docs/guias/ENV_GUIDE.md)**

## Inicio rápido

Para iniciar el servidor de desarrollo y consultar la documentación localmente, asegúrate de tener el entorno virtual activado y las dependencias instaladas, luego ejecuta:

```bash
# 1. Aplicar migraciones si es necesario
python manage.py migrate

# 2. (Opcional) Cargar datos semilla
python manage.py create_almacenista
python scripts/seed_db/run.py

# 3. Iniciar el servidor
python manage.py runserver
```

Una vez que el servidor esté corriendo, puedes acceder a:
- **Swagger UI:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

## API REST (OpenAPI y Swagger)

La documentación completa de la API, sus estándares de codificación, contrato REST, autenticación JWT, reglas de versión y checklist de validación quedó separada en [README_API.md](docs/api/README_API.md).

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
- Cualquier cambio en la API debe cumplir lo definido en [README_API.md](docs/api/README_API.md).

### Gestión de issues y cambios

Para mantener el historial limpio y fácil de revisar, el trabajo debe organizarse así:

1. **Issue**: se usa para describir un problema, mejora o tarea pendiente. Debe ser específico y tener un alcance claro.
2. **Rama de trabajo**: cada issue relevante se implementa en una rama dedicada cuando el cambio merece seguimiento propio. La rama debe ser corta, clara y relacionada con el objetivo del issue.
3. **Commits**: cada commit debe representar un paso lógico del cambio. Usar Conventional Commits en inglés, con alcance explícito, por ejemplo `fix(test-docs): reorganize test documentation indexes`.
4. **Pull Request**: el PR debe enlazar el issue correspondiente. Si el cambio resuelve el issue, usar la referencia automática en la descripción o el cierre explícito de GitHub para que quede trazado.
5. **Documentación**: si el issue afecta comportamiento, contrato, arquitectura o pruebas, debe quedar reflejado en la documentación del repo. El lugar correcto depende del tema:
   - Cambios de arquitectura: [docs/README_ARQUITECTURA.md](docs/README_ARQUITECTURA.md)
   - Cambios de API: [docs/api/README_API.md](docs/api/README_API.md)
   - Cambios de pruebas: [docs/test/README_TEST.md](docs/test/README_TEST.md)
   - Decisiones técnicas importantes: [docs/adr/README_ADR.md](docs/adr/README_ADR.md)

### Qué sí documentar

- Bugs que afecten funcionalidad, validación o contratos de API.
- Decisiones que cambien comportamiento del negocio o la arquitectura.
- Cambios que requieran trazabilidad entre issue, PR, tests y documentación.
- Reglas nuevas o ajustadas que otro integrante deba entender sin revisar el código completo.

### Qué no documentar de forma extensa

- Tareas muy pequeñas o transitorias que ya quedan cubiertas por el PR.
- Ajustes puramente internos sin impacto visible en el comportamiento o en el contrato técnico.
- Conversaciones informales que no cambian el estado funcional del proyecto.

## Estado actual

- Estructura modular de apps y carpeta `shared`.
- Settings por entorno (`base`, `development`, `production`, `test`).
- Configuración por variables de entorno — guía completa en [ENV_GUIDE.md](docs/guias/ENV_GUIDE.md).
- API bajo `/api/v1/` con documentación **OpenAPI 3** y **Swagger UI**; el contrato detallado vive en [README_API.md](docs/api/README_API.md).
- Autenticación JWT con cambio y recuperación de contraseña por email (Mailtrap Sandbox en dev).
- Setup de Docker y dependencias; 736+ tests automatizados con pytest.
