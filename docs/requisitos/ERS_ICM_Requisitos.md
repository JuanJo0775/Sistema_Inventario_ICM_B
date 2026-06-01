**DOCUMENTO DE ESPECIFICACIÓN DE REQUISITOS DE SOFTWARE**

**Sistema de Gestión de Inventario y Operaciones**

Import Corporal Medical (ICM)

Proyecto Nuclear 3 — Corporación Universitaria Alexander von Humboldt

Período Académico I-2026

Versión 1.0 — Abril 2026

# **1. Introducción**

El presente documento constituye la Especificación de Requisitos de Software (ERS) para el sistema de gestión de inventario y operaciones de Import Corporal Medical (ICM), desarrollado en el marco del Proyecto Nuclear 3 de la Corporación Universitaria Alexander von Humboldt, período académico I-2026.

Este documento integra de forma estructurada y completa la totalidad de los requisitos funcionales y no funcionales levantados durante las sesiones de elicitación realizadas con los responsables operativos de ICM, en coordinación con los estudiantes de Ingeniería Industrial que participan como clientes funcionales y asesores del dominio logístico. Su propósito es servir como referencia unificada y autoritativa para los equipos de Arquitectura de Software I, Programación con Tecnologías Web y Pruebas de Software durante todas las fases del proyecto.

Cada requisito funcional está redactado siguiendo el estándar IEEE 830 adaptado al contexto académico del proyecto, con los siguientes campos: identificador único, nombre, módulo al que pertenece, descripción funcional completa, reglas de negocio aplicables y criterios de aceptación en formato Gherkin (Given/When/Then). Los requisitos no funcionales siguen la misma estructura, adaptando los criterios de aceptación a condiciones de calidad medibles y verificables. Los criterios en formato Gherkin han sido redactados con el objetivo explícito de facilitar la construcción directa de casos de prueba por parte de la asignatura de Pruebas de Software, sin necesidad de reinterpretación.

# **2. Contexto del Negocio**

Import Corporal Medical es una empresa importadora y distribuidora de insumos médicos especializados para fisioterapeutas. Su modelo de negocio se basa en la importación directa de productos desde fabricantes en China bajo la marca propia denominada "Can" (estrategia de Private Label), lo cual centraliza el catálogo bajo una única marca y facilita el control de calidad en la recepción de mercancía.

El catálogo activo de ICM comprende aproximadamente 220 productos distribuidos en tres macro-categorías: Electroterapia, Manoterapia y Mesas de Fisioterapia. La alta similitud morfológica entre algunos productos del mismo segmento genera errores recurrentes en el despacho cuando el proceso de selección es manual. Esta realidad convierte la validación cruzada entre pedido y producto físico en un requerimiento crítico del sistema.

La operación logística se distribuye en tres puntos de almacenamiento físico: una Vitrina destinada a la venta minorista y dos Bodegas Base orientadas al almacenamiento mayorista. ICM gestiona actualmente el inventario a través de hojas de cálculo, lo que genera brechas constantes entre el stock físico y el registro digital, imposibilita la trazabilidad nominal de los movimientos y limita la capacidad de respuesta ante consultas de clientes durante negociaciones comerciales.

# **3. Actores, Roles y Modelo de Acceso**

El sistema implementará un modelo de Control de Acceso Basado en Roles (RBAC) que garantiza la segregación de funciones y la trazabilidad de cada transacción hasta el usuario responsable. Se definen tres roles con permisos y restricciones horarias diferenciados, descritos en la siguiente tabla.

| **Rol** | **Responsabilidades Clave** | **Permisos** | **Restricción Horaria** |
| --- | --- | --- | --- |
| Almacenista (Coordinador) | Supervisión total, integridad del stock, gestión de maestros y credenciales, auditoría. | Visualización, edición, ajustes, gestión de credenciales, auditoría de logs. | Acceso 24/7 |
| Auxiliar de Despacho (2 cupos) | Ejecución de flujos de entrada, salida y movimientos internos entre almacenes. | Registro de movimientos, visualización de stock. | 07:00–12:00 / 14:00–17:00 |
| Administrador / Jefe | Monitoreo estratégico y análisis de indicadores operativos. | Visualización de stock, módulo de reportes y KPIs. Sin permisos de edición. | Acceso 24/7 (solo dashboard) |

# **4. Consolidación de Reglas de Negocio**

Las siguientes reglas de negocio fueron identificadas durante las sesiones de elicitación con ICM. Constituyen restricciones de obligatorio cumplimiento en el diseño, desarrollo y validación del sistema. Cada requisito funcional referencia explícitamente las reglas de negocio que le aplican.

* BR-01 (Identidad única): Está prohibido el uso de cuentas compartidas. Cada transacción registrada en el sistema debe estar vinculada de manera unívoca al identificador de usuario (UserID) del empleado que la ejecutó.
* BR-02 (Gestión de credenciales): El Almacenista es el único rol facultado para crear, editar o inhabilitar credenciales de acceso. Los perfiles de Auxiliar de Despacho no pueden ser modificados por ellos mismos.
* BR-03 (Restricción horaria para despacho): Los Auxiliares de Despacho solo pueden acceder al sistema en las franjas operativas 07:00–12:00 y 14:00–17:00. Fuera de estas ventanas, el sistema bloquea el acceso para ese rol.
* BR-04 (Obligatoriedad de serial en Electroterapia): El campo "Número de Serie" es mandatorio en toda entrada de productos de la categoría Electroterapia. El sistema no permite registrar la entrada si está vacío para esta categoría.
* BR-05 (Devoluciones restringidas): Solo los productos de la categoría Electroterapia o Electrónicos admiten devoluciones. El sistema bloquea automáticamente cualquier devolución de otro tipo de producto.
* BR-06 (Ventana de autocorrección): Un Auxiliar de Despacho puede editar un movimiento que registró dentro de la misma franja horaria activa. Al cerrar la franja, el registro se vuelve inmutable.
* BR-07 (Ajuste con justificación): Todo ajuste de inventario fuera de la ventana de autocorrección requiere justificación obligatoria y es ejecutado exclusivamente por el Almacenista.
* BR-08 (Validación cruzada en despacho): El sistema verifica que el código escaneado en el despacho coincida con el SKU de la orden antes de confirmar la salida. Si no coincide, bloquea la operación.
* BR-09 (Nota de discrepancia en recepción): Si la cantidad recibida difiere de la facturada, el operario debe registrar una nota de discrepancia antes de confirmar la entrada.
* BR-10 (Inmutabilidad del log): Los registros históricos de movimientos, ajustes, devoluciones y auditorías no pueden ser eliminados ni modificados por ningún usuario.
* BR-11 (Stock por ubicación): El stock total es la sumatoria dinámica de las cantidades en Vitrina, Bodega 1 y Bodega 2. Los traslados internos no modifican el stock total global.
* BR-12 (SKU definido por usuario): El SKU es asignado por el usuario y debe seguir el patrón 1–4 letras, un guion, y 1–4 dígitos (ej: `AB-1234`). No es obligatorio aplicar un prefijo específico.
* BR-13 (Código de barras como alias de escaneo y factura digital): Cada producto puede tener registrado un código de barras físico como alias de escaneo. La ausencia del lector físico no debe bloquear ningún flujo del sistema. Todo despacho confirmado genera automáticamente una factura digital con numeración secuencial, almacenada de forma persistente y descargable en PDF.
* BR-14 (Estado operativo de ubicación restringe movimientos): El estado operativo de una ubicación determina qué operaciones de stock puede ejecutar. Las ubicaciones en estado `archived` o `blocked` no admiten ningún movimiento de entrada ni salida. Las ubicaciones en estado `maintenance` o `restricted` no pueden operar como origen de despachos, traslados o ajustes de reducción, pero sí pueden recibir stock como destino. Solo el Almacenista puede cambiar el estado operativo de una ubicación. Esta restricción es informativa respecto a la capacidad, pero operativa y no negociable respecto al estado.
* BR-15 (Tipo de almacenamiento activo como requisito de asignación): Un tipo de almacenamiento (`StorageType`) con estado inactivo no puede asignarse a nuevas ubicaciones ni reasignarse a ubicaciones existentes. La desactivación de un tipo no afecta las ubicaciones que ya lo tenían asignado, las cuales conservan su tipo sin restricción adicional. Solo el Almacenista puede crear, modificar o desactivar tipos de almacenamiento y plantillas de configuración.
* BR-16 (Precio congelado en despacho): Al confirmar un despacho, el sistema captura el precio unitario de venta, el costo unitario, el IVA aplicable y el total calculado en el registro de movimiento de forma permanente e inmutable. Ninguna modificación posterior al precio de un producto en el catálogo puede alterar el precio registrado en movimientos o facturas ya emitidas. Esta regla garantiza la integridad contable del historial de transacciones.
* BR-17 (Historial auditado de cambios de precio): Toda actualización de precio de un producto (precio minorista, precio mayorista, costo o tasa de IVA) debe registrarse de forma inmutable en un historial de precios que identifique el campo modificado, el valor anterior, el nuevo valor, el usuario que realizó el cambio y la fecha y hora exacta. El historial de precios es de solo lectura y no puede ser eliminado ni modificado.

# **5. Requisitos Funcionales**

A continuación se presentan los dieciocho requisitos que componen la especificación completa del sistema, organizados por módulo. Los requisitos funcionales (RF) describen los comportamientos específicos que el sistema debe exhibir ante determinadas condiciones de operación. Cada criterio de aceptación está redactado en formato Gherkin para facilitar su uso directo en la construcción de casos de prueba.

## **RF-001 — Inicio de Sesión con Credenciales Únicas**

**Módulo:** Autenticación y Gestión de Credenciales

**Descripción**

El sistema debe permitir que cada usuario acceda a la plataforma mediante un nombre de usuario y contraseña únicos y personales. Una vez autenticado exitosamente, el sistema debe redirigir automáticamente al usuario a la vista correspondiente a su rol (Almacenista, Auxiliar de Despacho o Administrador/Jefe). Ningún usuario podrá acceder a funcionalidades fuera del alcance de su rol.

**Reglas de Negocio Aplicables**

* BR-01: Está prohibido el uso de cuentas compartidas. Cada transacción debe estar vinculada a un UserID único e irrepetible.
* BR-03: Los Auxiliares de Despacho solo pueden acceder al sistema en las franjas horarias 07:00–12:00 y 14:00–17:00. Fuera de esas ventanas, el sistema bloquea el acceso para ese rol.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Inicio de sesión con credenciales únicas

### Scenario 1: Inicio de sesión exitoso como Almacenista

**Given (Dado que):**
- El usuario tiene un rol de "Almacenista"
- Sus credenciales están activas en el sistema

**When (Cuando):**
- Ingresa su nombre de usuario y contraseña correctos
- Hace clic en "Iniciar sesión"

**Then (Entonces):**
- El sistema autentica al usuario correctamente
- Lo redirige al dashboard del Almacenista
- Registra el evento de inicio de sesión con el UserID y timestamp exacto

---

### Scenario 2: Inicio de sesión exitoso como Auxiliar de Despacho dentro del horario permitido

**Given (Dado que):**
- El usuario tiene rol "Auxiliar de Despacho"
- La hora actual está dentro de la franja 07:00–12:00 o 14:00–17:00
- Sus credenciales están activas

**When (Cuando):**
- Ingresa sus credenciales correctas y hace clic en "Iniciar sesión"

**Then (Entonces):**
- El sistema lo autentica y redirige a la vista del Auxiliar de Despacho

---

### Scenario 3: Intento de inicio de sesión de Auxiliar fuera del horario permitido

**Given (Dado que):**
- El usuario tiene rol "Auxiliar de Despacho"
- La hora actual está fuera de las franjas 07:00–12:00 y 14:00–17:00

