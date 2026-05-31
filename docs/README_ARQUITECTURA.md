# README de Arquitectura - Sistema Inventario ICM (Backend)

Este documento describe la arquitectura tecnica del backend, con foco en decisiones de diseno, desacoplamiento, reglas de consistencia de inventario, calidad de codigo y criterios operativos (Docker, testing, seguridad y rendimiento).

Para operacion CI/CD (gates, despliegue, promociones, backups y rollback), consultar tambien:

- [docs/CI/README_CICD.md](CI/README_CICD.md)

## 1. Objetivo Arquitectonico

Construir un backend mantenible y trazable para inventario y operaciones logisticas, donde:

- El historial de movimientos sea inmutable y auditable.
- El stock por ubicacion sea consistente y reconstruible.
- La logica de negocio viva fuera de views y serializers.
- El sistema pueda evolucionar sin romper modulos existentes.

## 2. Estilo de Arquitectura

### 2.1 Monolito modular por dominio

El proyecto usa un monolito modular con apps Django por dominio:

- authentication
- catalog
- inventory
- movements
- dashboard
- reports
- alerts
- audit

Beneficios:

- Cohesion alta por dominio.
- Bajo acoplamiento entre modulos.
- Facilidad para pruebas unitarias e integracion.
- Escalamiento evolutivo sin migrar a microservicios prematuramente.

### 2.2 Separacion de responsabilidades por capa

En cada app se mantiene esta estructura:

- **models.py**: entidades y constraints de datos. Sin lógica de negocio.
- **serializers.py**: validacion y transformacion de entrada/salida. Sin lógica de negocio.
- **views.py**: adaptador HTTP (sin reglas de negocio). Solo orquesta recepción, delegación y respuesta.
- **services.py**: TODA la lógica de negocio. Aquí viven las reglas de dominio (BR-XX), validaciones, transacciones.
- **selectors.py**: consultas de lectura complejas sin efectos secundarios. Patrón de Query Object.
- **permissions.py**: reglas de acceso de DRF. Control de autorización por rol.

**Principio CRÍTICO**: La lógica de negocio NUNCA debe estar en models, serializers, o views. Eso es responsabilidad de services.py.

### 2.3 Integracion frontend-backend via API REST

La comunicacion entre frontend y backend se realizara exclusivamente por API REST (HTTP/JSON), bajo versionado `/api/v1/`.

Reglas de integracion:

- El frontend no accede a base de datos ni a logica interna del backend.
- Toda operacion de negocio se ejecuta por endpoints DRF.
- La autenticacion se maneja con JWT (access/refresh).
- La autorizacion se aplica por RBAC en cada endpoint.
- Los contratos de entrada/salida se documentan en OpenAPI/Swagger.

Contrato tecnico base de comunicacion:

- Base path: `/api/v1/`
- Formato: `application/json`
- Seguridad: `Authorization: Bearer <token>`
- Errores: estructura uniforme con `error`, `message` y `detail`
- Versionado: cambios incompatibles requieren `/api/v2/`

Dominios de API esperados:

- `/api/v1/auth/` autenticacion y gestion de usuarios
- `/api/v1/catalog/` productos, categorias, subcategorias y resolucion de identificadores
- `/api/v1/inventory/` stock por ubicacion y busqueda
- `/api/v1/movements/` entradas, salidas, traslados, devoluciones y ajustes
- `/api/v1/dashboard/` read model operacional orientado a UI ejecutiva
- `/api/v1/reports/` indicadores y reportes de solo lectura
- `/api/v1/alerts/` alertas operativas activas
- `/api/v1/audit/` trazabilidad historica (solo lectura autorizada)

Objetivo de esta decision:

- Mantener desacoplamiento frontend-backend.
- Permitir evolucion independiente de ambas capas.
- Facilitar pruebas de integracion y automatizacion de contratos.

## 3. Estructura del Proyecto

Estructura de Directorios del Proyecto:


```text
icm_backend/
├── apps/                                                       # Dominios Django del backend
│   ├── authentication/                                         # Autenticación JWT, RBAC y control de acceso
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_models.py                                  # Cobertura crítica del módulo
│   │   │   ├── test_services.py                                # Política de acceso y restricciones de rol
│   │   │   └── test_views.py                                   # Cobertura crítica del módulo
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Autenticación JWT, RBAC y verificación de identidad
│   │   ├── selectors.py                                        # Consultas de lectura sin efectos secundarios
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   ├── exceptions.py                                       # Excepciones de dominio y validación
│   │   ├── signals.py                                          # Sincronización de eventos de identidad
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   ├── catalog/                                                # Catálogo, SKUs definidos por usuario y validación de productos
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_models.py                                  # Cobertura crítica del módulo
│   │   │   ├── test_services.py                                # Cobertura crítica del módulo
│   │   │   └── test_views.py                                   # Cobertura crítica del módulo
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Catálogo, SKU definido por usuario y validación de producto
│   │   ├── selectors.py                                        # Consultas de lectura y agregaciones del módulo
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   ├── exceptions.py                                       # Excepciones de dominio y validación
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   ├── inventory/                                              # Consulta de stock en tiempo real
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_admin.py                                   # Reglas de negocio y transacciones del dominio
│   │   │   ├── test_models.py                                  # Reglas de negocio y transacciones del dominio
│   │   │   ├── test_selectors.py                               # Reglas de negocio y transacciones del dominio
│   │   │   ├── test_services.py                                # Cobertura crítica del módulo
│   │   │   └── test_views.py                                   # Cobertura crítica del módulo
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Reglas de negocio del ledger y actualización transaccional del stock
│   │   ├── selectors.py                                        # Lecturas de stock por ubicación
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   ├── exceptions.py                                       # Excepciones de dominio y validación
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   ├── movements/                                              # Ledger inmutable y consistencia de inventario
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_models.py                                  # Cobertura crítica del módulo
│   │   │   ├── test_services.py                                # Reglas de negocio y transacciones del dominio
│   │   │   └── test_views.py                                   # Cobertura crítica del módulo
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Ledger inmutable, atomicidad y actualización del stock derivado
│   │   ├── selectors.py                                        # Lecturas del ledger y del stock derivado
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   ├── exceptions.py                                       # Errores de inventario y consistencia
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   ├── reports/                                                # Reportes e indicadores operativos
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_models.py                                  # Cobertura crítica del módulo
│   │   │   ├── test_selectors.py                               # Reglas de negocio y transacciones del dominio
│   │   │   ├── test_services.py                                # Cobertura crítica del módulo
│   │   │   └── test_views.py                                   # Reglas de negocio y transacciones del dominio
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Reglas de negocio y transacciones del dominio
│   │   ├── selectors.py                                        # Consultas agregadas para reportes y KPIs
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   ├── alerts/                                                 # Alertas operativas y monitoreo preventivo
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_models.py                                  # Cobertura crítica del módulo
│   │   │   ├── test_services.py                                # Cobertura crítica del módulo
│   │   │   └── test_views.py                                   # Cobertura crítica del módulo
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Generación de alertas operativas
│   │   ├── selectors.py                                        # Consultas de lectura y agregaciones del módulo
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   ├── audit/                                                  # Trazabilidad e histórico de eventos
│   │   ├── tests/                                              # Pruebas del subdominio
│   │   │   ├── test_models.py                                  # Cobertura crítica del módulo
│   │   │   ├── test_services.py                                # Reglas de negocio y transacciones del dominio
│   │   │   └── test_views.py                                   # Cobertura crítica del módulo
│   │   ├── models.py                                           # Entidades y constraints de persistencia
│   │   ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│   │   ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│   │   ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│   │   ├── services.py                                         # Trazabilidad e inmutabilidad de eventos
│   │   ├── selectors.py                                        # Consultas de auditoría
│   │   ├── permissions.py                                      # Política de acceso y restricciones de rol
│   │   └── admin.py                                            # Registro administrativo y soporte operacional
│   └── dashboard/                                              # Aplicación Django detectada automáticamente
│       ├── tests/                                              # Pruebas del subdominio
│       │   └── test_views.py                                   # Reglas de negocio y transacciones del dominio
│       ├── serializers.py                                      # Validación y adaptación del contrato de entrada/salida
│       ├── views.py                                            # Endpoints HTTP del módulo y orquestación de requests
│       ├── urls.py                                             # Ruteo HTTP y composición de endpoints
│       └── services.py                                         # Reglas de negocio y transacciones del dominio
├── config/                                                     # Configuración central del proyecto Django
│   ├── settings/                                               # Configuración compartida y sobreescrituras por entorno
│   │   ├── base.py                                             # Configuración base compartida
│   │   ├── development.py                                      # Sobreescrituras para desarrollo local
│   │   ├── production.py                                       # Sobreescrituras para producción
│   │   └── test.py                                             # Configuración aislada para la suite de pruebas
│   ├── urls.py                                                 # Composición de rutas y puntos de entrada HTTP
│   ├── wsgi.py                                                 # Punto de entrada WSGI
│   └── asgi.py                                                 # Punto de entrada ASGI
├── docker/                                                     # Infraestructura de contenedores y arranque
│   ├── Dockerfile                                              # Imagen base del contenedor de despliegue
│   └── entrypoint.sh                                           # Inicialización del contenedor y arranque
├── docs/                                                       # Documentación técnica viva del proyecto
│   ├── README_ARQUITECTURA.md                                  # Documento vivo de arquitectura
│   ├── api/                                                    # Contratos OpenAPI, seguridad y permisos
│   │   ├── README_API.md                                       # Documento técnico relevante
│   │   └── README_MATRIZ_PERMISOS.md                           # Documento técnico relevante
│   ├── requisitos/                                             # Requisitos funcionales y contexto de negocio
│   │   ├── ERS_ICM_Requisitos.md                               # Documento técnico relevante
│   │   └── ICM_Informe_Elicitacion_v2_plus.docx.md             # Documento técnico relevante
│   ├── test/                                                   # Trazabilidad y documentación de pruebas
│   │   ├── README_TEST.md                                      # Documento técnico relevante
│   │   ├── TRAZABILIDAD_ERS_GHERKIN.md                         # Documento técnico relevante
│   │   ├── gherkin_scenarios.json                              # Documento técnico relevante
│   │   ├── gherkin_out_of_scope.json                           # Documento técnico relevante
│   │   ├── all_unit.md                                         # Documento técnico relevante
│   │   ├── all_integration.md                                  # Documento técnico relevante
│   │   ├── all_scenarios.md                                    # Documento técnico relevante
│   │   ├── unit/
│   │   │   └── index.md                                        # Documento técnico relevante
│   │   ├── integration/                                        # Pruebas HTTP/API de integración
│   │   │   └── index.md                                        # Documento técnico relevante
│   │   └── scenarios/
│   │       └── index.md                                        # Documento técnico relevante
│   ├── calidad_restricciones/                                  # Atributos de calidad y restricciones
│   │   ├── README_ATRIBUTOS_CALIDAD.md                         # Documento técnico relevante
│   │   └── README_RESTRICCIONES.md                             # Documento técnico relevante
│   ├── architecture/                                           # Síntesis arquitectónica: drivers, Utility Tree y ADRs
│   │   ├── architecture_drivers.md                             # Drivers arquitectónicos priorizados
│   │   ├── utility_tree.md                                     # Utility Tree con escenarios y trade-offs
│   │   ├── architectural_constraints.md                        # Restricciones arquitectónicas y riesgos
│   │   └── adr_relationships.md                                # Trazabilidad entre drivers y ADRs
│   ├── CI/                                                     # Documento arquitectónico relevante
│   │   └── README_CICD.md                                      # Documento técnico relevante
│   ├── evidence/                                               # Documento arquitectónico relevante
│   │   └── README.md                                           # Documento técnico relevante
│   └── GUIA_ONBOARDING.md                                      # Documento técnico relevante
├── requirements/                                               # Dependencias por entorno
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── scripts/                                                    # Automatizaciones reutilizables del repositorio
│   ├── README_SCRIPTS.md                                       # Índice y contexto de las automatizaciones
│   ├── project_structure/                                      # Generador semántico de la estructura arquitectónica
│   │   └── generate_project_structure.py                       # Generador semántico de la estructura arquitectónica
│   ├── parse_ers_gherkin.py                                    # Generador de escenarios ERS/Gherkin
│   ├── generate_docs/                                          # Generadores compartidos de documentación
│   │   ├── __main__.py                                         # Entry point oficial: python -m scripts.generate_docs
│   │   └── utils.py                                            # Pipeline compartido: descubrimiento, renderizado y escritura
│   └── perf/
│       └── locustfile.py
├── shared/                                                     # Código transversal reutilizable
│   ├── models.py                                               # BaseModel y metadatos comunes
│   ├── permissions.py                                          # Permisos base y reutilizables
│   ├── exceptions.py                                           # Excepciones tipadas del sistema
│   ├── mixins.py                                               # Mixins transversales para vistas
│   ├── pagination.py                                           # Paginación reutilizable
│   ├── openapi.py                                              # Tags OpenAPI y contratos compartidos
│   └── utils/                                                  # Utilidades transversales
│       └── validators.py                                       # Validadores reutilizables
├── tests/                                                      # Tests de integración cross-módulo
│   ├── factories.py                                            # Factories de datos de prueba
│   ├── ers/                                                    # Suite Gherkin dinámica alineada al ERS
│   │   ├── gherkin_impl.py                                     # Escenarios Gherkin y trazabilidad al ERS
│   │   └── test_gherkin_dynamic.py                             # Escenarios Gherkin y trazabilidad al ERS
│   ├── integration/                                            # Pruebas HTTP/API de integración
│   │   ├── test_api_integration.py                             # Pruebas de integración HTTP/API
│   │   ├── test_movements_integration.py                       # Pruebas de integración HTTP/API
│   │   └── test_smoke_endpoints.py                             # Pruebas de integración HTTP/API
│   └── concurrency/
│       └── test_concurrent_movements.py                        # Cobertura crítica del módulo
├── docker-compose.prod.yml                                     # Orquestación de producción
├── docker-compose.yml                                          # Orquestación local del stack
├── manage.py                                                   # Punto de entrada de comandos Django
├── pytest.ini                                                  # Configuración de pytest
├── README.md                                                   # Resumen general del repositorio
└── schema.yml                                                  # Esquema OpenAPI consolidado
```

Principio clave: shared contiene componentes transversales reutilizables, no logica de dominio especifica.

---

## 3.1 Reglas de Negocio (BR-XX) — Guía Completa de Implementación

Las siguientes reglas de negocio son **mandatorias** y deben implementarse en `services.py` de cada módulo responsable. No son negociables ni pueden ser simplificadas.

### 3.1.1 Autenticación, Autorización e Identidad

#### BR-01: Identidad Única y Trazabilidad en Todas las Operaciones

**Descripción**: Cada operación en el sistema debe estar asociada a un usuario autenticado identificable de forma única. No se permite ejecución anónima de operaciones de negocio.

**Implementación**:
- Modelo `authentication.User` extiende `AbstractUser` de Django con campo `role`.
- Cada `Movement` incluye campo `executed_by = ForeignKey(User)` inmutable.
- Cada `AuditLog` incluye campo `user` para trazabilidad de quién ejecutó la acción.
- Middleware de autenticación rechaza requests sin JWT válido para endpoints protegidos.

**Verificación en tests**:
```python
# Debe fallar: intento de movimiento sin usuario autenticado
POST /api/v1/movements/entry/ sin Authorization header → 401 Unauthorized

# Debe pasar: movimiento auditado correctamente
movement = register_entry(user=admin, ...)
assert movement.executed_by == admin
assert movement in AuditLog con user=admin
```

**Referencia**: RF-001, RF-002, RF-012

---

#### BR-02: Gestión de Credenciales Solo por Almacenista

**Descripción**: Solo los usuarios con rol `almacenista` pueden crear, modificar o deshabilitar cuentas de usuario. Los roles `auxiliar_despacho` y `administrador` no tienen permisos de gestión de identidades.

**Implementación**:
- `authentication.services.create_user(executor_user, user_data)` valida `executor_user.role == 'almacenista'`.
- Si no: lanza `UnauthorizedCredentialManagementError`.
- `authentication.permissions.IsAlmacenista` aplicado a endpoints POST/PATCH/DELETE en `/api/v1/auth/users/`.
- Cada intento de gestión de credenciales se registra en `AuditLog` (éxito o rechazo).

**Verificación en tests**:
```python
# Debe fallar: auxiliar intenta crear usuario
POST /api/v1/auth/users/ con token de auxiliar → 403 Forbidden

# Debe pasar: almacenista crea usuario
POST /api/v1/auth/users/ con token de almacenista + datos → 201 Created
```

**Referencia**: RF-001, RF-002

---

#### BR-03: Restricción Horaria para Auxiliar de Despacho

**Descripción**: Los usuarios con rol `auxiliar_despacho` solo pueden autenticarse e iniciar sesiones dentro de dos franjas horarias:
- **Mañana**: 07:00 a 12:00
- **Tarde**: 14:00 a 17:00

Fuera de estas franjas, cualquier intento de login falla. Además, si una sesión se abre en horario válido pero luego el sistema pasa a horario no válido, las solicitudes posteriores son rechazadas.

**Implementación**:
- `authentication.services.authenticate_user(username, password, request_time)` valida la franja horaria.
- Si rol es `auxiliar_despacho` y `request_time` NO está en las franjas permitidas: lanza `OutsideOperatingHoursError`.
- Permiso DRF `shared.permissions.IsWithinOperatingHours` se aplica a **todos** los endpoints que use el auxiliar, no solo el login.
- La validación se hace con `timezone.now()` en `America/Bogota`.

**Verificación en tests**:
```python
# Debe fallar: login a las 13:00 (franja muerta)
POST /api/v1/auth/login/ auxiliar a 13:00 → 403 Forbidden: OutsideOperatingHoursError

# Debe fallar: request con token válido, pero servidor ahora está fuera de horario
GET /api/v1/movements/ auxiliar a 18:00 → 403 Forbidden: OutsideOperatingHoursError

# Debe pasar: login a 08:30 (dentro de franja)
POST /api/v1/auth/login/ auxiliar a 08:30 → 200 OK con tokens

# Debe pasar: request dentro de franja
GET /api/v1/movements/ auxiliar a 10:00 → 200 OK
```

**Referencia**: RF-001, RF-002

---

### 3.1.2 Gestión de Catálogo y Productos

#### BR-04: Requisito de Número de Serie en Productos de Electroterapia

**Descripción**: Los productos pertenecientes a la categoría **Electroterapia** tienen **riesgo de seguridad eléctrica** y **deben** incluir número de serie en cada entrada y salida. Si un producto de Electroterapia se recibe, traslada o despacha sin número de serie, la operación es rechazada.

**Implementación**:
- Modelo `catalog.Category` con campo `requires_serial_number = BooleanField(default=False)`.
- Para categoría Electroterapia: `requires_serial_number = True`.
- `movements.services.register_entry()`: si `product.category.requires_serial_number == True` y `serial_number is None`, lanza `SerialNumberRequiredError`.
- `movements.services.register_dispatch()`: idem validación.
- El campo `serial_number` en `Movement` es obligatorio en estos casos.

**Verificación en tests**:
```python
# Debe fallar: entrada de electroterapia sin serial
register_entry(product=electroterapia_product, serial_number=None) → SerialNumberRequiredError

# Debe pasar: entrada de electroterapia con serial
register_entry(product=electroterapia_product, serial_number="SN12345") → Movement created

# Debe fallar: entrada de manoterapia sin serial (no requerida)
# (No la rechaza porque no lo requiere)
register_entry(product=manoterapia_product, serial_number=None) → Movement created
```

**Referencia**: RF-005, RF-006, RF-011

---

#### BR-12: Formato de SKU definido por el usuario

**Descripción**: El SKU lo define el usuario y debe seguir el patrón 1–4 letras, un guion y 1–4 dígitos (por ejemplo `PRD-0001`, `A-1` o `ELEC-123`). No se exige un prefijo obligatorio para la marca propia.

**Implementación**:
- Validación en `shared.utils.validators.validate_sku_format` y aplicable desde `catalog.models.Product` y `catalog.services.create_product()`.
- Si el SKU no cumple el patrón definido: lanza `InvalidSKUFormatError` o `ValueError` según el contexto.

**Verificación en tests**:
```python
# Debe fallar: SKU con formato inválido (sin guion)
create_product(sku="ELECTRO001", brand="Can") → InvalidSKUFormatError

# Debe pasar: SKU con formato válido
create_product(sku="ELEC-0001", brand="Can") → Product created

# Debe pasar: producto de otra marca con formato válido
create_product(sku="OTR-1", brand="OtraMarca") → Product created
```

**Referencia**: RF-003

---

### 3.1.3 Gestión de Inventario (Ledger de Movimientos)

#### BR-05: Devoluciones Solo Permitidas para Categorías Específicas

**Descripción**: Las devoluciones de productos (`DEVOLUCION`) solo se permiten para categorías que lo justifiquen técnicamente:
- **Permitidas**: Electroterapia, Electrónicos.
- **NO permitidas**: Mesas de Fisioterapia, Manoterapia (productos de difícil devolución).