**When (Cuando):**
- Ingresa sus credenciales correctas y hace clic en "Iniciar sesión"

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que su horario de acceso no está activo
- No genera sesión ni redirige a ninguna vista

---

### Scenario 4: Intento de inicio de sesión con credenciales incorrectas

**Given (Dado que):**
- Existe un usuario registrado en el sistema

**When (Cuando):**
- Ingresa una contraseña o nombre de usuario incorrecto

**Then (Entonces):**
- El sistema rechaza el acceso
- Muestra un mensaje de error genérico sin revelar si el fallo fue en usuario o contraseña
- No genera sesión activa

---

### Scenario 5: Inicio de sesión como Administrador fuera del horario laboral

**Given (Dado que):**
- El usuario tiene rol "Administrador/Jefe"
- La hora actual es fuera del horario laboral convencional

**When (Cuando):**
- Ingresa sus credenciales correctas

**Then (Entonces):**
- El sistema lo autentica sin restricción horaria
- Lo redirige al dashboard gerencial de solo lectura

## **RF-002 — Gestión de Credenciales de Usuario**

**Módulo:** Autenticación y Gestión de Credenciales

**Descripción**

El sistema debe permitir que el Almacenista, y únicamente él, pueda crear nuevas cuentas de usuario, asignar roles, modificar contraseñas y deshabilitar accesos cuando sea necesario. Los Auxiliares de Despacho no pueden modificar sus propios perfiles ni los de otros usuarios. Cuando una cuenta es deshabilitada, cualquier sesión activa de ese usuario debe terminarse de inmediato.

**Reglas de Negocio Aplicables**

* BR-01: Cada cuenta debe estar vinculada a un UserID único. No se permiten cuentas compartidas.
* BR-02: Solo el Almacenista puede crear, editar o inhabilitar credenciales. Los Auxiliares de Despacho no pueden modificar perfiles propios ni ajenos.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Gestión de credenciales de usuario

### Scenario 1: Almacenista crea una nueva cuenta de usuario

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al módulo de gestión de credenciales
- Completa el formulario con nombre de usuario, contraseña temporal y rol asignado
- Hace clic en "Crear usuario"

**Then (Entonces):**
- El sistema crea la cuenta con un UserID único e irrepetible
- La cuenta queda activa y asociada al rol seleccionado
- El evento de creación queda registrado en el log de auditoría con el UserID del Almacenista y el timestamp

---

### Scenario 2: Almacenista modifica la contraseña de un usuario existente

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una cuenta activa en el sistema

**When (Cuando):**
- Selecciona la cuenta y elige la opción "Modificar contraseña"
- Ingresa la nueva contraseña y confirma la acción

**Then (Entonces):**
- El sistema actualiza la contraseña de la cuenta seleccionada
- El cambio queda registrado en el log de auditoría con UserID del Almacenista y timestamp

---

### Scenario 3: Almacenista deshabilita una cuenta activa

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una cuenta de usuario activa en el sistema

**When (Cuando):**
- Selecciona la cuenta y elige la opción "Deshabilitar"
- Confirma la acción

**Then (Entonces):**
- El sistema deshabilita la cuenta inmediatamente
- Si el usuario tenía una sesión activa, ésta se termina en ese momento
- El usuario deshabilitado no puede iniciar sesión hasta que el Almacenista reactive la cuenta
- El evento queda registrado en el log de auditoría

---

### Scenario 4: Auxiliar de Despacho intenta modificar su propio perfil

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder a cualquier opción de edición de credenciales propias o ajenas

**Then (Entonces):**
- El sistema bloquea la acción
- Muestra un mensaje indicando que no tiene permisos para realizar esa operación
- No realiza ningún cambio en el sistema

---

### Scenario 5: Intento de crear una cuenta con un nombre de usuario ya existente

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Ya existe una cuenta con el nombre de usuario "auxiliar01" en el sistema

**When (Cuando):**
- Intenta crear una nueva cuenta con el mismo nombre de usuario "auxiliar01"

**Then (Entonces):**
- El sistema rechaza la creación
- Muestra un mensaje indicando que el nombre de usuario ya está en uso
- No genera ninguna cuenta duplicada

## **RF-003 — Registro de Producto en el Catálogo (SKU)**

**Módulo:** Gestión de Inventario

**Descripción**

  El sistema debe permitir al Almacenista crear nuevos productos en el catálogo del sistema, registrando todos los atributos necesarios para su gestión logística, de calidad y de trazabilidad. Cada producto queda identificado de forma unívoca por un SKU generado o asignado en el momento de su creación. El SKU debe ser definido por el usuario y cumplir el patrón 1–4 letras, un guion y 1–4 dígitos. El sistema debe soportar además la agrupación de múltiples SKUs bajo un identificador de Combo o Kit para el despacho simultáneo de paquetes de terapia como una sola unidad de salida.

**Reglas de Negocio Aplicables**

* BR-04: El campo "Número de Serie" es mandatorio para toda entrada de productos de la categoría Electroterapia, por lo que debe existir como atributo registrable desde la creación del producto.
* BR-11: El stock se gestiona por ubicación (Vitrina, Bodega 1, Bodega 2). El stock total es la sumatoria dinámica de los tres puntos.
* BR-12: El SKU debe ser definido por el usuario y seguir el patrón 1–4 letras, un guion y 1–4 dígitos. No es obligatorio aplicar un prefijo específico.
* BR-13: Cada producto puede tener registrado un código de barras físico como atributo adicional que actúa como alias de escaneo, sin reemplazar al SKU ni a ningún otro identificador.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Registro de producto en el catálogo

### Scenario 1: Almacenista registra un producto nuevo con todos los atributos obligatorios

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al formulario de creación de producto
- Completa todos los campos obligatorios: nombre, categoría, subcategoría, código de barras, fecha de vencimiento, peso unitario y punto de reorden
- Hace clic en "Guardar producto"

**Then (Entonces):**
- El sistema crea el producto con un SKU único
- Lo registra en el catálogo con stock inicial en cero para cada ubicación
- El evento de creación queda en el log de auditoría con UserID y timestamp

---

### Scenario 2: Registro de producto de marca propia "Can"

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto indicando que pertenece a la marca propia "Can"

**Then (Entonces):**
- El sistema acepta el SKU proporcionado por el usuario siempre que cumpla el patrón 1–4 letras, un guion y 1–4 dígitos
- No permite guardar el producto si el SKU no cumple el formato requerido

---

### Scenario 3: Registro de producto de categoría Electroterapia

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto con categoría "Electroterapia"

**Then (Entonces):**
- El sistema habilita y marca como obligatorio el campo "Número de Serie"
- No permite guardar el producto si ese campo está vacío

---

### Scenario 4: Registro de producto con código de barras como alias de escaneo

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto e ingresa un código de barras en el campo correspondiente

**Then (Entonces):**
- El sistema almacena el código como atributo adicional del producto
- Lo vincula internamente al SKU sin reemplazarlo
- Cuando ese código sea escaneado o ingresado manualmente en cualquier módulo, el sistema resuelve la correspondencia al SKU correcto

---

### Scenario 5: Registro de producto que requiere cadena de frío

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto y activa el indicador de "Cadena de frío"

**Then (Entonces):**
- El sistema almacena esa condición especial en la ficha del producto
- Desplegará una alerta visual persistente en cualquier módulo donde ese producto sea manipulado

---

### Scenario 6: Creación de un Combo o Kit con múltiples SKUs

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existen al menos dos productos registrados en el catálogo

**When (Cuando):**
- Crea un nuevo ítem de tipo "Combo" y asocia dos o más SKUs existentes

**Then (Entonces):**
- El sistema registra el Combo con un identificador propio
- Permite despacharlo como una sola unidad de salida
- Al confirmar un despacho de ese Combo, descuenta el stock de cada SKU componente en sus respectivas ubicaciones

---

### Scenario 7: Intento de guardar un producto sin completar campos obligatorios

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Intenta guardar un producto dejando uno o más campos obligatorios vacíos

**Then (Entonces):**
- El sistema rechaza el guardado
- Señala visualmente los campos faltantes
- No crea ningún registro parcial en el catálogo

## **RF-004 — Consulta y Búsqueda de Inventario en Tiempo Real**

**Módulo:** Gestión de Inventario

**Descripción**

El sistema debe ofrecer una interfaz de consulta del estado actual del stock que permita al usuario navegar el catálogo mediante filtros dinámicos multinivel, desde la categoría general hasta el SKU específico. La búsqueda debe ser accesible tanto por código de barras o SKU como por nombre con autocompletado, de modo que ambas vías sean igualmente eficientes. El sistema debe mostrar el stock desagregado por ubicación (Vitrina, Bodega 1, Bodega 2) y el stock total consolidado. Esta funcionalidad es crítica durante la atención al cliente en negociaciones comerciales, donde el vendedor necesita consultar disponibilidad en tiempo real sin interrumpir el flujo de conversación.

Adicionalmente, el sistema extiende el dominio de almacenamiento con tipos configurables (`StorageType`) que clasifican las ubicaciones (bodega grande, vitrina, cuarto frío, etc.) y plantillas reutilizables (`StorageTemplate`) que permiten crear ubicaciones con parámetros predefinidos. Cada ubicación tiene un estado operativo formal que determina qué operaciones de stock puede realizar. La capacidad relativa de cada ubicación es informativa y no bloquea movimientos. El almacenista puede consultar el inventario filtrado por tipo de ubicación, estado operativo o categoría de producto, y los reportes de utilización presentan distribución por tipo de almacenamiento y por estado.

**Reglas de Negocio Aplicables**

* BR-11: El stock total es la sumatoria dinámica de las cantidades registradas en Vitrina, Bodega 1 y Bodega 2. Debe reflejar el estado real en todo momento.
* BR-13: El código de barras actúa como alias de escaneo que el sistema resuelve internamente al SKU correspondiente, permitiendo búsquedas por esa vía de forma equivalente a cualquier otra.
* BR-14: El estado operativo de la ubicación (active, maintenance, restricted, blocked, archived) determina si puede operar como origen o destino de movimientos. Ver detalle en BR-14.
* BR-15: Un StorageType desactivado no puede asignarse a nuevas ubicaciones ni reasignarse a las existentes. Ver detalle en BR-15.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Consulta y búsqueda de inventario en tiempo real

### Scenario 1: Consulta de stock navegando por filtros multinivel

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Selecciona una categoría (por ejemplo "Electroterapia")
- Luego selecciona una subcategoría (por ejemplo "Agujas de Punción Seca")

**Then (Entonces):**
- El sistema muestra únicamente los productos que corresponden a esa combinación de categoría y subcategoría
- Para cada producto despliega el stock disponible en Vitrina, Bodega 1, Bodega 2 y el total consolidado

---

### Scenario 2: Búsqueda de producto por nombre con autocompletado

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Escribe al menos tres caracteres del nombre de un producto en el campo de búsqueda

**Then (Entonces):**
- El sistema despliega en tiempo real una lista de sugerencias que coinciden con los caracteres ingresados
- Al seleccionar un producto de la lista, muestra su ficha con el stock por ubicación y el total consolidado

---

### Scenario 3: Búsqueda de producto por código de barras escaneado

**Given (Dado que):**
- El usuario está autenticado con cualquier rol
- Hay un lector de código de barras conectado en modo HID

**When (Cuando):**
- Escanea el código de barras impreso en el empaque de un producto

**Then (Entonces):**
- El sistema resuelve el código al SKU interno correspondiente
- Muestra la ficha del producto con su stock por ubicación y el total consolidado en menos de 2 segundos

---

### Scenario 4: Búsqueda de producto por código de barras ingresado manualmente

**Given (Dado que):**
- El usuario está autenticado con cualquier rol
- No hay un lector de código de barras disponible

**When (Cuando):**
- Escribe manualmente el código de barras en el campo de búsqueda