**Implementación**:
- Modelo `catalog.Category` con campo `is_returnable = BooleanField(default=False)`.
- Electroterapia: `is_returnable = True`.
- `movements.services.register_return(user, product_id, ...)`: valida `product.category.is_returnable == True`. Si no, lanza `ProductNotReturnableError`.

**Verificación en tests**:
```python
# Debe fallar: devolución de mesa de fisioterapia
register_return(product=mesa_product) → ProductNotReturnableError

# Debe pasar: devolución de electroterapia
register_return(product=electro_product, serial_number="SN123") → Movement de devolución creado
```

**Referencia**: RF-008

---

#### BR-06: Ventana de Autocorrección (5 minutos)

**Descripción**: Los usuarios (`almacenista` y `auxiliar_despacho`) pueden corregir movimientos propios dentro de una **ventana de 5 minutos** desde su creación. Pasado ese tiempo, solo un nuevo `AJUSTE` puede corregir un error.

**Implementación**:
- `movements.models.Movement` con campo `created_at` registrado al crear.
- `movements.services.correct_movement_within_window(user, movement_id, corrected_data)` valida:
  - `now() - movement.created_at <= timedelta(minutes=5)`.
  - `movement.executed_by == user` (el que lo creó).
  - Si no cumple: lanza `CorrectionWindowClosedError`.
- Si cumple: crea una nueva `Movement` de corrección vinculada al original.

**Verificación en tests**:
```python
# Debe pasar: corrección a los 3 minutos
movement = register_entry(...)  # created_at = 10:00:00
# Tiempo actual: 10:03:00
correct_movement_within_window(user=same_user, movement_id=movement.id) → Corrección aplicada

# Debe fallar: corrección a los 6 minutos
movement = register_entry(...)  # created_at = 10:00:00
# Tiempo actual: 10:06:00
correct_movement_within_window(user=same_user, movement_id=movement.id) → CorrectionWindowClosedError

# Debe fallar: corrección por usuario diferente
movement = register_entry(user=user_a, ...)
correct_movement_within_window(user=user_b, movement_id=movement.id) → CorrectionWindowClosedError
```

**Referencia**: RF-009

---

#### BR-07: Ajuste de Inventario Requiere Justificación Obligatoria

**Descripción**: Los ajustes de inventario (para corregir discrepancias de stock o daños) **deben** incluir una justificación escrita. Un ajuste sin justificación es rechazado. Solo el rol `almacenista` puede crear ajustes.

**Implementación**:
- `movements.models.Movement` con campo `justification = TextField(blank=False, null=False)` cuando `movement_type == 'AJUSTE'`.
- `movements.services.register_adjustment(almacenista_user, product_id, location_id, new_quantity, justification)`:
  - Valida `almacenista_user.role == 'almacenista'`.
  - Valida `justification is not None and len(justification.strip()) > 0`.
  - Si no cumple: lanza `AdjustmentJustificationRequiredError` o `UnauthorizedError`.

**Verificación en tests**:
```python
# Debe fallar: ajuste sin justificación
register_adjustment(almacenista, product_id=123, location_id=1, new_quantity=50, justification="") 
→ AdjustmentJustificationRequiredError

# Debe fallar: ajuste por auxiliar
register_adjustment(auxiliar, product_id=123, ..., justification="Corección por daño") 
→ UnauthorizedError

# Debe pasar: ajuste con justificación por almacenista
register_adjustment(almacenista, product_id=123, location_id=1, new_quantity=50, 
                     justification="Corrección por faltante encontrado en conteo")
→ Movement de ajuste creado con justificación
```

**Referencia**: RF-009

---

#### BR-08: Validación Cruzada en Despacho (Scanning vs. SKU de Orden)

**Descripción**: Este es el **mecanismo crítico de prevención de errores** en el despacho. Cuando un `auxiliar_despacho` despacha un producto, debe **escanear físicamente el código de barras del producto real**. El sistema compara:
- `scanned_code` (código del producto físico escaneado).
- `order_sku` (SKU esperado de la orden).

Si **no coinciden**, el despacho es **rechazado** con excepción `CrossValidationFailedError`. Esto previene el error crítico de enviar un producto morfológicamente similar pero incorrecto.

**Implementación**:
- `movements.services.register_dispatch(user, product_id, location_id, quantity, movement_type, scanned_code, order_sku, ...)`.
- Lógica de `register_dispatch`:
  1. Obtener producto con `product_id`.
  2. Resolver el producto del `scanned_code` usando `catalog.services.resolve_identifier(scanned_code)`.
  3. Si el producto escaneado no coincide con `order_sku`: lanza `CrossValidationFailedError`.
  4. Si pasa validación cruzada: procede con despacho.
- El despacho se registra con ambos valores en `Movement` para auditoría.

**Verificación en tests**:
```python
# Escenario: auxiliar intenta despachar producto erróneo
order_sku = "ELEC-0001"  # esperado
scanned_code = "ELEC-0002"  # escaneado (producto similar)

register_dispatch(user=auxiliar, product_id=..., location_id=1, quantity=10,
                  movement_type='SALIDA_VENTA_MAYOR', scanned_code=scanned_code, 
                  order_sku=order_sku)
→ CrossValidationFailedError: Producto escaneado (ELEC-0002) no coincide con SKU de orden (ELEC-0001)

# Escenario correcto
order_sku = "ELEC-0001"
scanned_code = "ELEC-0001"

register_dispatch(user=auxiliar, product_id=..., location_id=1, quantity=10,
                  movement_type='SALIDA_VENTA_MAYOR', scanned_code=scanned_code, 
                  order_sku=order_sku)
→ Movement de despacho creado exitosamente
```

**Referencia**: RF-006 (Scenario 3)

---

#### BR-09: Nota de Discrepancia Requerida en Recepción

**Descripción**: Cuando un producto se recibe en cantidad diferente a la facturada, **debe anotarse una nota de discrepancia**. Si `quantity_received != quantity_invoiced`, la operación exige una justificación.

**Implementación**:
- `movements.models.Movement` con campos `quantity_invoiced` y `discrepancy_note`.
- `movements.services.register_entry(user, product_id, location_id, quantity, qty_invoiced=None, discrepancy_note=None)`:
  - Si `quantity != qty_invoiced` y `discrepancy_note is None or empty`: lanza `DiscrepancyNoteRequiredError`.
  - Si son iguales: `discrepancy_note` es opcional.
  
**Verificación en tests**:
```python
# Debe fallar: recepción con discrepancia sin nota
register_entry(product_id=123, quantity=48, qty_invoiced=50, discrepancy_note="")
→ DiscrepancyNoteRequiredError

# Debe pasar: recepción con discrepancia y nota
register_entry(product_id=123, quantity=48, qty_invoiced=50, 
               discrepancy_note="2 unidades faltantes en caja 5")
→ Movement de entrada creado con nota

# Debe pasar: recepción correcta sin discrepancia
register_entry(product_id=123, quantity=50, qty_invoiced=50)
→ Movement de entrada creado (discrepancy_note vacío/null)
```

**Referencia**: RF-005 (Scenario 2)

---

#### BR-10: Inmutabilidad del Ledger de Movimientos y Auditoría

**Descripción**: Los registros de movimientos (`Movement`) y auditoría (`AuditLog`) **son inmutables**. Una vez creados, no se pueden actualizar ni eliminar. Los errores se corrigen con **nuevos movimientos de ajuste**, nunca modificando el historial.

**Implementación**:
- `movements.models.Movement`: NO existen endpoints PUT/PATCH/DELETE.
- `audit.models.AuditLog`: NO existen endpoints PUT/PATCH/DELETE.
- Constraint en BD: `unique_together` y `created_at` sin `updated_at`.
- ViewSet de `movements.views.MovementViewSet` solo expone `create()` y `list()/retrieve()` (métodos seguros).
- Guardas en `permissions.py` rechazan requests de actualización.
- Si se intenta PUTPatch/DELETE: lanza `ImmutableRecordError`.

**Verificación en tests**:
```python
# Debe fallar: intento de actualizar movimiento
movement = Movement.objects.create(...)
PATCH /api/v1/movements/{id}/ → 405 Method Not Allowed o 403 Forbidden: ImmutableRecordError

# Debe fallar: intento de eliminar movimiento
DELETE /api/v1/movements/{id}/ → 405 Method Not Allowed o 403 Forbidden

# Debe pasar: crear nuevo movimiento de ajuste
register_adjustment(almacenista, justification="Corrección del movimiento anterior") 
→ Movement de ajuste creado (el anterior sigue intacto)
```

**Referencia**: RF-009, RF-012

---

#### BR-11: Stock por Ubicación y Ledger como Fuente de Verdad

**Descripción**: El inventario del sistema se gestiona mediante dos estructuras:
1. **Ledger** (`Movement`): registro inmutable de cada cambio (FUENTE DE VERDAD).
2. **Stock derivado** (`StockByLocation`): caché del stock actual por producto y ubicación.

El stock derivado debe estar siempre sincronizado con el ledger. Si hay desincronización, el stock derivado debe poder reconstruirse sumando todos los movimientos del ledger desde cero.

**Reglas obligatorias**:
- Nunca modificar `StockByLocation` sin crear un `Movement` en la misma transacción.
- No se permiten stocks negativos (constraint de BD: `current_stock >= 0`).
- Cada `Movement` registra snapshots: `stock_previo` y `stock_resultante` para trazabilidad.
- Para traslados internos: el stock global no cambia (sale de una ubicación, entra en otra).
- La función de reconstrucción `reconstruct_stock_from_ledger(product_id, location_id)` suma movimientos y debe coincidir con `StockByLocation.current_stock`.

**Implementación**:
- `movements.services.register_entry/dispatch/transfer/...` ejecutado dentro de `@transaction.atomic`.
- Paso 1: calcular stock previo de origen.
- Paso 2: validar que cantidad <= stock disponible (para salidas).
- Paso 3: crear `Movement` con snapshots.
- Paso 4: actualizar `StockByLocation` con el nuevo stock.
- Si algo falla: ROLLBACK automático (sin stock parcialmente actualizado).
- `inventory.selectors.reconstruct_stock_from_ledger()` ejecuta verificación bajo demanda.

**Verificación en tests**:
```python
# Test 1: Consistencia después de una entrada
initial_stock = 100
register_entry(product_id=1, location_id=1, quantity=20)
stock_by_location = StockByLocation.objects.get(product_id=1, location_id=1)
assert stock_by_location.current_stock == 120

# Test 2: Reconstrucción desde ledger
reconstructed = reconstruct_stock_from_ledger(product_id=1, location_id=1)
assert reconstructed == stock_by_location.current_stock

# Test 3: Traslado no altera stock global
total_before = sum(s.current_stock for s in StockByLocation.filter(product_id=1))
register_internal_transfer(product_id=1, origin_id=1, destination_id=2, quantity=10)
total_after = sum(s.current_stock for s in StockByLocation.filter(product_id=1))
assert total_before == total_after

# Test 4: Stock negativo rechazado
register_dispatch(product_id=1, location_id=1, quantity=200)  # solo hay 100
→ InsufficientStockError
```