**Then (Entonces):**
- El sistema resuelve el código al SKU interno correspondiente
- Muestra la misma ficha y resultado que si hubiera sido escaneado

---

### Scenario 5: Consulta de producto con alerta de cadena de frío

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Consulta un producto que tiene activado el indicador de cadena de frío

**Then (Entonces):**
- El sistema despliega una alerta visual persistente y de alta visibilidad junto a la ficha del producto
- Recuerda las condiciones especiales de manejo

---

### Scenario 6: Consulta de producto con alerta de seguridad eléctrica

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Consulta un producto de la categoría Electroterapia

**Then (Entonces):**
- El sistema despliega una advertencia visual sobre los protocolos de manejo seguro aplicables a equipos eléctricos

---

### Scenario 7: Búsqueda de un producto inexistente en el catálogo

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Realiza una búsqueda por nombre, SKU o código de barras que no corresponde a ningún producto registrado

**Then (Entonces):**
- El sistema muestra un mensaje claro indicando que no se encontraron resultados para ese criterio de búsqueda
- No genera ningún error ni interrupción en la interfaz

---

### Scenario 8: Crear tipo de almacenamiento y asignarlo a una ubicación

**Given (Dado que):**
- El usuario autenticado tiene rol Almacenista

**When (Cuando):**
- Crea un StorageType con code=bodega-grande, name=Bodega Grande y category=warehouse
- Crea una Location indicando el storage_type_id del paso anterior

**Then (Entonces):**
- Ambas peticiones retornan HTTP 201
- La ubicación expone storage_type_code=bodega-grande en su respuesta

---

### Scenario 9: Tipo de almacenamiento inactivo rechazado al crear ubicación

**Given (Dado que):**
- Existe un StorageType que fue desactivado por el Almacenista (is_active=False)

**When (Cuando):**
- El Almacenista intenta crear una ubicación asignando ese storage_type_id

**Then (Entonces):**
- El sistema retorna HTTP 400 o 422
- El mensaje de error indica que el tipo de almacenamiento está inactivo y no puede asignarse

---

### Scenario 10: Plantilla de almacenamiento aplica defaults al crear ubicación

**Given (Dado que):**
- Existe una StorageTemplate activa con defaults: max_capacity=40, capacity_mode=relative_scale, capacity_level=2

**When (Cuando):**
- El Almacenista crea una ubicación indicando únicamente el storage_template_id

**Then (Entonces):**
- El sistema retorna HTTP 201
- La ubicación hereda max_capacity=40, capacity_mode=relative_scale y capacity_level=2 desde la plantilla
- El storage_type de la plantilla queda asignado a la ubicación si la plantilla lo tenía configurado

---

### Scenario 11: Transición a estado mantenimiento bloquea despacho desde esa ubicación

**Given (Dado que):**
- Existe una ubicación activa con stock disponible de un producto

**When (Cuando):**
- El Almacenista transiciona la ubicación al estado maintenance via el endpoint de transiciones de estado
- Luego se intenta registrar un despacho de stock desde esa ubicación

**Then (Entonces):**
- La transición retorna HTTP 200 con operational_status=maintenance e is_active=true
- El despacho retorna HTTP 422 con código de error LOCATION_STATE_NOT_ALLOWED
- El stock de la ubicación no se modifica

---

### Scenario 12: Archivar una ubicación fuerza is_active=False

**Given (Dado que):**
- Existe una ubicación activa

**When (Cuando):**
- El Almacenista transiciona la ubicación al estado archived

**Then (Entonces):**
- El sistema retorna HTTP 200
- La respuesta muestra operational_status=archived e is_active=false
- La ubicación no aparece en listados de ubicaciones activas

---

### Scenario 13: Ubicación archivada rechaza entradas de stock

**Given (Dado que):**
- Existe una ubicación con estado archived

**When (Cuando):**
- Se intenta registrar una entrada de mercancía hacia esa ubicación

**Then (Entonces):**
- El sistema retorna HTTP 422 con código LOCATION_STATE_NOT_ALLOWED
- El stock de la ubicación no cambia

---

### Scenario 14: Ubicación restringida bloquea despacho pero permite entrada

**Given (Dado que):**
- Existe una ubicación con estado restricted y con stock disponible de un producto

**When (Cuando):**
- Se intenta registrar un despacho de stock desde esa ubicación (debe fallar)
- Se intenta registrar una entrada de stock hacia esa ubicación (debe funcionar)

**Then (Entonces):**
- El despacho retorna HTTP 422 con código LOCATION_STATE_NOT_ALLOWED
- La entrada retorna HTTP 201 y el stock de la ubicación incrementa correctamente

---

### Scenario 15: Capacidad relativa se guarda y se expone en la ubicación y en reportes

**Given (Dado que):**
- El Almacenista va a configurar una ubicación con escala relativa de capacidad

**When (Cuando):**
- Crea la ubicación con capacity_mode=relative_scale, capacity_level=3 y capacity_score=30

**Then (Entonces):**
- El sistema retorna HTTP 201 con esos campos en la respuesta
- El endpoint GET /api/v1/reports/warehouse-utilization/ incluye esa ubicación con capacity_level=3 en by_location
- La capacidad relativa es informativa y no bloquea movimientos

---

### Scenario 16: Filtro de inventario por storage_type_id muestra solo productos de ese tipo

**Given (Dado que):**
- Existen dos tipos de almacenamiento (Tipo A y Tipo B) con ubicaciones y stock de productos distintos en cada uno

**When (Cuando):**
- Se consulta GET /api/v1/inventory/?storage_type_id=<id_tipo_A>

**Then (Entonces):**
- Solo aparecen productos que tienen stock en ubicaciones del Tipo A
- Productos exclusivos del Tipo B no aparecen en la respuesta

---

### Scenario 17: Filtro de inventario por estado operativo muestra solo ubicaciones en ese estado

**Given (Dado que):**
- Una ubicación con estado active y una con estado maintenance, ambas con stock del mismo producto

**When (Cuando):**
- Se consulta GET /api/v1/inventory/?operational_status=maintenance

**Then (Entonces):**
- Solo aparece el producto con stock en la ubicación en mantenimiento
- La ubicación activa no influye en los resultados

---

### Scenario 18: Reporte de utilización agrupa ubicaciones por tipo de almacenamiento

**Given (Dado que):**
- Existen dos ubicaciones asignadas al mismo StorageType, cada una con stock registrado

**When (Cuando):**
- Se consulta GET /api/v1/reports/warehouse-utilization/

**Then (Entonces):**
- La sección by_storage_type contiene un bucket para ese tipo con locations=2 y occupied_units igual a la suma del stock de ambas ubicaciones
- La sección by_operational_status contiene un bucket correspondiente al estado operativo de esas ubicaciones

## **RF-005 — Recepción de Mercancía (Entradas al Inventario)**

**Módulo:** Recepción de Mercancía

**Descripción**

El sistema debe gestionar el ingreso de productos al inventario, ya sea por compra a proveedor externo o por reposición de marca propia. El flujo de recepción debe permitir identificar el producto mediante escaneo de código de barras o búsqueda por nombre, registrar la cantidad recibida comparándola contra la cantidad facturada o esperada, exigir el número de serie para productos de Electroterapia, seleccionar la ubicación de destino, y generar el movimiento de inventario correspondiente con trazabilidad completa. Si existe discrepancia entre la cantidad recibida y la facturada, el sistema debe obligar al operario a registrar una nota explicativa antes de confirmar la entrada.

**Reglas de Negocio Aplicables**

* BR-04: El campo "Número de Serie" es mandatorio en toda entrada de productos de la categoría Electroterapia. El sistema no permite confirmar la entrada si está vacío para esa categoría.
* BR-09: Si la cantidad recibida difiere de la facturada, el operario debe registrar una nota de discrepancia antes de confirmar la entrada.
* BR-10: El registro del movimiento de entrada es inmutable una vez confirmado. Cualquier corrección posterior debe tramitarse como ajuste formal.
* BR-11: El stock se actualiza por ubicación. El stock total es la sumatoria dinámica de Vitrina, Bodega 1 y Bodega 2.
* BR-13: El código de barras actúa como alias de escaneo que el sistema resuelve internamente al SKU, sin reemplazarlo.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Recepción de mercancía al inventario

### Scenario 1: Recepción exitosa de producto estándar sin discrepancia

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catálogo
- La hora actual está dentro de la franja horaria permitida

**When (Cuando):**
- Inicia un registro de entrada
- Selecciona el producto por escaneo de código de barras o búsqueda por nombre
- Ingresa la cantidad recibida igual a la cantidad facturada
- Selecciona la ubicación de destino (Vitrina, Bodega 1 o Bodega 2)
- Confirma la entrada

**Then (Entonces):**
- El sistema incrementa el stock del producto en la ubicación seleccionada
- Recalcula el stock total consolidado
- Genera un movimiento de entrada inmutable con UserID, timestamp, ubicación de destino, cantidad, stock previo y stock resultante

---

### Scenario 2: Recepción con discrepancia entre cantidad recibida y facturada

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catálogo

**When (Cuando):**
- Ingresa una cantidad recibida diferente a la cantidad facturada o esperada
- Intenta confirmar la entrada sin registrar una nota de discrepancia

**Then (Entonces):**
- El sistema bloquea la confirmación
- Muestra un mensaje indicando que es obligatorio registrar una nota que explique la diferencia
- No genera ningún movimiento hasta que la nota sea completada

---

### Scenario 3: Recepción exitosa con discrepancia documentada

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- La cantidad recibida difiere de la facturada

**When (Cuando):**
- Registra la nota de discrepancia obligatoria
- Confirma la entrada

**Then (Entonces):**
- El sistema acepta la operación
- Genera el movimiento de entrada vinculando la nota de discrepancia al registro
- El movimiento queda inmutable con todos los atributos de trazabilidad

---

### Scenario 4: Recepción de producto de categoría Electroterapia sin número de serie

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto seleccionado pertenece a la categoría "Electroterapia"

**When (Cuando):**
- Completa el formulario de entrada dejando vacío el campo "Número de Serie"
- Intenta confirmar la entrada

**Then (Entonces):**
- El sistema bloquea la confirmación
- Muestra un mensaje indicando que el número de serie es obligatorio para productos de Electroterapia
- No genera ningún movimiento ni actualización de stock

---

### Scenario 5: Recepción exitosa de producto de Electroterapia con número de serie

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto pertenece a la categoría "Electroterapia"

**When (Cuando):**
- Ingresa el número de serie de cada unidad recibida
- Completa los demás campos obligatorios y confirma la entrada

**Then (Entonces):**
- El sistema registra cada unidad vinculada a su número de serie individual
- Actualiza el stock en la ubicación de destino seleccionada
- Genera el movimiento con trazabilidad completa incluyendo los seriales

---

### Scenario 6: Identificación del producto por código de barras escaneado durante recepción

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Hay un lector de código de barras conectado en modo HID

**When (Cuando):**
- Escanea el código de barras del producto a recepcionar

**Then (Entonces):**
- El sistema resuelve el código al SKU interno
- Autocompleta el formulario con el nombre, categoría y demás atributos del producto
- El operario solo debe completar cantidad, ubicación y los campos variables de esa entrada

---

### Scenario 7: Recepción cuando el lector de código de barras no está disponible

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El lector de código de barras no está conectado o no es reconocido

**When (Cuando):**
- El sistema detecta la ausencia del lector

**Then (Entonces):**
- Muestra una notificación visible informando que el lector no está disponible
- Permite continuar el flujo de recepción mediante búsqueda por nombre, ingreso manual del código de barras o ingreso directo del SKU
- No interrumpe ni bloquea el proceso de entrada bajo ninguna circunstancia

## **RF-006 — Despacho y Salidas de Inventario**

**Módulo:** Despacho y Salidas

**Descripción**

El sistema debe gestionar todos los egresos de productos desde el inventario de ICM. Cada salida debe clasificarse obligatoriamente en una de cuatro categorías: Venta al por Mayor, Venta al por Menor, Daño o Vencimiento, ya que cada tipo tiene implicaciones distintas en la auditoría y los reportes. El mecanismo central de seguridad de este módulo es la validación cruzada: antes de confirmar cualquier despacho, el sistema debe verificar que el código escaneado físicamente coincida con el SKU de la orden, bloqueando la operación si no hay coincidencia. Esto previene el error más crítico identificado en ICM durante la elicitación: el despacho de un producto por otro morfológicamente similar. Una vez confirmado el despacho, el sistema genera automáticamente una factura o remisión digital en PDF con numeración secuencial.

**Reglas de Negocio Aplicables**

* BR-08: El sistema verifica que el código escaneado en el despacho coincida con el SKU de la orden antes de confirmar la salida. Si no coincide, bloquea la operación y muestra un mensaje de error descriptivo.
* BR-10: El registro del movimiento de salida es inmutable una vez confirmado.
* BR-11: El stock se descuenta por ubicación. El stock total es la sumatoria dinámica de los tres puntos de almacenamiento.
* BR-13: El código de barras actúa como alias de escaneo. La ausencia del lector no debe bloquear el flujo de despacho bajo ninguna circunstancia. Todo despacho confirmado genera automáticamente una factura digital con numeración secuencial almacenada de forma persistente.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Despacho y salidas de inventario

### Scenario 1: Despacho exitoso de venta al por mayor con validación cruzada

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existe una orden de despacho con uno o más productos
- El stock disponible en la ubicación de origen es suficiente

**When (Cuando):**
- Selecciona el tipo de salida "Venta al por Mayor"
- Registra los datos completos del cliente receptor (nombre o razón social, correo, teléfono, dirección)
- Escanea o ingresa el código del producto a despachar
- El código coincide con el SKU de la orden
- Confirma el despacho

**Then (Entonces):**
- El sistema descuenta el stock del producto en la ubicación de origen
- Recalcula el stock total consolidado
- Genera un movimiento de salida inmutable con UserID, timestamp, tipo de salida, cliente, SKU, cantidad, ubicación de origen, stock previo y stock resultante
- Genera automáticamente una factura digital en PDF con numeración secuencial que incluye todos los datos del despacho
- La factura queda almacenada de forma persistente en el historial

---

### Scenario 2: Validación cruzada falla por código escaneado incorrecto

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existe una orden de despacho para el SKU "ELEC-0001"

**When (Cuando):**
- Escanea físicamente un producto cuyo código corresponde a un SKU diferente

**Then (Entonces):**
- El sistema bloquea la confirmación del despacho
- Muestra un mensaje de error descriptivo indicando que el producto escaneado no corresponde al producto de la orden
- No genera ningún movimiento ni descuento de stock
- No genera factura hasta que la validación sea superada

---

### Scenario 3: Despacho de venta al por menor sin registro obligatorio de cliente

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona el tipo de salida "Venta al por Menor"
- Completa el formulario sin registrar datos del cliente
- La validación cruzada del producto es exitosa
- Confirma el despacho

**Then (Entonces):**
- El sistema acepta la operación sin exigir datos del cliente
- Genera el movimiento de salida con trazabilidad completa
- Genera la factura o remisión digital en PDF

---

### Scenario 4: Registro de baja por daño

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona el tipo de salida "Daño"
- Ingresa el número de unidades afectadas
- Registra una nota descriptiva del daño detectado
- Confirma la operación

**Then (Entonces):**
- El sistema descuenta las unidades del stock en la ubicación correspondiente
- Registra el movimiento como "baja por daño", no como venta
- La nota descriptiva queda vinculada de forma inmutable al movimiento
- Genera el documento de remisión en PDF reflejando el tipo de baja

---

### Scenario 5: Registro de baja por vencimiento

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existen productos con alertas de vencimiento activas

**When (Cuando):**
- Selecciona el tipo de salida "Vencimiento"
- Selecciona el producto y el lote afectado
- Confirma la operación

**Then (Entonces):**
- El sistema descuenta las unidades del stock en la ubicación correspondiente
- Registra el movimiento como "baja por vencimiento"
- Vincula la fecha de vencimiento del lote al registro del movimiento
- El movimiento queda inmutable con trazabilidad completa

---

### Scenario 6: Advertencia por peso total del despacho excede capacidad del vehículo

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El tipo de salida es "Venta al por Mayor"
- El sistema tiene configurada la capacidad máxima del vehículo de transporte

**When (Cuando):**
- El peso total calculado de todos los ítems del despacho supera la capacidad máxima configurada

**Then (Entonces):**
- El sistema emite una advertencia visible al operario indicando que la carga excede la capacidad del vehículo
- Permite al operario revisar y ajustar el despacho
- No bloquea la operación de forma definitiva, ya que la decisión final corresponde al operario responsable

---

### Scenario 7: Despacho cuando el lector de código de barras no está disponible

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El lector de código de barras no está conectado o no es reconocido

**When (Cuando):**
- El sistema detecta la ausencia del lector

**Then (Entonces):**
- Muestra una notificación visible pero no interrumpe el flujo de despacho
- Permite al operario identificar el producto ingresando manualmente el código de barras, el SKU, el código serial o buscando por nombre
- La validación cruzada se ejecuta igualmente usando el valor ingresado

## **RF-007 — Movimientos Internos entre Ubicaciones**

**Módulo:** Movimientos Internos

**Descripción**

El sistema debe permitir registrar traslados de productos entre los tres puntos de almacenamiento de ICM (Vitrina, Bodega 1 y Bodega 2) sin que ello implique una venta ni una salida definitiva de la empresa. Este tipo de operación actualiza únicamente la distribución del stock entre ubicaciones: resta la cantidad de la ubicación de origen y la suma en la ubicación de destino, pero el stock total global de ICM permanece inalterado. Antes de confirmar cualquier traslado, el sistema debe validar que la ubicación de origen tenga stock suficiente para cubrir la cantidad solicitada, impidiendo que se genere stock negativo en ningún punto de almacenamiento.

**Reglas de Negocio Aplicables**

* BR-10: El registro del movimiento de traslado es inmutable una vez confirmado. Cualquier corrección posterior debe tramitarse como ajuste formal por el Almacenista.
* BR-11: Los traslados internos no modifican el stock total global de ICM. El stock total es siempre la sumatoria dinámica de las cantidades en Vitrina, Bodega 1 y Bodega 2.
* BR-06: Si el traslado fue registrado por un Auxiliar de Despacho y se detecta un error dentro de la misma franja horaria activa, el auxiliar puede editar el registro antes de que se cierre la ventana. Una vez cerrada, el registro queda inmutable.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Movimientos internos entre ubicaciones de almacenamiento

### Scenario 1: Traslado exitoso de producto entre ubicaciones con stock suficiente

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catálogo
- La ubicación de origen tiene stock suficiente para cubrir la cantidad a trasladar

**When (Cuando):**
- Selecciona el producto a trasladar
- Indica la cantidad, la ubicación de origen y la ubicación de destino
- Confirma el traslado

**Then (Entonces):**
- El sistema resta la cantidad indicada del stock en la ubicación de origen
- Suma esa misma cantidad al stock en la ubicación de destino
- El stock total global del producto permanece sin cambios
- Genera un movimiento inmutable con UserID, timestamp, producto, cantidad, ubicación de origen, ubicación de destino, stock previo y stock resultante por ubicación

---

### Scenario 2: Intento de traslado con stock insuficiente en la ubicación de origen

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto tiene 3 unidades disponibles en Bodega 1

**When (Cuando):**
- Intenta registrar un traslado de 5 unidades desde Bodega 1 hacia cualquier otra ubicación

**Then (Entonces):**
- El sistema bloquea la operación
- Muestra un mensaje indicando que el stock disponible en la ubicación de origen es insuficiente
- No genera ningún movimiento ni modifica el stock en ninguna ubicación

---

### Scenario 3: Intento de traslado hacia la misma ubicación de origen

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona la misma ubicación como origen y como destino del traslado

**Then (Entonces):**
- El sistema rechaza la operación
- Muestra un mensaje indicando que el origen y el destino no pueden ser la misma ubicación
- No genera ningún movimiento

---

### Scenario 4: Auxiliar corrige un traslado dentro de la misma franja horaria activa

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- Registró un traslado durante la franja horaria activa actual
- La franja horaria aún no ha cerrado

**When (Cuando):**
- Detecta un error en el registro y accede a la opción de edición
- Corrige los datos incorrectos y confirma los cambios

**Then (Entonces):**
- El sistema permite la corrección
- Actualiza el registro reflejando los valores corregidos
- Deja constancia en el log de auditoría de que el registro fue editado, indicando el UserID del auxiliar y el timestamp de la corrección

---

### Scenario 5: Auxiliar intenta corregir un traslado después de cerrada la franja horaria

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- Registró un traslado durante una franja horaria que ya cerró

**When (Cuando):**
- Intenta acceder a la opción de edición de ese registro

**Then (Entonces):**
- El sistema bloquea la edición
- Muestra un mensaje indicando que la ventana de corrección ha cerrado y que cualquier ajuste debe ser solicitado al Almacenista
- El registro original permanece inmutable

## **RF-008 — Registro de Devoluciones de Productos**

**Módulo:** Devoluciones

**Descripción**

El sistema debe gestionar el reingreso de productos al inventario de ICM provenientes de clientes externos. Esta operación tiene una restricción de negocio crítica: únicamente los productos de la categoría Electroterapia o Electrónicos pueden ser objeto de devolución. Para cualquier otro tipo de producto, el sistema debe bloquear automáticamente el intento e informar al operario la razón. Adicionalmente, toda devolución de producto eléctrico debe pasar por un proceso de auditoría en dos etapas antes de reincorporarse al stock disponible: primero el operario registra la devolución con el estado del producto y el motivo declarado por el cliente, y luego el Almacenista revisa y aprueba o rechaza la reincorporación al stock.

**Reglas de Negocio Aplicables**

* BR-05: Solo los productos de la categoría Electroterapia o Electrónicos admiten devoluciones. El sistema bloquea automáticamente cualquier devolución de otro tipo de producto.
* BR-10: El log de cada devolución es inmutable una vez registrado. Incluye SKU, número de serie, motivo, estado del producto, UserID del operario y timestamp.
* BR-02: La aprobación de reincorporación al stock es una facultad exclusiva del Almacenista.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Registro de devoluciones de productos

### Scenario 1: Registro exitoso de devolución de producto de Electroterapia

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto a devolver pertenece a la categoría "Electroterapia" o "Electrónicos"

**When (Cuando):**
- Inicia el registro de devolución
- Selecciona el producto por SKU o número de serie
- Registra el motivo declarado por el cliente
- Registra el estado físico del producto al momento de recibirlo
- Confirma la devolución

**Then (Entonces):**
- El sistema genera un log inmutable de la devolución con SKU, número de serie, motivo, estado del producto, UserID del operario y timestamp exacto
- El producto queda en estado "Pendiente de revisión" sin ser reincorporado al stock disponible todavía
- El Almacenista recibe una notificación de que hay una devolución pendiente de aprobación

---

### Scenario 2: Intento de devolución de producto que no es Electroterapia ni Electrónico

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto seleccionado pertenece a la categoría "Manoterapia" o "Mesas de Fisioterapia"

**When (Cuando):**
- Intenta iniciar el registro de una devolución para ese producto

**Then (Entonces):**
- El sistema bloquea la operación de forma inmediata
- Muestra un mensaje descriptivo indicando que ese tipo de producto no admite devoluciones según la política de ICM
- No genera ningún registro ni modifica el stock