**Referencia**: RF-004, RF-005, RF-006, RF-007, RF-008, RF-009, RF-010

---

#### BR-13: Factura Digital y Numeración Secuencial

**Descripción**: Cada despacho genera automáticamente una factura digital en formato **PDF**. Las facturas se numeran secuencialmente con prefijo `ICM-` y se almacenan de forma inmutable. El PDF incluye:
- Número de factura.
- SKU y descripción de productos.
- Cantidad, precio unitario, total.
- Fecha/hora del despacho.
- Usuario responsable (almacenista firmante).
- QR con metadatos para auditoría.

**Implementación**:
- `movements.models.Movement` con campo `invoice_number = CharField(unique=True)`.
- `movements.services.register_dispatch()` llama a `movements.services.generate_invoice_pdf(movement)`.
- La numeración es secuencial: `ICM-0001`, `ICM-0002`, etc. (usando `Counter` atómico en BD).
- El PDF se genera con `WeasyPrint` o `ReportLab` a partir de template HTML.
- El archivo PDF se almacena en media storage sin permitir acceso de lectura no autorizado.

**Verificación en tests**:
```python
# Test 1: Numeración secuencial
m1 = register_dispatch(...)
m2 = register_dispatch(...)
assert m1.invoice_number == "ICM-0001"
assert m2.invoice_number == "ICM-0002"

# Test 2: PDF generado
movement = register_dispatch(...)
assert movement.invoice_pdf is not None
assert File(movement.invoice_pdf).exists()

# Test 3: PDF contiene información correcta
pdf_content = extract_pdf_text(movement.invoice_pdf)
assert "ICM-0001" in pdf_content
assert product.sku in pdf_content
```

**Referencia**: RF-006, RF-010

---

#### BR-14: Estado Operativo de Ubicación Restringe Movimientos

**Descripción**: El estado operativo de una ubicación (`OperationalStatus`) determina qué operaciones de stock puede ejecutar. Las ubicaciones en estado `archived` o `blocked` no admiten ningún movimiento. Las en estado `maintenance` o `restricted` no pueden operar como origen de despachos, traslados ni ajustes reductores, pero sí pueden recibir stock como destino. Solo el Almacenista puede cambiar el estado operativo.

**Matriz de elegibilidad**:

| Estado | Entrada (destino) | Despacho (origen) | Traslado destino | Devolución (destino) |
|--------|:-----------------:|:-----------------:|:----------------:|:--------------------:|
| active | ✅ | ✅ | ✅ | ✅ |
| maintenance | ✅ | ❌ | ✅ | ✅ |
| restricted | ✅ | ❌ | ✅ | ✅ |
| blocked | ❌ | ❌ | ❌ | ❌ |
| archived | ❌ | ❌ | ❌ | ❌ |

**Implementación**:
- `inventory.models.Location.OperationalStatus` — enum con los cinco estados.
- `movements.services._ensure_location_allows_origin` — gate para operaciones de salida.
- `movements.services._ensure_location_allows_destination` — gate para operaciones de entrada.
- `shared.exceptions.LocationStateNotAllowedError` — excepción de dominio (HTTP 422).

**Referencia**: RF-004, RF-005, RF-006, RF-007, RF-008, RF-009

---

#### BR-15: Tipo de Almacenamiento Activo como Requisito de Asignación

**Descripción**: Un `StorageType` con `is_active=False` no puede asignarse a nuevas ubicaciones ni reasignarse a las existentes. La desactivación es soft (el tipo permanece en BD para no romper FKs existentes). Solo el Almacenista puede crear, modificar o desactivar tipos de almacenamiento.

**Implementación**:
- `inventory.services.create_location` — valida `storage_type.is_active` antes de asignar.
- `inventory.services.update_location` — igual validación al cambiar `storage_type_id`.
- `shared.exceptions.DomainValidationError` — lanzada con mensaje descriptivo (HTTP 422).

**Referencia**: RF-004

---

### 3.1.4 Auditoría y Reportes

#### Reglas de Auditoría Derivadas de BR-10

**Descripción**: La app `audit` registra cada evento significativo del sistema. Estos registros son:
- Inmutables (solo lectura después de creación).
- Completos (incluyen quién, qué, cuándo, dónde).
- Consultables solo por usuarios autorizados.

**Eventos auditados mínimamente**:
1. Autenticación exitosa/fallida.
2. Creación/modificación/deshabilitación de usuario.
3. Creación de cada tipo de movimiento.
4. Ajustes de inventario.
5. Generación de reportes.
6. Cambios en permisos o roles.

**Referencia**: RF-012

---

## Tabla Resumida de Reglas de Negocio

| BR-ID | Nombre | Categoría | Implementación Principal | Validación Clave |
|-------|--------|-----------|--------------------------|------------------|
| BR-01 | Identidad Única | Auth | `User` + `executed_by` en Movement | Tests: verificar `executed_by` en todos los movimientos |
| BR-02 | Gestión Credenciales Solo Almacenista | Auth | Guardas en `authentication/services.py` + `IsAlmacenista` | Tests: rechazar auxiliar/admin en POST users |
| BR-03 | Restricción Horaria Auxiliar | Auth | `IsWithinOperatingHours` en cada request | Tests: login 13:00 rechazado, 08:00 aceptado |
| BR-04 | Serial Obligatorio Electroterapia | Catalog | `Category.requires_serial_number` + validación en `register_entry` | Tests: rechazo sin serial, aceptación con serial |
| BR-05 | Devoluciones Restringidas | Inventory | `Category.is_returnable` + validación en `register_return` | Tests: rechazo mesa, aceptación electro |
| BR-06 | Ventana 5 Min Autocorrección | Movements | `correct_movement_within_window` + validación de tiempo | Tests: corrección 3min pasa, 6min falla |
| BR-07 | Justificación Obligatoria Ajuste | Movements | `register_adjustment` exige justificación + rol almacenista | Tests: rechazo sin justificación, aceptación con texto |
| BR-08 | Validación Cruzada Despacho | Movements | `register_dispatch` compara scanned vs order_sku | Tests: mismatch rechazado, match aceptado |
| BR-09 | Nota Discrepancia Recepción | Movements | `register_entry` exige nota si qty != qty_facturada | Tests: discrepancia sin nota rechazada |
| BR-10 | Inmutabilidad Ledger | Movements/Audit | SIN PUT/PATCH/DELETE en viewsets + guardas de permisos | Tests: intento PUT rechazado con 405/403 |
| BR-11 | Stock por Ubicación + Ledger | Inventory | `StockByLocation` + `Movement` atómico + `reconstruct_stock_from_ledger` | Tests: sincronización y reconstrucción correcta |
| BR-12 | SKU patrón | Catalog | Validador en `Product.sku` (`validate_sku_format`) | Tests: rechazo "ELECTRO001", aceptación "ELEC-0001" |
| BR-13 | Factura PDF + Numeración | Movements | `generate_invoice_pdf` + secuencia atómica | Tests: PDF existe, numeración correcta |
| BR-14 | Estado Operativo de Ubicación | Inventory/Movements | `_ensure_location_allows_origin` + `_ensure_location_allows_destination` en `movements/services.py`; `Location.OperationalStatus` en `inventory/models.py` | Tests: archived/blocked bloquean todo, maintenance/restricted bloquean origen |
| BR-15 | StorageType Activo como Requisito | Inventory | Validación en `create_location`/`update_location`; `StorageType.is_active` | Tests: tipo inactivo rechazado en asignación |

---

## 4. Modelo de Inventario: Ledger + Stock Derivado

Este es el **núcleo crítico** de la arquitectura. Implementa un modelo de inventario robusto basado en **event sourcing lite** donde la fuente de verdad es inmutable.

### 4.1 Fuente de Verdad: El Ledger de Movimientos

La fuente de verdad del inventario es el ledger de movimientos (`Movement`). Cada cambio en el stock se registra como un movimiento atómico e inmutable.

**Tipos de movimiento permitidos**:

- **ENTRADA**: Recepción de mercancía en una ubicación.
- **SALIDA_VENTA_MAYOR**: Despacho a cliente mayorista.
- **SALIDA_VENTA_MENOR**: Despacho minorista (vitrina).
- **SALIDA_DANO**: Baja de inventario por daño.
- **SALIDA_VENCIMIENTO**: Baja de inventario por vencimiento.
- **TRASLADO**: Movimiento interno entre ubicaciones (no altera stock global).
- **AJUSTE**: Corrección de discrepancia con justificación (solo almacenista).
- **DEVOLUCION**: Reingreso de producto (Electroterapia/Electrónicos).

**Campos obligatorios en cada movimiento**:

```python
class Movement(Model):
    id = UUIDField(primary_key=True)  # Identificador único
    movement_type = CharField(choices=MOVEMENT_TYPES)
    product = ForeignKey('catalog.Product')
    origin_location = ForeignKey('inventory.Location', null=True)  # Para salidas/traslados
    destination_location = ForeignKey('inventory.Location', null=True)  # Para traslados/entradas
    quantity = PositiveIntegerField()
    
    # Snapshots de stock para trazabilidad completa
    stock_previo_origen = PositiveIntegerField()
    stock_resultante_origen = PositiveIntegerField()
    stock_previo_destino = PositiveIntegerField(null=True)  # Solo traslados
    stock_resultante_destino = PositiveIntegerField(null=True)  # Solo traslados
    
    # Atributos de validación
    serial_number = CharField(null=True, blank=True)  # BR-04: obligatorio para Electroterapia
    quantity_invoiced = PositiveIntegerField(null=True)  # BR-09: cantidad facturada
    discrepancy_note = TextField(null=True, blank=True)  # BR-09: nota si hay diferencia
    justification = TextField(null=True, blank=True)  # BR-07: obligatoria en AJUSTE
    
    # Validación cruzada en despacho
    scanned_code = CharField(null=True)  # BR-08: código físicamente escaneado
    order_sku = CharField(null=True)  # BR-08: SKU esperado de la orden
    
    # Facturación
    invoice_number = CharField(unique=True, null=True)  # BR-13: ICM-0001, ICM-0002, etc.
    invoice_pdf = FileField(null=True)  # BR-13: PDF generado
    
    # Auditoría
    executed_by = ForeignKey('authentication.User')  # BR-01: quién lo ejecutó
    created_at = DateTimeField(auto_now_add=True)  # Timestamp UTC
    
    # Vínculos para correcciones
    related_movement = ForeignKey('self', null=True)  # BR-06: movimiento corregido/referencia
    
    # Inmutabilidad
    class Meta:
        immutable = True  # No PUT/PATCH/DELETE
```