---

### Scenario 3: Almacenista aprueba la reincorporación al stock de un producto devuelto

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una devolución en estado "Pendiente de revisión"

**When (Cuando):**
- Accede al listado de devoluciones pendientes
- Revisa el log de la devolución incluyendo motivo y estado del producto
- Aprueba la reincorporación al stock
- Selecciona la ubicación de destino donde se reincorporará el producto

**Then (Entonces):**
- El sistema incrementa el stock del producto en la ubicación seleccionada
- Actualiza el estado de la devolución a "Reincorporado"
- Registra la aprobación en el log con el UserID del Almacenista y timestamp
- El movimiento de reincorporación queda vinculado al log original de la devolución

---

### Scenario 4: Almacenista rechaza la reincorporación de un producto devuelto

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una devolución en estado "Pendiente de revisión"

**When (Cuando):**
- Revisa el log de la devolución
- Determina que el producto no está en condiciones de ser reincorporado
- Rechaza la reincorporación registrando el motivo del rechazo

**Then (Entonces):**
- El sistema actualiza el estado de la devolución a "Rechazada"
- No modifica el stock disponible en ninguna ubicación
- El motivo del rechazo queda vinculado al log original de la devolución
- El registro completo permanece inmutable para efectos de auditoría

---

### Scenario 5: Consulta del historial de devoluciones por el Almacenista

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al historial de devoluciones

**Then (Entonces):**
- El sistema muestra todas las devoluciones registradas con su estado actual (Pendiente, Reincorporado o Rechazada)
- Permite filtrar por producto, período, operario o estado
- Cada registro del historial es de solo lectura e inmutable

## **RF-009 — Ajustes de Inventario**

**Módulo:** Ajustes de Inventario

**Descripción**

El sistema debe permitir corregir discrepancias entre el stock físico real y el registrado en el sistema, cuando dichas diferencias no pueden resolverse mediante las operaciones estándar de entrada, salida o traslado. Este módulo está restringido exclusivamente al rol de Almacenista, quien es el único habilitado para ejecutar ajustes formales. Todo ajuste debe incluir una justificación obligatoria que explique la causa de la discrepancia, y el sistema debe generar un log inmutable del ajuste con el delta entre el stock previo y el stock ajustado. Un ajuste no reemplaza ni elimina el movimiento original erróneo, sino que convive con él en el historial, garantizando así una trazabilidad completa y honesta de lo que ocurrió en el inventario.

**Reglas de Negocio Aplicables**

* BR-06: Un Auxiliar de Despacho puede editar un movimiento que registró dentro de la misma franja horaria activa. Una vez cerrada la franja, el registro queda inmutable y cualquier corrección debe tramitarse como ajuste formal por el Almacenista.
* BR-07: Todo ajuste de inventario fuera de la ventana de autocorrección requiere justificación obligatoria y es ejecutado exclusivamente por el Almacenista.
* BR-10: Los registros históricos de movimientos y ajustes no pueden ser eliminados ni modificados por ningún usuario. Un ajuste erróneo se corrige con un nuevo ajuste, nunca borrando el anterior.
* BR-11: El stock se gestiona por ubicación. El ajuste debe especificar en cuál de los tres puntos de almacenamiento se aplica la corrección.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Ajustes de inventario

### Scenario 1: Almacenista registra un ajuste de inventario con justificación

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una discrepancia entre el stock físico real y el stock registrado en el sistema

**When (Cuando):**
- Accede al módulo de ajustes de inventario
- Selecciona el producto y la ubicación donde ocurre la discrepancia
- Ingresa el nuevo valor de stock correcto
- Registra una justificación obligatoria explicando la causa de la discrepancia
- Confirma el ajuste

**Then (Entonces):**
- El sistema actualiza el stock del producto en la ubicación indicada
- Genera un log inmutable del ajuste con UserID del Almacenista, timestamp, producto, ubicación, stock previo, stock ajustado, delta de la diferencia y justificación registrada
- Recalcula el stock total consolidado del producto

---

### Scenario 2: Intento de registrar un ajuste sin justificación

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Completa el formulario de ajuste dejando vacío el campo de justificación
- Intenta confirmar el ajuste

**Then (Entonces):**
- El sistema bloquea la operación
- Muestra un mensaje indicando que la justificación es un campo obligatorio
- No modifica el stock ni genera ningún registro

---

### Scenario 3: Auxiliar de Despacho intenta ejecutar un ajuste formal

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al módulo de ajustes de inventario

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que esta funcionalidad está reservada exclusivamente para el Almacenista
- No genera ningún cambio en el sistema

---

### Scenario 4: Corrección de un ajuste registrado incorrectamente

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe un ajuste previo registrado con valores incorrectos

**When (Cuando):**
- Determina que el ajuste anterior fue erróneo
- Registra un nuevo ajuste con los valores correctos
- Proporciona una justificación que referencia el ajuste anterior
- Confirma el nuevo ajuste

**Then (Entonces):**
- El sistema registra el nuevo ajuste como un movimiento independiente
- El ajuste anterior permanece inmutable en el historial
- Ambos registros quedan vinculados en el log de auditoría
- El stock refleja el valor correcto según el ajuste más reciente

---

### Scenario 5: Auxiliar corrige su propio movimiento dentro de la franja horaria activa

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- Registró un movimiento durante la franja horaria activa actual
- La franja horaria aún no ha cerrado

**When (Cuando):**
- Detecta el error y accede a la opción de edición del movimiento
- Corrige los valores incorrectos y confirma el cambio

**Then (Entonces):**
- El sistema permite la corrección sin requerir intervención del Almacenista
- Registra en el log de auditoría que el movimiento fue editado con el UserID del auxiliar y el timestamp de la corrección
- El movimiento corregido refleja los valores actualizados

---

### Scenario 6: Consulta del historial completo de ajustes por el Almacenista

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al historial de ajustes de inventario

**Then (Entonces):**
- El sistema muestra todos los ajustes registrados en orden cronológico
- Para cada ajuste despliega el producto, ubicación, stock previo, stock ajustado, delta, justificación, UserID y timestamp
- Permite filtrar por producto, período o usuario responsable
- Todos los registros son de solo lectura e inmutables

## **RF-010 — Reportes e Indicadores Operativos (Dashboard Gerencial)**

**Módulo:** Reportes e Indicadores

**Descripción**

El sistema debe contar con un módulo de reportes y dashboard gerencial que transforme los datos operativos acumulados en información estratégica de valor para la toma de decisiones. El dashboard operacional pertenece al rol de Almacenista como usuario rector de la operación, mientras que el Administrador/Jefe conserva acceso de lectura limitada a los reportes que correspondan. Los reportes deben poder exportarse en formato Excel o CSV para integrarse con el software contable externo de ICM, y el módulo debe centralizar además el historial completo de facturas y remisiones generadas desde el módulo de Despacho, permitiendo su consulta, filtrado y descarga individual en PDF. Este módulo no genera datos nuevos ni modifica el inventario: es exclusivamente un módulo de lectura y presentación de la información que otros módulos han producido.

**Reglas de Negocio Aplicables**

* BR-10: Los registros históricos que alimentan los reportes son inmutables. El módulo de reportes no debe permitir ninguna modificación sobre los datos que presenta.
* BR-11: El stock total presentado en cualquier reporte es siempre la sumatoria dinámica de Vitrina, Bodega 1 y Bodega 2, consistente con el modelo de almacenaje caótico de ICM.
* BR-13: El historial de facturas digitales generadas en cada despacho debe ser consultable desde este módulo, con posibilidad de filtrado por período, tipo de salida o cliente, y descarga individual en PDF.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Reportes e indicadores operativos

### Scenario 1: Almacenista consulta el reporte de ventas por período

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al módulo de reportes
- Selecciona el tipo "Reporte de ventas"
- Define un rango de fechas (diario, semanal, mensual o rango personalizado)
- Aplica el filtro

**Then (Entonces):**
- El sistema muestra un reporte consolidado de todas las salidas clasificadas como venta dentro del período seleccionado
- Desglosa los resultados por tipo de salida (Venta al por Mayor, Venta al por Menor)
- El reporte es de solo lectura y no permite modificaciones

---

### Scenario 2: Almacenista consulta el dashboard de KPIs operativos

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al dashboard gerencial

**Then (Entonces):**
- El sistema presenta de forma visual e interactiva los siguientes indicadores:
  - Índice de rotación de inventario por categoría con gráficos de tendencia
  - Porcentaje de ocupación por zona de almacenamiento
  - Nivel de servicio expresado como porcentaje de pedidos despachados completos y a tiempo
  - Panel de alertas operativas activas (vencimientos, stock mínimo y pedidos pendientes)
- Ninguno de estos indicadores permite edición desde esta vista

### Scenario 2.1: Almacenista consulta el dashboard operacional por contratos composables

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede a `overview` o a uno de los contratos parciales del dashboard

**Then (Entonces):**
- El sistema permite consultar métricas, alertas, KPIs y movimientos recientes por separado
- El contrato `overview` agrega estos bloques sin mezclar lógica de negocio ni exportación
- El dashboard actúa como read model operacional orientado a UI ejecutiva
- Las métricas parciales o futuras se presentan con su nivel real de precisión

---

### Scenario 3: Exportación de reporte en formato Excel o CSV

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"
- Ha generado un reporte con los filtros deseados

**When (Cuando):**
- Selecciona la opción de exportar y elige el formato (Excel o CSV)

**Then (Entonces):**
- El sistema genera el archivo con los datos del reporte en el formato seleccionado
- Lo pone a disposición del usuario para su descarga inmediata
- El archivo exportado contiene exactamente los mismos datos visibles en pantalla

---

### Scenario 4: Consulta del historial de movimientos por operario

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al reporte de historial de movimientos
- Filtra por un operario específico y un período de tiempo

**Then (Entonces):**
- El sistema muestra todos los movimientos registrados por ese operario en el período
- Para cada movimiento despliega tipo de transacción, producto, cantidad, ubicación, timestamp y stock resultante
- Permite exportar ese historial en Excel o CSV

---

### Scenario 5: Consulta del reporte de productos próximos a vencer

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al reporte de vencimientos

**Then (Entonces):**
- El sistema lista todos los productos con fecha de vencimiento dentro de los próximos 60 días
- Los organiza por urgencia, mostrando primero los que vencen más pronto
- Para cada producto indica SKU, nombre, lote, fecha de vencimiento, stock disponible y ubicación

---

### Scenario 6: Consulta y descarga de factura individual desde el historial

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al historial de facturas y remisiones
- Filtra por período, tipo de salida o cliente
- Selecciona una factura específica del listado

**Then (Entonces):**
- El sistema muestra los detalles completos de esa factura
- Permite su descarga individual en formato PDF
- El documento descargado es idéntico al generado en el momento del despacho

---

### Scenario 7: Usuario sin permisos intenta acceder al módulo de reportes

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al módulo de reportes o al dashboard gerencial

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que no tiene permisos para visualizar esta sección
- No expone ningún dato operativo ni indicador

## **RF-011 — Alertas Proactivas del Sistema**

**Módulo:** Alertas Proactivas

**Descripción**

El sistema debe emitir alertas automáticas ante condiciones operativas que requieran atención inmediata o preventiva, sin que el usuario tenga que buscarlas activamente. Este módulo es transversal a toda la plataforma: las alertas acompañan al usuario en el módulo donde está trabajando en ese momento. Se definen cuatro tipos de alerta: stock mínimo, vencimiento próximo, cadena de frío y seguridad eléctrica. Cada una tiene un momento de disparo, una audiencia y un nivel de urgencia diferente, y el sistema debe tratarlas de forma diferenciada para evitar que todas compitan por la atención del operario con la misma intensidad visual.

**Reglas de Negocio Aplicables**

* BR-11: El punto de reorden se calcula con base en la rotación mensual de cada SKU. Cuando el stock total cae por debajo de ese umbral, se activa la alerta de stock mínimo.
* BR-04: Los productos de Electroterapia requieren manejo especial. La alerta de seguridad eléctrica debe desplegarse en cualquier movimiento que involucre esta categoría.
* BR-10: Las alertas generadas quedan registradas en el log de auditoría y son inmutables. No pueden ser eliminadas manualmente por ningún usuario.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Alertas proactivas del sistema

### Scenario 1: Alerta de stock mínimo cuando el inventario cae bajo el punto de reorden

**Given (Dado que):**
- Un producto tiene configurado un punto de reorden de 10 unidades
- El stock total del producto era de 12 unidades

**When (Cuando):**
- Se confirma un despacho que deja el stock total en 8 unidades

**Then (Entonces):**
- El sistema emite de forma automática una alerta de stock mínimo visible en el dashboard del Almacenista y del Administrador
- La alerta indica el SKU, nombre del producto, stock actual y punto de reorden
- La alerta permanece activa hasta que el stock supere nuevamente el umbral
- El evento de activación queda registrado en el log con timestamp

---

### Scenario 2: Alerta de vencimiento próximo a 60 días

**Given (Dado que):**
- Existe un lote de producto registrado con fecha de vencimiento

**When (Cuando):**
- Faltan exactamente 60 días calendario para esa fecha de vencimiento

**Then (Entonces):**
- El sistema emite automáticamente una alerta de vencimiento visible en el dashboard y en el módulo de inventario
- La alerta indica SKU, nombre del producto, número de lote, fecha de vencimiento y stock disponible del lote afectado
- La alerta queda registrada en el log de auditoría con timestamp

---

### Scenario 3: Alerta de vencimiento próximo a 30 días

**Given (Dado que):**
- Existe una alerta de vencimiento activa a 60 días
- Han transcurrido 30 días desde su activación

**When (Cuando):**
- El sistema detecta que ahora faltan 30 días para el vencimiento

**Then (Entonces):**
- El sistema escala la alerta existente a un nivel de urgencia mayor
- La alerta actualizada es visualmente diferenciada de la alerta a 60 días
- El escalamiento queda registrado en el log de auditoría

---

### Scenario 4: Alerta de cadena de frío al registrar movimiento de producto refrigerado

**Given (Dado que):**
- Un producto tiene activado el indicador de cadena de frío

**When (Cuando):**
- Cualquier usuario registra un movimiento que involucra ese producto

**Then (Entonces):**
- El sistema despliega de forma inmediata una alerta visual persistente y de alta visibilidad en la pantalla activa del usuario
- El usuario debe reconocer la alerta antes de poder confirmar el movimiento
- El reconocimiento queda registrado en el log con UserID y timestamp

---

### Scenario 5: Alerta de seguridad eléctrica al registrar movimiento de equipo eléctrico

**Given (Dado que):**
- Un producto pertenece a la categoría "Electroterapia"

**When (Cuando):**
- Cualquier usuario registra un movimiento que involucra ese producto

**Then (Entonces):**
- El sistema despliega una advertencia visual sobre los protocolos de manejo seguro
- La advertencia es visualmente distinguible de la alerta de cadena de frío
- El usuario debe reconocer la advertencia antes de confirmar el movimiento
- El reconocimiento queda registrado en el log con UserID y timestamp

---

### Scenario 6: Panel de alertas activas en el dashboard

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al dashboard principal

**Then (Entonces):**
- El sistema presenta un panel consolidado con todas las alertas operativas activas, organizadas por tipo y urgencia
- Cada alerta en el panel es navegable hacia el producto o movimiento que la originó
- Las alertas a 30 días aparecen por encima de las alertas a 60 días en el panel

---

### Scenario 7: Resolución automática de una alerta de stock mínimo

**Given (Dado que):**
- Existe una alerta de stock mínimo activa para un producto

**When (Cuando):**
- Se confirma una entrada de mercancía que eleva el stock total del producto por encima del punto de reorden

**Then (Entonces):**
- El sistema desactiva automáticamente la alerta de stock mínimo
- La elimina del panel de alertas activas
- Deja constancia en el log de auditoría de que la alerta fue resuelta, con el timestamp de resolución y el movimiento de entrada que la originó

## **RF-012 — Log de Auditoría y Trazabilidad de Operaciones**

**Módulo:** Auditoría y Trazabilidad

**Descripción**

El sistema debe mantener un log de auditoría centralizado, continuo e inmutable que registre automáticamente cada operación que afecte el inventario, las credenciales de acceso o la seguridad del sistema. Este log no es generado manualmente por ningún usuario: es el sistema quien lo produce en el momento exacto en que ocurre cada evento, sin posibilidad de intervención humana sobre su contenido una vez creado. El Almacenista es el único rol con acceso directo al log completo. La trazabilidad nominal —la capacidad de vincular cada transacción al UserID exacto del empleado que la ejecutó— es un atributo de calidad no negociable del sistema.

**Reglas de Negocio Aplicables**

* BR-01: Cada transacción registrada en el log debe estar vinculada de forma unívoca al UserID del empleado que la ejecutó. No puede existir ningún movimiento anónimo en el sistema.
* BR-10: Los registros históricos no pueden ser eliminados ni modificados por ningún usuario, incluyendo el Almacenista. La inmutabilidad es absoluta y sin excepciones.
* BR-06: La ventana de autocorrección del Auxiliar de Despacho también queda registrada en el log, dejando constancia tanto del registro original como de la corrección posterior.
* BR-07: Los ajustes formales ejecutados por el Almacenista quedan registrados en el log con justificación obligatoria vinculada.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Log de auditoría y trazabilidad de operaciones

### Scenario 1: El sistema genera automáticamente un registro de auditoría al confirmar cualquier movimiento de inventario

**Given (Dado que):**
- Cualquier usuario autenticado confirma una operación que afecta el stock

**When (Cuando):**
- El sistema procesa y confirma la operación

**Then (Entonces):**
- El sistema genera de forma automática e inmediata un registro en el log que contiene:
  - Identificador único del movimiento
  - Timestamp con fecha y hora exacta
  - UserID del operario responsable
  - Tipo de transacción
  - SKU del producto involucrado
  - Código serial cuando aplique
  - Ubicación de origen y destino
  - Cantidad operada
  - Stock previo y stock resultante
  - Nota o justificación cuando la operación lo requiera
- Ese registro queda inmutable desde el momento de su creación

---

### Scenario 2: El sistema registra en el log los eventos de autenticación

**Given (Dado que):**
- Cualquier usuario intenta iniciar o cerrar sesión en el sistema

**When (Cuando):**
- El intento de autenticación ocurre, sea exitoso o fallido

**Then (Entonces):**
- El sistema registra en el log el evento con timestamp, UserID o nombre de usuario intentado, resultado del intento (éxito o fallo) y dirección del dispositivo desde donde se realizó el intento
- Ese registro es inmutable y no puede ser eliminado

---

### Scenario 3: El sistema registra en el log los eventos de gestión de credenciales

**Given (Dado que):**
- El Almacenista crea, modifica o deshabilita una cuenta de usuario

**When (Cuando):**
- Confirma cualquiera de esas acciones

**Then (Entonces):**
- El sistema registra en el log el evento con timestamp, UserID del Almacenista que ejecutó la acción, tipo de acción realizada (creación, modificación o deshabilitación) y UserID de la cuenta afectada
- El registro es inmutable desde su creación

---

### Scenario 4: El sistema registra el reconocimiento de alertas de cadena de frío y seguridad eléctrica

**Given (Dado que):**
- Un usuario reconoce activamente una alerta de cadena de frío o de seguridad eléctrica antes de confirmar un movimiento

**When (Cuando):**
- Confirma el reconocimiento de la alerta

**Then (Entonces):**
- El sistema registra en el log ese reconocimiento con UserID, timestamp, tipo de alerta reconocida y SKU del producto involucrado
- Ese registro queda vinculado al movimiento que originó la alerta

---

### Scenario 5: Almacenista consulta el log completo de auditoría con filtros

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al módulo de auditoría
- Aplica filtros por período, tipo de operación, operario o producto

**Then (Entonces):**
- El sistema muestra todos los registros que coinciden con los filtros en orden cronológico
- Cada registro es de solo lectura, sin opción de edición ni eliminación
- El Almacenista puede exportar el log filtrado en formato Excel o CSV

---

### Scenario 6: Auxiliar de Despacho intenta acceder al log de auditoría

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al módulo de auditoría por cualquier vía

**Then (Entonces):**
- El sistema bloquea el acceso de forma inmediata
- Muestra un mensaje indicando que no tiene permisos para consultar el log
- No expone ningún registro del historial

---

### Scenario 7: El log registra tanto el movimiento original como la corrección del Auxiliar

**Given (Dado que):**
- Un Auxiliar de Despacho registró un movimiento durante la franja activa
- Detecta un error y lo corrige antes de que cierre la franja

**When (Cuando):**
- Confirma la corrección

**Then (Entonces):**
- El sistema mantiene el registro original en el log con su timestamp de creación
- Agrega un segundo registro vinculado al primero indicando que fue corregido, con el UserID del auxiliar y el timestamp exacto de la corrección
- Ambos registros son inmutables e independientes

---

### Scenario 8: Intento de eliminación o modificación de un registro del log

**Given (Dado que):**
- Cualquier usuario autenticado, independientemente de su rol, intenta modificar o eliminar un registro existente en el log

**When (Cuando):**
- Ejecuta esa acción por cualquier vía disponible en la interfaz

**Then (Entonces):**
- El sistema rechaza la operación de forma absoluta
- Muestra un mensaje indicando que los registros de auditoría son inmutables
- Registra en el propio log el intento fallido de modificación con UserID y timestamp

---

## **RF-013 — Precios y Facturación Comercial**

**Módulo:** Precios y Facturación

**Descripción**

El sistema debe gestionar el ciclo completo de precios de productos y la generación de documentos comerciales con valor económico real. Cada producto puede tener hasta cuatro campos de precio opcionales: costo de adquisición, precio de venta al por menor, precio de venta al por mayor y tasa de IVA. Toda modificación de precio debe quedar registrada de forma inmutable en un historial que identifica el campo, el valor anterior, el valor nuevo y el usuario responsable. Al confirmar cualquier despacho de venta, el sistema captura el precio vigente en el registro de movimiento de manera permanente, garantizando que documentos históricos no se vean afectados por cambios futuros al catálogo. El sistema genera automáticamente un modelo de factura consolidado con subtotales, IVA y total, exportable en PDF con todos los datos del despacho y del cliente. Los reportes financieros permiten calcular revenue por tipo de venta, margen bruto por SKU y ventas agrupadas por cliente.

**Reglas de Negocio Aplicables**

* BR-13: Todo despacho confirmado genera factura digital con numeración secuencial. El PDF incluye precio unitario, descuento, IVA y total.
* BR-16: Al confirmar un despacho, el precio unitario, subtotal, IVA y total quedan congelados de forma permanente en el movimiento. Modificaciones posteriores al precio del producto no alteran movimientos ni facturas históricas.
* BR-17: Toda actualización de precio genera un registro inmutable en el historial con el campo modificado, valor anterior, valor nuevo, usuario y timestamp. Si el valor enviado es idéntico al actual, no se registra nada.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Precios y facturación comercial

### Scenario 1: Despacho captura precio congelado del producto al momento de la salida

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Auxiliar de Despacho"
- Existe un producto con sale_price_retail=10000, tax_rate_pct=19.00 y currency="COP"
- Hay stock suficiente del producto en la ubicación de origen

**When (Cuando):**
- Registra un despacho de venta al por menor de 3 unidades del producto y confirma la operación