### 4.2 Stock Derivado: Caché Consistente

El stock actual se almacena en `StockByLocation` como caché derivado del ledger. Esta estructura permite consultas rápidas, pero **NO es la fuente de verdad**.

```python
class StockByLocation(Model):
    product = ForeignKey('catalog.Product')
    location = ForeignKey('inventory.Location')
    current_stock = PositiveIntegerField(default=0)  # Caché del stock actual
    
    class Meta:
        unique_together = ('product', 'location')
```

**Garantías de sincronización**:
- Cada `Movement` que altera stock **debe** actualizar `StockByLocation` en la misma transacción (`@transaction.atomic`).
- Si la transacción falla, se revierte todo: movimiento y stock.
- El stock derivado puede reconstruirse ejecutando `SELECT SUM(delta) FROM movements WHERE producto=X AND ubicacion=Y`.

### 4.3 Reglas de Consistencia Obligatorias (BR-11)

**REGLA 1**: Nunca modificar `StockByLocation` sin crear un `Movement` en la misma transacción.
- Esto asegura que el historial refleja todo cambio de stock.

**REGLA 2**: El stock derivado siempre debe poder reconstruirse desde el ledger.
- Implementar función de verificación: `reconstruct_stock_from_ledger(product_id, location_id)`.
- Comparar con `StockByLocation.current_stock`.
- Si hay discrepancia: generar alerta y reporte.

**REGLA 3**: Toda operación sobre el inventario es atómica (transacción de BD).
- Si un paso falla, se revierte todo.
- Usar `@transaction.atomic` en `services.py`.
- Usar `select_for_update()` en actualizaciones concurrentes para evitar race conditions.

**REGLA 4**: Los movimientos son inmutables. No existen endpoints PUT/PATCH/DELETE.
- Un error se corrige con un nuevo movimiento (BR-06, BR-07).
- Nunca editar historial.

**REGLA 5**: No se permiten stocks negativos.
- Constraint en BD: `CHECK (current_stock >= 0)`.
- Validación en lógica: antes de salida, verificar `current_stock >= cantidad_requerida`.
- Si insuficiente: lanzar `InsufficientStockError`.

### 4.4 Flujos Atómicos de Operación

Cada operación de inventario implementada en `movements/services.py` sigue este patrón:

```python
@transaction.atomic
def register_entry(user, product_id, location_id, quantity, serial_number=None, 
                   qty_invoiced=None, discrepancy_note=None):
    # Paso 1: Validaciones de negocio (BR-04, BR-09, etc.)
    product = validate_and_get_product(product_id)
    location = validate_and_get_location(location_id)
    
    if product.category.requires_serial_number and not serial_number:
        raise SerialNumberRequiredError()  # BR-04
    
    if qty_invoiced and quantity != qty_invoiced and not discrepancy_note:
        raise DiscrepancyNoteRequiredError()  # BR-09
    
    # Paso 2: Obtener stock previo
    stock_by_location, created = StockByLocation.objects.get_or_create(
        product=product, location=location, defaults={'current_stock': 0}
    )
    stock_previo = stock_by_location.current_stock
    
    # Paso 3: Crear movimiento
    movement = Movement.objects.create(
        movement_type='ENTRADA',
        product=product,
        origin_location=None,
        destination_location=location,
        quantity=quantity,
        stock_previo_origen=None,
        stock_resultante_origen=None,
        stock_previo_destino=stock_previo,
        stock_resultante_destino=stock_previo + quantity,
        serial_number=serial_number,
        quantity_invoiced=qty_invoiced,
        discrepancy_note=discrepancy_note,
        executed_by=user,
    )
    
    # Paso 4: Actualizar stock derivado
    stock_by_location.current_stock += quantity
    stock_by_location.save()
    
    # Paso 5: Registrar auditoría
    audit_log_event(event_type='ENTRY', movement=movement, user=user)
    
    # Paso 6: Evaluar alertas (BR-11)
    check_and_create_minimum_stock_alert(product, location)
    
    return movement  # Todo atómico o ROLLBACK
```

### 4.5 Ubicaciones de Almacenamiento

El sistema soporta tres ubicaciones físicas:

```python
class Location(Model):
    code = CharField(unique=True)  # 'VITRINA', 'BODEGA_1', 'BODEGA_2'
    description = CharField()
    is_retail = BooleanField(default=False)  # Vitrina = True, Bodegas = False
```

Las ubicaciones definen:
- Dónde se ejecutan las operaciones (vitrina vs. mayorista).
- Cómo se consolida el stock total.
- Reglas de visibilidad en reportes.

---

## 5. Desacoplamiento entre Modulos y Separación de Responsabilidades

### 5.1 Regla de comunicacion inter-app

Las apps se comunican por contratos de servicio (funciones en services.py), evitando acceso directo a modelos de otro dominio salvo casos justificados.

Esto reduce acoplamiento, mejora testabilidad y permite refactors internos sin romper consumidores.

### 5.2 Separacion lectura/escritura

Patron aplicado:

- Escritura: services.py (comandos con efectos).
- Lectura: selectors.py (consultas puras).

Esta separacion simplifica optimizacion de consultas y evita mezclar reglas de negocio con reporting.

## 6. SOLID Aplicado al Proyecto

### 6.1 SRP (Single Responsibility)

Cada capa tiene una responsabilidad única:
- `models.py`: Estructura de datos.
- `serializers.py`: Validación y transformación de formato.
- `views.py`: Protocolo HTTP.
- `services.py`: Lógica de dominio.
- `selectors.py`: Consultas.
- `permissions.py`: Acceso.

### 6.2 OCP (Open/Closed)

Nuevos flujos de movimiento o validaciones se agregan en `services.py` sin reescribir `views.py`, `serializers.py` o `models.py`.

Ejemplo: Nuevo tipo de movimiento `REEMPAQUE`:
1. Agregar a `Movement.movement_type` choices.
2. Agregar función `register_repack()` en `services.py`.
3. Agregar endpoint en `views.py` que llame al servicio.
4. Sin tocar models ni serializers.

### 6.3 LSP (Liskov Substitution)

Permisos y excepciones especializadas (ej: `IsAlmacenista`, `SerialNumberRequiredError`) mantienen comportamiento compatible con contratos base de DRF y excepciones compartidas.

### 6.4 ISP (Interface Segregation)

Permisos y servicios se mantienen pequeños y específicos:
- `IsAlmacenista` solo valida rol.
- `IsWithinOperatingHours` solo valida horario.
- Se combinan en views si es necesario (`permission_classes = [IsAuthenticated, IsAlmacenista, IsWithinOperatingHours]`).

### 6.5 DIP (Dependency Inversion)

Los módulos dependen de abstracciones operativas (servicios/selectores), no de detalles internos:
- `from apps.inventory.services import get_stock_by_product()` (abstracción).
- NO: `from apps.inventory.models import StockByLocation` (detalle).

## 7. Patrones de Diseño Utilizados

### 7.1 Service Layer (Capa de Servicio)

**Propósito**: Centralizar toda la lógica de negocio en funciones reutilizables.

**Ejemplo**:
```python
# apps/movements/services.py
def register_entry(user, product_id, location_id, quantity, ...):
    # Toda la lógica aquí: validaciones, transacciones, efectos secundarios.
    pass

# apps/movements/views.py
class EntryViewSet(ViewSet):
    def create(self, request):
        serializer = EntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = register_entry(
            user=request.user,
            product_id=serializer.validated_data['product_id'],
            ...
        )
        return Response(MovementSerializer(movement).data)
```

**Beneficio**: La vista es delgada, el servicio es reutilizable (CLI, tasks, tests).

### 7.2 Repository-like Query Object (Selectores)

**Propósito**: Encapsular consultas complejas sin efectos secundarios.

**Ejemplo**:
```python
# apps/inventory/selectors.py
def get_stock_by_product(product_id):
    """Retorna stock por ubicación y total consolidado."""
    stocks = StockByLocation.objects.filter(product_id=product_id)
    return {
        'product_id': product_id,
        'by_location': [{
            'location': s.location.code,
            'quantity': s.current_stock,
        } for s in stocks],
        'total': sum(s.current_stock for s in stocks),
    }
```

**Beneficio**: Lógica de acceso a datos centralizada, fácil de testear y optimizar.

### 7.3 Transaction Script (Transacciones Atómicas)

**Propósito**: Garantizar consistencia all-or-nothing en operaciones críticas.

**Ejemplo**:
```python
# apps/movements/services.py
@transaction.atomic
def register_entry(...):
    # Paso 1: Validar
    # Paso 2: Leer stock previo
    # Paso 3: Crear movimiento
    # Paso 4: Actualizar stock derivado
    # Paso 5: Registrar auditoría
    # Si algo falla: ROLLBACK de todos los pasos
```

**Beneficio**: No hay inconsistencias intermedias, especialmente crítico para BR-11.

### 7.4 Unit of Work (via transaction.atomic)

**Propósito**: Garantizar que múltiples cambios de datos se persisten conjuntamente.

**Implementación**: Django `@transaction.atomic` + `select_for_update()` para locks de fila.

**Beneficio**: Manejo automático de rollback, evita race conditions.

### 7.5 Domain Exceptions (Excepciones de Dominio)

**Propósito**: Expresar errores de negocio de forma clara y controlada.

**Ejemplo**:
```python
# shared/exceptions.py
class SerialNumberRequiredError(ICMBaseException):
    """BR-04: Producto requiere número de serie."""
    pass

# apps/movements/services.py
if product.category.requires_serial_number and not serial_number:
    raise SerialNumberRequiredError(
        f"Producto {product.sku} requiere número de serie"
    )

# config/exception_handler.py
def custom_exception_handler(exc, context):
    if isinstance(exc, ICMBaseException):
        return Response(
            {'error': exc.default_code, 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

**Beneficio**: Errores claros, manejo centralizado, trazables.

### 7.6 Factory (para Testing)

**Propósito**: Construir datos de prueba reproducibles.

**Ejemplo**:
```python
# tests/factories.py
class ProductFactory(factory.django.DjangoModelFactory):
    sku = factory.Sequence(lambda n: f"PRD-{n%9999+1:04d}")
    category = factory.SubFactory(CategoryFactory)
    
    class Meta:
        model = Product

# tests/test_movements.py
def test_entry_requires_serial():
    product = ProductFactory(
        category__requires_serial_number=True
    )
    with pytest.raises(SerialNumberRequiredError):
        register_entry(..., product_id=product.id, serial_number=None)