**Then (Entonces):**
- El sistema crea un Movement con unit_price=10000, subtotal=30000, tax_amount=5700, total_amount=35700 y price_type="retail"
- El sistema crea un registro Invoice con los mismos totales consolidados
- El PDF del comprobante incluye precio unitario, IVA y total

---

### Scenario 2: Precio en historial permanece inmutable tras modificar el precio actual del producto

**Given (Dado que):**
- Existe un producto con sale_price_retail=10000
- Se realizó y confirmó un despacho de venta al por menor; el Movement quedó con unit_price=10000

**When (Cuando):**
- El Almacenista actualiza el precio del producto a sale_price_retail=20000 mediante PATCH /api/v1/catalog/products/<id>/prices/

**Then (Entonces):**
- El Movement histórico conserva unit_price=10000 sin alteración
- La factura descargable sigue mostrando el precio original del despacho
- El nuevo precio 20000 aplica únicamente a despachos futuros

---

### Scenario 3: Actualización de precio genera historial auditado con valor anterior y nuevo

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe un producto con sale_price_retail=10000

**When (Cuando):**
- El Almacenista ejecuta PATCH /api/v1/catalog/products/<id>/prices/ con {"sale_price_retail": "12000"}

**Then (Entonces):**
- Se crea un registro en ProductPriceHistory con field_changed="sale_price_retail", old_value=10000, new_value=12000 y changed_by igual al almacenista
- Si el valor enviado es idéntico al actual, no se crea ningún registro de historial
- GET /api/v1/catalog/products/<id>/prices/ retorna el historial completo del producto
- Un usuario con rol distinto a almacenista recibe 403 Forbidden al intentar actualizar precios

---

### Scenario 4: Factura comercial reconstruible completamente desde el Movement sin consultar el catálogo actual

**Given (Dado que):**
- Se confirmó un despacho de venta al por mayor con datos del cliente: nombre, correo, teléfono y dirección
- El producto tenía sale_price_wholesale=9000 y tax_rate_pct=19.00

**When (Cuando):**
- El administrador o almacenista consulta GET /api/v1/movements/invoices/<number>/ o descarga el PDF

**Then (Entonces):**
- La respuesta incluye datos del cliente, subtotal, IVA, total y moneda con los valores exactos del momento del despacho
- El PDF contiene la tabla de líneas con precio unitario, descuento, IVA y total
- Los valores son correctos aunque el precio del producto haya sido modificado después del despacho
- Los valores son correctos aunque el producto esté actualmente desactivado

---

# **6. Requisitos No Funcionales**

Los requisitos no funcionales (RNF) definen los atributos de calidad que el sistema debe cumplir para ser operativamente viable en el contexto real de ICM. A diferencia de los requisitos funcionales, que describen qué hace el sistema, los requisitos no funcionales describen cómo debe hacerlo: con qué velocidad, con qué nivel de seguridad, con qué grado de disponibilidad. Estos requisitos son transversales a todos los módulos y deben ser considerados desde la fase de diseño arquitectónico, no como consideraciones tardías de optimización.

## **RNF-001 — Usabilidad e Interfaz Intuitiva**

**Módulo:** Transversal

**Descripción**

El sistema debe diseñarse bajo el principio KISS (Keep It Simple, Stupid), priorizando una interfaz que pueda ser operada con fluidez por personal de bodega sin formación técnica especializada. Dado que los Auxiliares de Despacho son el perfil de usuario más frecuente y el menos técnico, la interfaz debe minimizar la fricción en los flujos más repetitivos como búsqueda de productos, registro de entradas y confirmación de despachos. La interfaz debe ser responsiva y estar optimizada para dispositivos móviles y tabletas, ya que los operarios realizan consultas y registros directamente desde la bodega usando esos dispositivos.

**Reglas de Negocio Aplicables**

* No aplican reglas de negocio específicas. Este requisito se deriva del principio KISS establecido en los requerimientos no funcionales del informe de elicitación y de la realidad operativa de ICM donde el personal de bodega opera sin background técnico.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Usabilidad e interfaz intuitiva

### Scenario 1: Operario completa un flujo de despacho sin formación técnica previa

**Given (Dado que):**
- Un Auxiliar de Despacho accede al sistema por primera vez tras una inducción operativa básica de no más de 30 minutos

**When (Cuando):**
- Intenta registrar un despacho estándar de principio a fin

**Then (Entonces):**
- El operario completa el flujo sin necesidad de consultar documentación técnica ni solicitar asistencia
- El sistema guía al usuario paso a paso dentro del flujo sin ambigüedad sobre cuál es la siguiente acción requerida

---

### Scenario 2: La interfaz responde correctamente en dispositivos móviles y tabletas

**Given (Dado que):**
- Un operario accede al sistema desde una tableta o un teléfono inteligente

**When (Cuando):**
- Navega por cualquier módulo disponible para su rol

**Then (Entonces):**
- Todos los elementos de la interfaz se adaptan al tamaño de pantalla del dispositivo sin pérdida de funcionalidad
- Los botones y campos son suficientemente grandes para ser operados con precisión táctil
- Ningún elemento crítico queda oculto o inaccesible en resoluciones móviles

---

### Scenario 3: La búsqueda de productos es igualmente eficiente por cualquier vía

**Given (Dado que):**
- Un operario necesita localizar un producto durante la atención a un cliente

**When (Cuando):**
- Busca el producto ya sea por nombre, SKU o código de barras

**Then (Entonces):**
- El sistema devuelve resultados relevantes en menos de 2 segundos por cualquiera de las tres vías de búsqueda
- El operario puede identificar y seleccionar el producto correcto sin navegar por más de dos pantallas desde el punto de búsqueda

## **RNF-002 — Disponibilidad del Sistema**

**Módulo:** Transversal

**Descripción**

El sistema debe garantizar disponibilidad continua y sin interrupciones durante las franjas horarias de operación de los Auxiliares de Despacho (07:00–12:00 y 14:00–17:00), ya que cualquier caída del sistema en esas ventanas impacta directamente el cumplimiento de despachos y la operación de ICM. Para el Almacenista y el Administrador, la disponibilidad debe ser total, las 24 horas del día los 7 días de la semana, dado que ambos roles pueden necesitar consultar el sistema o gestionar incidencias fuera del horario laboral convencional.

**Reglas de Negocio Aplicables**

* BR-03 establece las franjas horarias de operación de los Auxiliares de Despacho, que son exactamente las ventanas críticas que este requisito debe garantizar.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Disponibilidad del sistema

### Scenario 1: El sistema permanece disponible durante las franjas críticas de operación

**Given (Dado que):**
- El sistema está desplegado en el entorno de producción

**When (Cuando):**
- Un Auxiliar de Despacho intenta acceder al sistema dentro de su franja horaria

**Then (Entonces):**
- El sistema responde y permite el acceso sin interrupciones
- Cualquier operación iniciada dentro de la franja puede completarse sin que el sistema la interrumpa por inactividad o caída durante esa ventana

---

### Scenario 2: El Almacenista puede acceder al sistema en cualquier momento del día

**Given (Dado que):**
- El sistema está desplegado en producción

**When (Cuando):**
- El Almacenista intenta acceder al sistema fuera del horario laboral convencional

**Then (Entonces):**
- El sistema responde y otorga acceso completo sin restricciones horarias
- Todas las funcionalidades del rol Almacenista están disponibles

---

### Scenario 3: El sistema notifica adecuadamente ante una interrupción no planificada

**Given (Dado que):**
- Ocurre una interrupción no planificada del sistema

**When (Cuando):**
- Un usuario intenta acceder durante esa interrupción

**Then (Entonces):**
- El sistema muestra un mensaje claro indicando que el servicio no está disponible
- El mensaje no expone detalles técnicos internos del error al usuario final

## **RNF-003 — Seguridad e Integridad de Datos**

**Módulo:** Transversal

**Descripción**

El sistema debe proteger la información operativa y comercial de ICM mediante cifrado tanto en tránsito como en reposo, garantizando que los datos no puedan ser interceptados ni accedidos por agentes externos. El modelo RBAC implementado desde RF-001 y RF-002 es el mecanismo principal de control de acceso, y este requisito lo complementa con las condiciones técnicas que hacen que ese modelo sea realmente seguro y no solo declarativo. La trazabilidad nominal, la inmutabilidad del log y la segregación de funciones son atributos de seguridad que este requisito eleva al nivel de verificable y medible.

**Reglas de Negocio Aplicables**

* BR-01 garantiza la trazabilidad nominal mediante UserIDs únicos.
* BR-10 establece la inmutabilidad absoluta de todos los registros históricos.
* BR-02 define la segregación de funciones en la gestión de credenciales, que es el primer vector de ataque en cualquier sistema con roles diferenciados.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Seguridad e integridad de datos

### Scenario 1: Los datos sensibles viajan cifrados entre el cliente y el servidor

**Given (Dado que):**
- Cualquier usuario realiza una operación en el sistema que implica transmisión de datos

**When (Cuando):**
- Esa operación genera tráfico de red entre el frontend y el backend

**Then (Entonces):**
- Toda la comunicación ocurre exclusivamente sobre HTTPS
- Ningún dato sensible se transmite en texto plano bajo ninguna circunstancia

---

### Scenario 2: Un usuario no puede acceder a funcionalidades fuera de su rol

**Given (Dado que):**
- Cualquier usuario está autenticado en el sistema

**When (Cuando):**
- Intenta acceder a una ruta, vista o endpoint que corresponde a un rol distinto al suyo, ya sea manipulando la URL directamente o mediante cualquier otro mecanismo

**Then (Entonces):**
- El sistema rechaza la solicitud con un error de autorización
- No expone ningún dato ni funcionalidad del rol restringido
- El intento queda registrado en el log de auditoría

---

### Scenario 3: Las contraseñas de los usuarios se almacenan de forma segura

**Given (Dado que):**
- El Almacenista crea o modifica la contraseña de cualquier usuario

**When (Cuando):**
- El sistema procesa y almacena esa contraseña

**Then (Entonces):**
- La contraseña se almacena en la base de datos usando un algoritmo de hashing seguro con sal (por ejemplo bcrypt)
- En ningún punto del sistema la contraseña es almacenada ni transmitida en texto plano

---

### Scenario 4: Ningún usuario puede modificar ni eliminar un registro histórico

**Given (Dado que):**
- Cualquier usuario autenticado, independientemente de su rol, intenta modificar o eliminar un registro del log o un movimiento ya confirmado

**When (Cuando):**
- Ejecuta o intenta ejecutar esa acción

**Then (Entonces):**
- El sistema rechaza la operación de forma absoluta
- El registro original permanece intacto e inalterado
- El intento fallido queda registrado en el log con UserID y timestamp

## **RNF-004 — Rendimiento en Consultas y Operaciones**

**Módulo:** Transversal

**Descripción**

El sistema debe responder con la velocidad suficiente para no interrumpir el flujo de trabajo durante la atención al cliente en negociaciones comerciales, que es el escenario de mayor presión identificado durante la elicitación con ICM. Con un catálogo de entre 220 y 250 productos distribuidos en tres ubicaciones, las consultas de stock no deben representar una fricción perceptible para el operario. Este requisito establece los umbrales de tiempo de respuesta que el equipo de pruebas debe verificar como parte del plan maestro de pruebas del Corte 3.

**Reglas de Negocio Aplicables**

* No aplican reglas de negocio de dominio directamente. El umbral de 2 segundos proviene directamente del informe de elicitación como condición operativa mínima aceptable para ICM.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Rendimiento en consultas y operaciones

### Scenario 1: Consulta de stock de un producto responde dentro del umbral definido

**Given (Dado que):**
- El sistema está operando bajo condiciones normales de uso
- El catálogo contiene entre 220 y 250 productos registrados