```

**Beneficio**: Tests más limpios, datos consistentes, menos código de setup.

### 7.7 CQRS-lite (Separación Lectura/Escritura)

**Propósito**: Diferencias clara entre comandos (escriben) y consultas (leen).

**Implementación**:
- `services.py`: Comandos (write).
- `selectors.py`: Consultas (read).

**Ejemplo**:
```python
# Escritura
from apps.movements.services import register_entry

# Lectura
from apps.inventory.selectors import get_stock_by_product
from apps.reports.selectors import get_movements_by_period
```

**Beneficio**: Permite optimizaciones independientes (replicación de lectura, índices específicos, caché).

---

## 8. Seguridad, RBAC y Cumplimiento

### 8.1 Control de Acceso Basado en Roles (RBAC)

**Tres roles del sistema**:

| Rol | Descripción | Endpoints | Restricciones |
|-----|-------------|-----------|---------------|
| `almacenista` | Supervisor. Acceso total. | Todas las APIs (excepto admin) | Acceso 24/7. BR-02: Gestiona credenciales. BR-07: Puede crear ajustes. |
| `auxiliar_despacho` | Operario de despacho. | Movimientos de salida, consultas limitadas | Acceso solo 07:00–12:00 y 14:00–17:00 (BR-03). No puede gestionar usuarios. |
| `administrador` | Analista. Monitoreo KPI. | Reportes, solo lectura | Acceso 24/7. Solo dashboards, sin permisos de escritura. |

**Implementación**: 
```python
# shared/permissions.py
class IsAlmacenista(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'almacenista'

class IsAuxiliarDespacho(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'auxiliar_despacho'

class IsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'administrador'

class IsWithinOperatingHours(BasePermission):
    """BR-03: Restricción horaria para auxiliar."""
    def has_permission(self, request, view):
        user = request.user
        if user.role != 'auxiliar_despacho':
            return True
        now = timezone.now().astimezone(
            timezone.pytz.timezone('America/Bogota')
        )
        hour = now.hour
        return (7 <= hour < 12) or (14 <= hour < 17)
```

**Aplicación en views**:
```python
# apps/movements/views.py
class DispatchViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsAuxiliarDespacho, IsWithinOperatingHours]
```

### 8.2 Autenticación con JWT

**Flujo de autenticación**:

1. **Login**: Usuario envía `{username, password}`.
2. **Validación**: `authenticate_user()` valida credenciales + restricción horaria (BR-03).
3. **Tokens generados**:
   - `access_token`: Vida corta (60 min), incluye rol y user_id en payload.
   - `refresh_token`: Vida larga (7 días), se almacena en cliente.
4. **Uso**: Cada request incluye `Authorization: Bearer <access_token>`.
5. **Renovación**: Cuando expira, cliente envía refresh_token para obtener nuevo access_token.
6. **Logout**: Refresh token se agrega a blacklist (revocable).

**Configuración**:
```python
# settings/base.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'SIGNING_KEY': SECRET_KEY,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**Endpoints de autenticación**:
- `POST /api/v1/auth/login/` → tokens (validación horaria BR-03).
- `POST /api/v1/auth/token/refresh/` → nuevo access_token.
- `POST /api/v1/auth/logout/` → agregar refresh a blacklist.
- `GET /api/v1/auth/me/` → perfil autenticado.

### 8.3 Gestión de Credenciales (BR-02)

**Regla**: Solo almacenista puede crear/modificar/deshabilitar usuarios.

**Seguridad de contraseñas**:
- El modelo de usuario hereda de `AbstractUser`, por lo que el campo `password` y su manejo seguro ya vienen provistos por Django.
- La creación y el cambio de contraseña usan `set_password()`, así que la contraseña nunca se persiste en texto plano.
- En desarrollo y producción se conserva el hashing seguro de Django; en la suite de pruebas se usa un hasher más liviano solo para acelerar la ejecución.

**Implementación**:
```python
# apps/authentication/services.py
def create_user(executor_user, user_data):
    if executor_user.role != 'almacenista':
        raise UnauthorizedCredentialManagementError(
            f"Solo almacenista puede crear usuarios. Rol actual: {executor_user.role}"
        )
    user = User.objects.create_user(**user_data)
    audit_log_event('USER_CREATED', user=executor_user, user_affected=user)
    return user

# apps/authentication/views.py
class UserViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsAlmacenista]
    
    def create(self, request):
        # Solo almacenista llega aquí
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_user(request.user, serializer.validated_data)
        return Response(UserSerializer(user).data, status=201)
```

### 8.4 Auditoría de Autenticación (BR-01)

**Eventos auditados**:
- Login exitoso.
- Login fallido (credenciales inválidas, horario no permitido).
- Creación de usuario.
- Modificación de usuario.
- Deshabilitación de usuario.
- Logout.

**Ejemplo**:
```python
# apps/authentication/services.py
def authenticate_user(username, password, request_time):
    user = User.objects.get(username=username)
    
    # Validar credenciales
    if not user.check_password(password):
        audit_log_event(
            'LOGIN_FAILED',
            user=user,
            detail='Contraseña inválida'
        )
        raise AuthenticationFailed("Credenciales inválidas")
    
    # Validar horario (BR-03)
    if user.role == 'auxiliar_despacho':
        if not is_within_operating_hours(request_time):
            audit_log_event(
                'LOGIN_FAILED',
                user=user,
                detail='Fuera de horas de operación'
            )
            raise OutsideOperatingHoursError(...)
    
    audit_log_event('LOGIN_SUCCESS', user=user)
    return user
```

### 8.5 Cumplimiento de Datos Personales (Ley 1581)

**Principios**:
- Los datos de cliente se exponen solo si el usuario está autorizado en el contexto de una operación.
- Consentimiento explícito para procesamiento de datos en despachos mayoristas.
- Anonimización en reportes generales.

**Implementación**:
```python
# apps/movements/models.py
class Movement(Model):
    customer_data = JSONField(null=True, blank=True)  # Datos de cliente
    privacy_notice_acknowledged = BooleanField(default=False)

# apps/movements/services.py
def register_dispatch(user, ..., customer_data=None):
    if movement_type == 'SALIDA_VENTA_MAYOR' and customer_data:
        if not customer_data.get('privacy_notice_acknowledged'):
            raise PrivacyConsentRequiredError(
                "Debe reconocer aviso de privacidad para despacho mayorista"
            )
```

### 8.6 Seguridad de Datos y Superficie de Exposición

La seguridad en ICM no depende de una sola capa; se aplica de forma transversal en autenticación, autorización, persistencia y auditoría.

**Controles principales**:
- Autenticación sin sesiones de servidor: el acceso a la API usa JWT con `Bearer`.
- Contraseñas almacenadas solo como hash seguro administrado por Django.
- Permisos por rol en backend y validaciones adicionales por caso de uso.
- Tokens `refresh` revocables mediante blacklist al cerrar sesión o deshabilitar usuarios.
- Respuestas de autenticación y perfil sin exponer el campo `password`.
- Auditoría de eventos sensibles como login, logout, creación de usuarios, cambios de credenciales y deshabilitación de cuentas.
- Uso de consultas y serializers controlados para evitar exponer campos no previstos en el contrato.

**Datos sensibles**:
- Los datos personales se manejan bajo el principio de mínimo privilegio.
- Los reportes y consultas deben devolver solo lo necesario para el contexto funcional.
- Cuando un flujo requiere datos personales de cliente, la validación de consentimiento o aviso de privacidad se realiza en la capa de servicio.

**Notas operativas**:
- En local y producción se recomienda transporte cifrado a nivel de infraestructura o proxy inverso.
- La política de hashing de contraseñas no debe redefinirse para debilitar la seguridad fuera de pruebas.
- La suite de pruebas puede usar hashers más rápidos, pero eso no cambia el comportamiento del sistema en ejecución real.

**Consultas con control de acceso**:
```python
# apps/reports/selectors.py
def get_movements_with_customer_data(user):
    """Solo almacenista y administrador ven datos de cliente."""
    if user.role not in ['almacenista', 'administrador']:
        # Auxiliar ve movimientos pero sin customer_data
        movements = Movement.objects.filter(...).values(
            'id', 'product', 'quantity', 'created_at'
            # Sin customer_data
        )
    else:
        # Almacenista ve todo
        movements = Movement.objects.filter(...).values()
    return movements
```

---

## 9. Rendimiento y Consistencia de Datos

El desempeño del sistema está ligado directamente a la solidez de la arquitectura de inventario.

### 9.1 Optimización de Consultas

**Principios**:

1. **Evitar N+1**: Usar `select_related()` y `prefetch_related()`.

```python
# MALO: N+1
movements = Movement.objects.all()
for m in movements:
    print(m.product.sku, m.executed_by.username)  # Query por cada fila

# BUENO
movements = Movement.objects.select_related(
    'product', 'executed_by'
).all()
for m in movements:
    print(m.product.sku, m.executed_by.username)  # Sin queries adicionales
```

2. **Agregaciones en BD**: Suma, conteo, etc., en SQL, no en Python.

```python
# MALO
stocks = StockByLocation.objects.filter(product_id=1)
total = sum(s.current_stock for s in stocks)  # Iteración en Python

# BUENO
total = StockByLocation.objects.filter(product_id=1).aggregate(
    total=Sum('current_stock')
)['total']
```

3. **Índices estratégicos**: En movimientos y stock.

```python
# models.py
class Movement(Model):
    ...
    class Meta:
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['executed_by', 'created_at']),
            models.Index(fields=['movement_type', 'created_at']),
            models.Index(fields=['origin_location', 'created_at']),
        ]

class StockByLocation(Model):
    ...
    class Meta:
        indexes = [
            models.Index(fields=['product', 'location']),  # PK virtual
            models.Index(fields=['current_stock']),  # Búsquedas de bajo stock
        ]
```

### 9.2 Consistencia Bajo Concurrencia

**Problema**: Múltiples auxiliares despachan simultáneamente, race condition en stock.

**Solución**: Bloqueos de fila (`select_for_update`).

```python
# apps/movements/services.py
@transaction.atomic
def register_dispatch(user, product_id, location_id, quantity, ...):
    # Obtener y bloquear fila en stock
    stock_by_location = StockByLocation.objects.select_for_update().get(
        product_id=product_id, location_id=location_id
    )
    
    # Validar cantidad disponible
    if stock_by_location.current_stock < quantity:
        raise InsufficientStockError()
    
    # Crear movimiento y actualizar (dentro de transacción)
    movement = Movement.objects.create(...)
    stock_by_location.current_stock -= quantity
    stock_by_location.save()
    
    return movement
    # Si otra transacción esperaba este lock, procede aquí
    # Garantiza consistencia
```

### 9.3 Reconstrucción y Verificación de Consistencia

**Función de verificación** (útil para debugging):

```python
# apps/inventory/selectors.py
def reconstruct_stock_from_ledger(product_id, location_id):
    """
    Reconstruye el stock derivado desde el ledger.
    Si hay discrepancia con StockByLocation.current_stock → alerta.
    """
    delta = Movement.objects.filter(
        product_id=product_id,
        destination_location_id=location_id
    ).aggregate(
        total_entrada=Sum('quantity', filter=Q(movement_type__in=[
            'ENTRADA', 'TRASLADO', 'DEVOLUCION'
        ])),
        total_salida=Sum('quantity', filter=Q(movement_type__in=[
            'SALIDA_VENTA_MAYOR', 'SALIDA_VENTA_MENOR', 'SALIDA_DANO', 
            'SALIDA_VENCIMIENTO'
        ]))
    )
    
    entrada = delta['total_entrada'] or 0
    salida = delta['total_salida'] or 0
    reconstructed = entrada - salida
    
    actual = StockByLocation.objects.get(
        product_id=product_id, location_id=location_id
    ).current_stock
    
    if reconstructed != actual:
        # Alerta de discrepancia
        audit_log_event(
            'STOCK_DISCREPANCY',
            detail=f"Reconstructed: {reconstructed}, Actual: {actual}"
        )
        return {'status': 'DISCREPANCY', 'reconstructed': reconstructed, 'actual': actual}
    
    return {'status': 'CONSISTENT', 'stock': actual}
```

### 9.4 Caché y TTL (Preparación Futura)

Aunque no se implementa en esta fase, la arquitectura prepara para:
- Redis caché de stock por ubicación (TTL 5 min).
- Invalidación automática al crear movimiento.
- Fallback a BD si caché expira.

---

---

## 10. Docker, Entornos y Operación

La contenerización garantiza consistencia entre desarrollo, testing y producción.

### 10.1 Composición de Servicios

`docker-compose.yml`:

```yaml
version: '3.9'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: icm_db
      POSTGRES_USER: icm_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U icm_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - icm_network

  web:
    build: .
    command: /entrypoint.sh python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DATABASE_URL=postgresql://icm_user:${DB_PASSWORD}@db:5432/icm_db
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    networks:
      - icm_network

volumes:
  postgres_data:

networks:
  icm_network:
    driver: bridge
```

**Características**:
- Health checks: Espera a que BD esté lista antes de iniciar web.
- Volúmenes: Persistencia de BD.
- Variables de entorno: Configuración centralizada.

### 10.2 Entrypoint (Inicialización)

`docker/entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "Esperando a que PostgreSQL esté disponible..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "PostgreSQL disponible."

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando servidor..."
exec "$@"
```

**Garantía**: BD lista + esquema actualizado + statics servidos antes de que el servidor escuche.

### 10.3 Variables de Entorno

`
.env.example`:

```env
# Django
DJANGO_SECRET_KEY=change-this-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.development

# Database
DB_NAME=icm_db
DB_USER=icm_user
DB_PASSWORD=icm_password
DB_HOST=db
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Application
APP_TIMEZONE=America/Bogota

# Optional (future phases)
REDIS_URL=redis://redis:6379/0
```

**Principio**: Nunca hardcodear secretos en código fuente. Usar `.env` localmente, variables de entorno en producción.

### 10.4 Ambientes (Development vs Production)

**Development** (`config/settings/development.py`):
- Debug: True
- DB local
- CORS: Abierto
- Email: Console

**Production** (`config/settings/production.py`):
- Debug: False
- DB remota (RDS/managed)
- CORS: Whitelist
- Email: SMTP
- HTTPS: Forzado
- Security headers: Aplicados

### 10.5 Restricción actual de empaquetado de producción

La imagen de produccion no es equivalente a la de desarrollo: `docker-compose.prod.yml` arranca `gunicorn`, pero `docker/Dockerfile` instala solo `requirements/base.txt`. Como `gunicorn` vive en `requirements/production.txt`, cualquier despliegue productivo debe incorporar esa dependencia o una capa equivalente antes del arranque.

Impacto:

- No se debe asumir que la imagen base sirva para produccion sin una construccion adicional.
- Si cambian las dependencias de runtime, el Dockerfile y los requirements deben mantenerse sincronizados.
- La validacion de despliegue requiere revisar el binario de arranque, no solo la compilacion de Django.

---

## 11. Testing y Aseguramiento de Calidad

La arquitectura modular facilita testing en múltiples niveles.

### 11.1 Estrategia de Pruebas

**Unitarias** (60% cobertura):
- Servicios: Lógica de dominio aislada.
- Validadores y excepciones.

**Integración** (25% cobertura):
- Endpoints API + autenticación + permisos.
- Flujos completos de movimientos.

**Consistencia** (15% cobertura):
- Invariantes de inventario (BR-11).
- Restricciones de rol (BR-01, BR-02, BR-03).
- Inmutabilidad de ledger (BR-10).

### 11.2 Casos Críticos de Testing

Estos tests **deben** pasar siempre:

| Caso | Referencia | Verificación |
|------|-----------|--------------|
| Auxiliar rechazado fuera de horario | BR-03 | Login 13:00 falla, 08:00 pasa |
| Movimiento inmutable | BR-10 | PUT/PATCH devuelven 405/403 |
| Validación cruzada en despacho | BR-08 | Código escaneado != SKU rechazado |
| Serial obligatorio Electroterapia | BR-04 | Entrada sin serial rechazada |
| Devolución bloqueada en Mesas | BR-05 | Devolucion de mesa rechazada |
| Ajuste sin justificación | BR-07 | Ajuste vacío rechazado |
| Stock reconstribible | BR-11 | ledger sum == StockByLocation.current_stock |
| Nota de discrepancia | BR-09 | Recepción con qty diferente exige nota |
| Solo almacenista gestiona usuarios | BR-02 | Auxiliar POST /users/ rechazado |

### 11.3 Herramientas y Configuración

```python
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
addopts = --cov=apps --cov-report=html --tb=short

# Run: pytest
# Run with coverage: pytest --cov
```

**Librerías**:
- `pytest`, `pytest-django`: Framework.
- `factory-boy`: Fixtures de datos.
- `pytest-cov`: Cobertura.
- `freeze-gun`: Mocking de tiempo (para BR-03, BR-06).

### 11.5 Restricción actual de fidelidad de pruebas

La configuracion de pruebas usa `config.settings.test`, que ejecuta la suite sobre SQLite in-memory y desactiva `DEFAULT_THROTTLE_CLASSES`. Esto acelera la ejecucion y reduce friccion local, pero no reproduce la semantica de PostgreSQL ni valida throttling de produccion.

Impacto:

- Las pruebas automatizadas no ejercitan `select_for_update()` ni bloqueos reales de PostgreSQL.
- Los limites de peticiones se validan a nivel logico, no con el throttler activo.
- Para concurrencia real o limites de produccion, hacen falta pruebas especificas contra PostgreSQL.

### 11.4 CI/CD (GitHub Actions - Preparación)

`.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - run: pip install -r requirements/development.txt
      - run: pytest
```

---

## 12. Convenciones de Implementación

### 12.1 Estilo de Código

- **PEP 8**: `black` (formateador), `isort` (imports), `flake8` (linter).
- **Type hints**: Obligatorios en `services.py` y `selectors.py`.

```python
# CORRECTO
from typing import List, Dict, Optional
from django.db.models import QuerySet

def get_stock_by_product(product_id: int) -> Dict[str, any]:
    """Retorna stock consolidado por ubicación."""
    ...

# INCORRECTO
def get_stock(product_id):
    # Sin type hints
    ...
```

### 12.2 Docstrings y Referencia a Requisitos

Cada función debe incluir docstring con referencia a RF/BR:

```python
def register_entry(
    user: User,
    product_id: int,
    location_id: int,
    quantity: int,
    serial_number: Optional[str] = None,
    qty_invoiced: Optional[int] = None,
    discrepancy_note: Optional[str] = None,
) -> Movement:
    """
    Registra una entrada de producto a una ubicación.
    
    Ref: RF-005, Scenario 1
    Reglas aplicadas:
    - BR-04: Serial requerido si producto lo exige.
    - BR-09: Nota de discrepancia si qty != qty_facturada.
    - BR-11: Atomicidad con StockByLocation.
    
    Args:
        user: Usuario ejecutor.
        product_id: ID del producto.
        location_id: Ubicación destino.
        quantity: Cantidad recibida.
        serial_number: Número de serie (obligatorio para Electroterapia).
        qty_invoiced: Cantidad facturada (para detección de discrepancia).
        discrepancy_note: Nota si hay discrepancia.
    
    Returns:
        Movement creado.
    
    Raises:
        SerialNumberRequiredError: Si producto requiere serial y no se proporciona.
        DiscrepancyNoteRequiredError: Si hay discrepancia sin nota.
        InsufficientStockError: Si no hay espacio (constraint DB).
    """
    ...
```

### 12.3 Timestamps en UTC

Todos los `created_at`, `updated_at` se almacenan en UTC:

```python
# settings/base.py
USE_TZ = True
TIME_ZONE = 'UTC'

# Conversión a zona local: solo en serialización
class MovementSerializer(Serializer):
    created_at = DateTimeField(format='%Y-%m-%d %H:%M:%S %Z')
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Convertir a zona local
        local_tz = pytz.timezone('America/Bogota')
        local_dt = instance.created_at.astimezone(local_tz)
        ret['created_at_local'] = local_dt.strftime('%Y-%m-%d %H:%M:%S')
        return ret
```

### 12.4 Versionado de API

Todo endpoint está bajo `/api/v1/`:

```python
# config/urls.py
urlpatterns = [
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/catalog/', include('apps.catalog.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/movements/', include('apps.movements.urls')),
    ...
]
```

Cambios incompatibles → `/api/v2/`.

### 12.5 Documentación OpenAPI/Swagger

`drf-spectacular` genera automáticamente, pero asegúrate de actualizar descripciones:

```python
# apps/movements/views.py
class DispatchViewSet(ViewSet):
    """
    Despacho de productos a clientes.
    
    Incluye validación cruzada (BR-08) y generación de factura (BR-13).
    """
    
    @action(detail=False, methods=['post'])
    def register_dispatch(self, request):
        """
        Registra una salida de producto.
        
        Valida que código escaneado coincida con SKU de orden (BR-08).
        """
        ...
```

Acceso: `GET /api/v1/docs/` → Swagger UI.

---

## 13. Checklist de Integridad Arquitectónica

**Antes de aceptar cambios estructurales, validar**:

### Separación de Responsabilidades

- [ ] No hay lógica de negocio en `models.py` (solo estructura).
- [ ] No hay lógica de negocio en `serializers.py` (solo validación de formato).
- [ ] No hay lógica de negocio en `views.py` (solo protocolo HTTP).
- [ ] Toda la lógica de negocio está en `services.py`.
- [ ] Todas las consultas complejas están en `selectors.py`.
- [ ] No existen imports cruzados de `models.py` entre apps (salvo justificación explícita).

### Reglas de Negocio Críticas

- [ ] BR-01: Cada movimiento tiene `executed_by`.
- [ ] BR-02: Solo almacenista puede crear usuarios (guarda en `services.py` + permiso DRF).
- [ ] BR-03: Auxiliar rechazado fuera de horario (validación en login + middleware).
- [ ] BR-04: Serial obligatorio para Electroterapia.
- [ ] BR-05: Devoluciones bloqueadas en Mesas.
- [ ] BR-06: Correcciones solo dentro de 5 minutos.
- [ ] BR-07: Ajustes exigen justificación + rol almacenista.
- [ ] BR-08: Validación cruzada en despacho (código != SKU rechazado).
- [ ] BR-09: Nota obligatoria si hay discrepancia en recepción.
- [ ] BR-10: **Movimientos e AuditLog son inmutables** (sin PUT/PATCH/DELETE).
- [ ] BR-11: Stock derivado sincronizado + reconstruible desde ledger.
- [ ] BR-12: SKU validado contra el patrón 1–4 letras, guion, 1–4 dígitos.
- [ ] BR-13: Facturas numeradas secuencialmente + PDF generado.
- [ ] BR-14: Estado operativo de ubicación validado antes de cada movimiento (archived/blocked rechazan todo, maintenance/restricted rechazan origen).
- [ ] BR-15: StorageType inactivo rechazado al asignar a ubicaciones nuevas o existentes.

### Transacciones y Consistencia

- [ ] Todas las operaciones de `services.py` que alteren stock tienen `@transaction.atomic`.
- [ ] Uso de `select_for_update()` en lecturas que precedan actualizaciones (prevención de race conditions).
- [ ] Stock negativo imposible (constraint CHECK en BD).
- [ ] No hay Stock actualizado sin Movement creado en la misma transacción.

### Testing

- [ ] Tests unitarios de `services.py` > 60% cobertura.
- [ ] Tests de integración de endpoints > 25% cobertura.
- [ ] Tests de invariantes (BR-11, stock reconstribible) > 15% cobertura.
- [ ] Todos los 9 casos críticos pasan (tabla de BR en 11.2).

### Seguridad y Auditoría

- [ ] JWT configurado con tiempos de expiración (access 60min, refresh 7d).
- [ ] Refresh tokens en blacklist al logout/deshabilitar usuario.
- [ ] RBAC aplicado en todos los endpoints.
- [ ] Todos los eventos significativos registrados en `AuditLog`.
- [ ] Datos de cliente expuestos solo a usuarios autorizados.

### Performance

- [ ] Índices creados en Movement (producto, user, tipo, fecha).
- [ ] Índices en StockByLocation (product, location, current_stock).
- [ ] Consultas de búsqueda optimizadas sin N+1.
- [ ] Agregaciones en BD, no en Python.

### Desacoplamiento

- [ ] Las apps se comunican por `services.py`, no importan modelos ajenos.
- [ ] Cambios en un servicio no rompen consumidores (interfaz estable).
- [ ] Excepciones de dominio reutilizables desde `shared/exceptions.py`.

### Documentación

- [ ] Docstrings con referencia explícita a RF/BR.
- [ ] Type hints en `services.py` y `selectors.py`.
- [ ] Swagger/OpenAPI actualizado (`drf-spectacular`).
- [ ] README con instrucciones de setup, testing, deployment.

---

## 14. Alcance y Evolución

Esta arquitectura prepara el sistema para:

- Crecimiento de catalogo y volumen transaccional.
- Nuevos tipos de reportes e indicadores.
- Integraciones futuras (sin romper el nucleo de inventario).

No se adopta microservicios en esta fase para evitar complejidad operacional innecesaria.

Documentacion complementaria de este analisis:

- [docs/calidad_restricciones/README_RESTRICCIONES.md](calidad_restricciones/README_RESTRICCIONES.md)
- [docs/calidad_restricciones/README_ATRIBUTOS_CALIDAD.md](calidad_restricciones/README_ATRIBUTOS_CALIDAD.md)
- [docs/architecture/architecture_drivers.md](architecture_drivers.md)
- [docs/architecture/utility_tree.md](utility_tree.md)
- [docs/architecture/architectural_constraints.md](architectural_constraints.md)
- [docs/architecture/adr_relationships.md](adr_relationships.md)

## 15. Matriz de Trazabilidad Completa (RF -> Arquitectura)

| Requisito | Modulo funcional | Componentes tecnicos principales | Reglas de negocio asociadas |
| --- | --- | --- | --- |
| RF-001 | Autenticacion | `apps/authentication/views.py`, `apps/authentication/services.py`, `shared/permissions.py` | BR-01, BR-03 |
| RF-002 | Credenciales | `apps/authentication/services.py`, `apps/authentication/views.py`, `apps/audit/services.py` | BR-01, BR-02 |
| RF-003 | Catalogo | `apps/catalog/models.py`, `apps/catalog/services.py`, `apps/catalog/views.py` | BR-04, BR-12, BR-13 |
| RF-004 | Consulta inventario | `apps/inventory/selectors.py`, `apps/inventory/views.py`, `apps/inventory/models.py` | BR-11, BR-13, BR-14, BR-15 |
| RF-005 | Recepcion (entradas) | `apps/movements/services.py::register_entry`, `apps/movements/views.py`, `apps/inventory/models.py` | BR-04, BR-09, BR-10, BR-11, BR-13, BR-14 |
| RF-006 | Despacho/salidas | `apps/movements/services.py::register_dispatch`, `apps/catalog/services.py`, `apps/movements/models.py` | BR-08, BR-10, BR-11, BR-13, BR-14 |
| RF-007 | Traslados internos | `apps/movements/services.py::register_internal_transfer`, `apps/inventory/models.py` | BR-06, BR-10, BR-11, BR-14 |
| RF-008 | Devoluciones | `apps/movements/services.py::register_return`, `apps/movements/services.py::approve_return` | BR-02, BR-05, BR-10, BR-14 |
| RF-009 | Ajustes | `apps/movements/services.py::register_adjustment`, `apps/movements/services.py::correct_movement_within_window` | BR-06, BR-07, BR-10, BR-11, BR-14 |
| RF-010 | Reportes/KPI | `apps/reports/selectors.py`, `apps/reports/views.py` | BR-10, BR-11, BR-13 |
| RF-011 | Alertas | `apps/alerts/services.py`, `apps/alerts/models.py` | BR-04, BR-10, BR-11 |
| RF-012 | Auditoria | `apps/audit/models.py`, `apps/audit/services.py`, `apps/audit/views.py` | BR-01, BR-06, BR-07, BR-10 |

## 16. Matriz de Trazabilidad Completa (BR -> Implementacion)

| Regla de negocio | Implementacion arquitectonica | Verificacion |
| --- | --- | --- |
| BR-01 Identidad unica | Usuario autenticado + `executed_by` en movimientos + `user` en auditoria | Tests auth/audit y revision de campos obligatorios |
| BR-02 Gestion credenciales solo almacenista | Guardas de rol en `authentication/services.py` y permisos DRF | Tests de autorizacion por rol |
| BR-03 Restriccion horaria auxiliar | Validacion en login y permiso por request (`IsWithinOperatingHours`) | Tests de horario en servicios/permisos |
| BR-04 Serial obligatorio electroterapia | Validacion en `register_entry` y metadatos de catalogo | Tests de entrada sin serial |
| BR-05 Devolucion restringida | Validacion de categoria en `register_return` | Tests de devolucion bloqueada |
| BR-06 Ventana de autocorreccion | `correct_movement_within_window` con chequeo de franja/autor | Tests de correccion dentro/fuera de ventana |
| BR-07 Ajuste con justificacion | `register_adjustment` exige justificacion y rol almacenista | Tests de ajuste sin justificacion |
| BR-08 Validacion cruzada despacho | `register_dispatch` compara `scanned_code` contra `order_sku` | Tests de mismatch SKU |
| BR-09 Nota de discrepancia recepcion | `register_entry` exige nota cuando qty recibida != facturada | Tests de discrepancia sin nota |
| BR-10 Inmutabilidad de log | Sin PUT/DELETE de movimientos/auditoria + guardas de inmutabilidad en modelos | Tests de intentos de modificacion |
| BR-11 Stock por ubicacion | `StockByLocation` + traslados sin cambio global + ledger como fuente de verdad | Tests de consolidado y reconstruccion |
| BR-12 SKU definido por usuario | Validadores y reglas en `catalog/services.py` y `catalog/models.py` | Tests de SKU inválido |
| BR-13 Barcode alias + factura PDF | `resolve_identifier`, flujo fallback manual, numeracion secuencial y PDF en despacho | Tests de identificacion y facturacion |
| BR-14 Estado operativo de ubicacion | `_ensure_location_allows_origin` + `_ensure_location_allows_destination` en `movements/services.py` | Tests de estados archived, blocked, maintenance, restricted |
| BR-15 StorageType activo como requisito | Validacion en `create_location`/`update_location`; `StorageType.is_active` | Tests de tipo inactivo rechazado |

## 17. Matriz de Trazabilidad Completa (RNF -> Decisiones tecnicas)

| RNF | Decision de arquitectura | Evidencia tecnica |
| --- | --- | --- |
| RNF-001 Usabilidad | Contratos simples API REST + busqueda por multiples identificadores | Endpoints de catalog/inventory + autocompletado |
| RNF-002 Disponibilidad | Docker Compose, entrypoint con migraciones y health checks | `docker-compose.yml`, `docker/entrypoint.sh` |
| RNF-003 Seguridad e integridad | JWT, RBAC, restriccion horaria, auditoria inmutable, CORS/HTTPS | `shared/permissions.py`, settings JWT, app audit |
| RNF-004 Rendimiento | Selectores optimizados, agregaciones en BD, indices y locks | `inventory/selectors.py`, indices en modelos, `select_for_update` |
| RNF-005 Mantenibilidad | Separacion por capas, SOLID, OpenAPI, type hints y testing | Estructura modular + `/api/docs/` |
| RNF-006 Cumplimiento legal | Control de exposicion de datos personales y consentimiento en despacho | Campos cliente + `privacy_notice_acknowledged` |

Nota final de trazabilidad:

- Cada historia o cambio nuevo debe incluir referencia explicita a RF/BR/RNF impactados.
- Ningun cambio de logica de negocio se acepta sin actualizar esta matriz.