**When (Cuando):**
- Cualquier usuario realiza una consulta de stock por nombre, SKU o código de barras

**Then (Entonces):**
- El sistema devuelve el resultado con el stock por ubicación y el stock total consolidado en un tiempo no mayor a 2 segundos

---

### Scenario 2: El registro de un movimiento de inventario se confirma dentro de un tiempo razonable

**Given (Dado que):**
- Un operario completa y confirma un movimiento de inventario

**When (Cuando):**
- El sistema procesa la confirmación

**Then (Entonces):**
- El sistema actualiza el stock, genera el log de auditoría y muestra la confirmación al usuario en un tiempo no mayor a 3 segundos bajo condiciones normales de uso

---

### Scenario 3: El sistema mantiene el rendimiento bajo uso simultáneo de los tres roles

**Given (Dado que):**
- El Almacenista, un Auxiliar de Despacho y el Administrador están usando el sistema de forma simultánea

**When (Cuando):**
- Cada uno ejecuta operaciones propias de su rol al mismo tiempo

**Then (Entonces):**
- El tiempo de respuesta de cada operación no se degrada más allá de los umbrales definidos para cada tipo de consulta
- Ningún usuario experimenta bloqueos ni timeouts durante el uso concurrente normal

## **RNF-005 — Mantenibilidad y Estándares Técnicos**

**Módulo:** Transversal

**Descripción**

El código del sistema debe desarrollarse siguiendo los principios SOLID para garantizar que el MVP sea extensible sin necesidad de reescrituras estructurales cuando el sistema evolucione después del proyecto nuclear. La arquitectura debe separar claramente el frontend del backend con comunicación mediante APIs REST, y todos los endpoints del backend deben estar documentados con Swagger/OpenAPI. Este requisito es especialmente relevante para la asignatura de Arquitectura de Software I, que verificará su cumplimiento en el Corte 3 mediante una evaluación arquitectónica formal y un informe de refactorización y deuda técnica.

**Reglas de Negocio Aplicables**

* No aplican reglas de negocio de dominio directamente. Este requisito se deriva de los estándares técnicos establecidos en la sección 6.5 del informe de elicitación y de los entregables académicos definidos en la guía del seminario nuclear.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Mantenibilidad y estándares técnicos

### Scenario 1: La arquitectura del sistema separa frontend y backend con APIs REST

**Given (Dado que):**
- El sistema está implementado y desplegado

**When (Cuando):**
- Se analiza la estructura del proyecto en el repositorio

**Then (Entonces):**
- Existe una separación clara entre el proyecto de frontend y el de backend como unidades independientes
- Toda la comunicación entre frontend y backend ocurre exclusivamente a través de endpoints REST documentados
- No existe lógica de negocio embebida directamente en el frontend

---

### Scenario 2: Los endpoints del backend están documentados con Swagger

**Given (Dado que):**
- El sistema está desplegado en el entorno de producción

**When (Cuando):**
- Se accede a la ruta de documentación Swagger del backend

**Then (Entonces):**
- Todos los endpoints disponibles están listados y documentados con su método HTTP, parámetros esperados, cuerpo de la solicitud y estructura de la respuesta
- La documentación refleja el estado actual del backend sin endpoints faltantes ni documentación desactualizada

---

### Scenario 3: El código cumple con los principios SOLID verificables

**Given (Dado que):**
- El equipo de Arquitectura de Software I realiza la evaluación formal del Corte 3

**When (Cuando):**
- Analiza la estructura de clases, servicios y módulos del backend

**Then (Entonces):**
- Cada clase o componente tiene una única responsabilidad claramente definida (SRP)
- Es posible extender el comportamiento del sistema sin modificar clases existentes (OCP)
- El sistema no presenta dependencias directas entre módulos de alto y bajo nivel (DIP)
- El informe de evaluación no identifica violaciones críticas no justificadas a ninguno de los cinco principios SOLID

## **RNF-006 — Cumplimiento Legal: Ley 1581 de 2012**

**Módulo:** Transversal

**Descripción**

El tratamiento de datos operativos y comerciales de ICM, así como los datos personales de clientes capturados durante las ventas mayoristas (nombre, correo, teléfono, dirección), debe cumplir estrictamente con la Ley 1581 de 2012, que es la Ley de Protección de Datos Personales de Colombia. Este requisito no es opcional ni negociable: es una obligación legal que aplica desde el primer momento en que el sistema captura un dato personal real de un cliente o empleado. El equipo de desarrollo debe obtener además autorización expresa de ICM para el uso de sus datos operativos reales en el contexto del proyecto académico, antes de iniciar cualquier prueba con información real de la empresa.

**Reglas de Negocio Aplicables**

* No aplican reglas de negocio de dominio directamente. Este requisito se deriva de la Ley 1581 de 2012 y de las consideraciones éticas establecidas tanto en el informe de elicitación como en la guía académica del seminario nuclear.

**Criterios de Aceptación (Formato Gherkin)**

Feature: Cumplimiento legal con la Ley 1581 de 2012

### Scenario 1: El sistema captura datos personales de clientes mayoristas con aviso de privacidad

**Given (Dado que):**
- Un operario registra los datos de un cliente mayorista durante un despacho

**When (Cuando):**
- Completa el formulario con nombre, correo, teléfono y dirección

**Then (Entonces):**
- El sistema informa al operario, antes de guardar los datos, que esa información será tratada conforme a la política de privacidad de ICM bajo la Ley 1581 de 2012
- No almacena los datos del cliente sin que ese aviso haya sido presentado en el flujo

---

### Scenario 2: Los datos personales de clientes no son accesibles para el Auxiliar de Despacho fuera del contexto de su operación

**Given (Dado que):**
- El sistema tiene almacenados datos personales de clientes mayoristas

**When (Cuando):**
- Un Auxiliar de Despacho intenta consultar el historial de clientes fuera del contexto de un despacho activo

**Then (Entonces):**
- El sistema no expone listados de datos personales de clientes a ese rol
- El acceso a esa información está restringido al Almacenista y al Administrador dentro del módulo de reportes

---

### Scenario 3: El equipo documenta la autorización de ICM antes de usar datos reales en pruebas

**Given (Dado que):**
- El equipo de desarrollo va a ejecutar pruebas de aceptación usando datos operativos reales de ICM en el Corte 3

**When (Cuando):**
- Se planifica la fase de pruebas de aceptación

**Then (Entonces):**
- El equipo debe contar con un documento de autorización expresa firmado por ICM que permita el uso de sus datos operativos en el contexto académico del proyecto
- Las pruebas con datos reales no deben ejecutarse hasta que esa autorización esté formalmente obtenida

# **7. Resumen de Trazabilidad Requisitos — Módulos**

La siguiente tabla presenta un resumen de todos los requisitos especificados en este documento, con su módulo de pertenencia y las reglas de negocio que les aplican directamente. Esta tabla constituye el punto de partida para la Matriz de Trazabilidad Requisitos-Pruebas que debe ser elaborada por la asignatura de Pruebas de Software como entregable del Corte 1.

| **ID** | **Nombre** | **Módulo** | **Reglas de Negocio** |
| --- | --- | --- | --- |
| RF-001 | Inicio de Sesión con Credenciales Únicas | Autenticación | BR-01, BR-03 |
| RF-002 | Gestión de Credenciales de Usuario | Autenticación | BR-01, BR-02 |
| RF-003 | Registro de Producto en el Catálogo (SKU) | Gestión de Inventario | BR-04, BR-11, BR-12, BR-13 |
| RF-004 | Consulta y Búsqueda de Inventario en Tiempo Real | Gestión de Inventario | BR-11, BR-13, BR-14, BR-15 |
| RF-005 | Recepción de Mercancía | Recepción de Mercancía | BR-04, BR-09, BR-10, BR-11, BR-13, BR-14 |
| RF-006 | Despacho y Salidas de Inventario | Despacho y Salidas | BR-08, BR-10, BR-11, BR-13, BR-14 |
| RF-007 | Movimientos Internos entre Ubicaciones | Movimientos Internos | BR-06, BR-10, BR-11, BR-14 |
| RF-008 | Registro de Devoluciones de Productos | Devoluciones | BR-02, BR-05, BR-10, BR-14 |
| RF-009 | Ajustes de Inventario | Ajustes de Inventario | BR-06, BR-07, BR-10, BR-11, BR-14 |
| RF-010 | Reportes e Indicadores Operativos | Reportes e Indicadores | BR-10, BR-11, BR-13 |
| RF-011 | Alertas Proactivas del Sistema | Alertas Proactivas | BR-04, BR-10, BR-11 |
| RF-012 | Log de Auditoría y Trazabilidad | Auditoría y Trazabilidad | BR-01, BR-06, BR-07, BR-10 |
| RF-013 | Precios y Facturación Comercial | Precios y Facturación | BR-13, BR-16, BR-17 |
| RNF-001 | Usabilidad e Interfaz Intuitiva | Transversal | — |
| RNF-002 | Disponibilidad del Sistema | Transversal | BR-03 |
| RNF-003 | Seguridad e Integridad de Datos | Transversal | BR-01, BR-02, BR-10 |
| RNF-004 | Rendimiento en Consultas y Operaciones | Transversal | — |
| RNF-005 | Mantenibilidad y Estándares Técnicos | Transversal | — |
| RNF-006 | Cumplimiento Legal: Ley 1581 de 2012 | Transversal | — |

# **8. Conclusiones**

El presente documento centraliza la especificación completa de dieciocho requisitos —doce funcionales y seis no funcionales— para el sistema de gestión de inventario y operaciones de Import Corporal Medical. Cada requisito ha sido elaborado a partir de la información recogida durante el proceso de elicitación con los responsables operativos de ICM y alineado con las condiciones académicas del Proyecto Nuclear 3.

Los requisitos funcionales cubren la totalidad de los módulos identificados en la elicitación: autenticación y gestión de credenciales, gestión de inventario, recepción de mercancía, despacho y salidas, movimientos internos, devoluciones, ajustes de inventario, reportes e indicadores, alertas proactivas y auditoría. Los requisitos no funcionales complementan esta especificación con atributos de calidad medibles en usabilidad, disponibilidad, seguridad, rendimiento, mantenibilidad y cumplimiento legal.

La redacción de los criterios de aceptación en formato Gherkin responde a una decisión deliberada orientada a facilitar el trabajo de la asignatura de Pruebas de Software: cada escenario puede ser convertido directamente en un caso de prueba sin necesidad de reinterpretación, lo que reduce el margen de error entre lo que el sistema debe hacer y lo que efectivamente se verifica en las fases de prueba.

Este documento debe ser considerado un artefacto vivo durante el desarrollo del proyecto: cualquier cambio en los requisitos acordado con el cliente funcional (estudiantes de Ingeniería Industrial) debe quedar registrado mediante una nueva versión del documento, garantizando la trazabilidad de los cambios a lo largo de los tres cortes académicos del período I-2026.

# **9. Referencias Bibliográficas**

* [1] Pressman, R. S. y Maxim, B. R. (2021). Ingeniería del software: Un enfoque práctico (9.ª ed.). McGraw-Hill.
* [2] Bass, L., Clements, P. y Kazman, R. (2021). Software Architecture in Practice (4.ª ed.). Addison-Wesley.
* [3] Myers, G. J., Sandler, C. y Badgett, T. (2011). The Art of Software Testing (3.ª ed.). Wiley.
* [4] Ballou, R. H. (2004). Logística: Administración de la cadena de suministro (5.ª ed.). Pearson Educación.
* [5] Schwaber, K. y Sutherland, J. (2020). La Guía Scrum. Recuperado de https://scrumguides.org
* [6] Congreso de Colombia. (2012). Ley 1581 de 2012 — Protección de Datos Personales. Diario Oficial.
* [7] IEEE. (1998). IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications. Institute of Electrical and Electronics Engineers.