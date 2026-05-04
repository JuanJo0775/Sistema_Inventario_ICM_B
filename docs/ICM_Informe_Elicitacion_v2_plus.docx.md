**Informe de Elicitacion**

**Sistema de Gestión de Inventario y Operaciones**

Import Corporal Medical (ICM)

Proyecto Nuclear 3 — Corporación Universitaria Alexander von Humboldt

# 1. Introducción y Contexto del Proyecto

El presente documento constituye el Informe de Especificación de Requerimientos para el sistema de gestión de inventario y operaciones de Import Corporal Medical (ICM), elaborado en el marco del Proyecto Nuclear 3 de la Corporación Universitaria Alexander von Humboldt. Este informe integra la información obtenida durante las sesiones de elicitación de requisitos con los responsables operativos de ICM y la guía académica del seminario nuclear, cuyo objetivo es el desarrollo de un Producto Mínimo Viable (MVP) que digitalice y centralice la gestión logística de la empresa.

El proyecto articula las asignaturas de Arquitectura de Software I, Programación con Tecnologías Web y Pruebas de Software, con la participación activa de estudiantes de Ingeniería Industrial en calidad de clientes funcionales y asesores del dominio logístico. La solución resultante debe transformar los procesos manuales de ICM en flujos de datos auditables, garantizando consistencia del inventario en tiempo real, trazabilidad nominal de cada movimiento y visibilidad gerencial mediante indicadores clave de operación.

# 2. Contexto del Negocio: Import Corporal Medical

Import Corporal Medical es una empresa importadora y distribuidora de insumos médicos especializados para fisioterapeutas. Su modelo de negocio se basa en la importación directa de productos desde fabricantes en China bajo la marca propia denominada "Can" (estrategia de Private Label), lo cual simplifica la gestión de proveedores al centralizar el catálogo bajo una única marca y facilita el control de calidad en la recepción de mercancía.

El catálogo activo de ICM comprende aproximadamente 220 productos distribuidos en tres macro-categorías: Electroterapia, Manoterapia y Mesas de Fisioterapia. La alta similitud morfológica entre algunos productos del mismo segmento —por ejemplo, pelotas de gel redondas frente a ovaladas, o distintos tipos de agujas— genera errores recurrentes en el despacho cuando el proceso de selección es manual. Esta realidad convierte la validación cruzada entre pedido y producto físico en un requerimiento crítico del sistema.

La operación logística se distribuye en tres puntos de almacenamiento físico: una Vitrina destinada a la venta minorista y dos Bodegas Base orientadas al almacenamiento mayorista. Actualmente, ICM gestiona el inventario a través de hojas de cálculo (Google Sheets o Excel), lo que genera brechas constantes entre el stock físico y el registro digital, imposibilita la trazabilidad nominal de los movimientos y limita la capacidad de respuesta ante consultas de clientes durante negociaciones comerciales.

# 3. Actores, Roles y Modelo de Acceso

El sistema implementará un modelo de Control de Acceso Basado en Roles (RBAC) que garantiza la segregación de funciones y la trazabilidad de cada transacción hasta el usuario responsable. Se definen tres roles con permisos y restricciones horarias diferenciados.

## 3.1 Matriz de Roles y Permisos

|  |  |  |  |
| --- | --- | --- | --- |
| **Rol** | **Responsabilidades Clave** | **Permisos** | **Restricción Horaria** |
| Almacenista (Coordinador) | Supervisión total, integridad del stock, gestión de maestros y credenciales, auditoría. | Visualización, edición, ajustes de inventario, gestión de credenciales, auditoría de logs. | Acceso 24/7 |
| Auxiliar de Despacho (2 cupos) | Ejecución de flujos de entrada, salida y movimientos internos entre almacenes. | Registro de movimientos, visualización de stock. | 07:00–12:00 / 14:00–17:00 |
| Administrador / Jefe | Monitoreo estratégico y análisis de indicadores operativos. | Visualización de stock, módulo de reportes y KPIs. Sin permisos de edición. | Acceso 24/7 (solo dashboard) |

## 3.2 Reglas de Negocio sobre Identidad y Acceso

Las siguientes reglas de negocio son de obligatorio cumplimiento para todos los usuarios del sistema:

* BR-01 (Identidad única): Está prohibido el uso de cuentas compartidas. Cada transacción registrada en el sistema debe estar vinculada de manera unívoca al identificador de usuario (UserID) del empleado que la ejecutó. Esto garantiza la trazabilidad nominal e inmutable de los movimientos.
* BR-02 (Gestión de credenciales): El Almacenista es el único rol facultado para crear, editar o inhabilitar credenciales de acceso. Los perfiles de Auxiliar de Despacho no pueden ser modificados por ellos mismos. Esto previene escalaciones de privilegios no autorizadas.
* BR-03 (Restricción horaria para despacho): Los Auxiliares de Despacho solo pueden acceder al sistema en las franjas operativas definidas: 07:00–12:00 y 14:00–17:00. Fuera de estas ventanas, el sistema debe bloquear el acceso para este rol. El Almacenista y el Administrador tienen acceso permanente.

# 4. Entidades del Sistema

El sistema operará sobre un conjunto de entidades centrales que representan los objetos del dominio logístico de ICM. A continuación se describen cada una con sus atributos y relaciones.

## 4.1 Producto (SKU)

El producto es la entidad central del sistema. Cada ítem del catálogo de ICM debe estar identificado de forma unívoca mediante un código de barras o QR, y debe contener los atributos necesarios para su gestión logística, de calidad y de trazabilidad. La tabla siguiente describe los atributos obligatorios y condicionales por producto:

|  |  |  |
| --- | --- | --- |
| **Atributo** | **Descripción** | **Obligatorio** |
| Código (Barcode/QR) | Código de barras físico impreso en el empaque del producto. Se almacena como atributo adicional del SKU y actúa como alias de escaneo: cuando el lector HID lo captura o el operario lo ingresa manualmente, el sistema lo resuelve internamente al SKU correspondiente. No reemplaza al SKU ni a los demás identificadores del producto; coexiste con ellos como vía de acceso rápido. | Sí |
| Nombre del producto | Nombre descriptivo. Junto al código permite autocompletado en búsquedas. | Sí |
| Categoría / Subcategoría | Clasificación jerárquica: Electroterapia, Manoterapia o Mesas de Fisioterapia. | Sí |
| Código serial | Identificador único por unidad física. Solo obligatorio para productos de Electroterapia. | Electroterapia |
| Fecha de vencimiento | Fecha límite de uso. Activa alertas a 30 y 60 días antes del vencimiento. | Sí |
| Stock por ubicación | Cantidad disponible en cada punto: Vitrina, Bodega 1, Bodega 2. El stock total es la suma de los tres. | Sí |
| Nota de cadena de frío | Alerta visual persistente en la interfaz de picking cuando el producto requiere refrigeración. | Condicional |
| Peso unitario | En gramos o kilogramos. Usado para calcular capacidad de transporte por despacho. | Sí |

Los productos de la marca propia deben incluir el prefijo "CAN-" en su código de SKU para diferenciarlos de cualquier importación de terceros. El sistema debe soportar además la agrupación de múltiples SKUs bajo un identificador de "Combo" o Kit, permitiendo el despacho simultáneo de paquetes de terapia como una sola unidad de salida.

## 4.2 Almacén / Ubicación

ICM opera bajo un modelo de almacenaje caótico, en el que un mismo producto puede estar físicamente distribuido en más de una ubicación simultáneamente. El sistema debe soportar esta realidad registrando la cantidad disponible de cada SKU por punto de almacenamiento, en lugar de limitar un producto a una única ubicación.

Los tres puntos de almacenamiento definidos son: la Vitrina (exhibición y venta minorista), la Bodega Base 1 (almacenamiento masivo) y la Bodega Base 2 (almacenamiento masivo). El Stock Total de cada producto es la sumatoria dinámica de las cantidades registradas en los tres puntos. El campo de ubicación es obligatorio en cada registro de movimiento para mantener la consistencia del modelo caótico.

## 4.3 Proveedor

El sistema debe incluir un módulo de gestión CRUD (Crear, Leer, Actualizar, Eliminar) para proveedores. Dado que ICM trabaja principalmente bajo marca propia con fábricas en China, los atributos mínimos del proveedor deben incluir: nombre o razón social, país de origen, correo electrónico de contacto y teléfono. Esta entidad se vincula directamente al módulo de recepción de mercancía, donde cada entrada debe registrar el origen de los productos (proveedor externo o marca propia "Can").

## 4.4 Cliente (para ventas mayoristas)

Para las salidas clasificadas como Venta al por Mayor, el sistema debe capturar y almacenar los datos del cliente receptor. Los atributos requeridos son: nombre o razón social, correo electrónico, teléfono y dirección de entrega. Esta información alimenta tanto el registro de auditoría de despachos como los reportes de ventas por período. Para ventas al por menor o minoristas, el registro del cliente es opcional.

## 4.5 Movimiento de Inventario

El movimiento es la entidad transaccional del sistema. Cada operación que afecte el stock —ya sea una entrada, una salida, un traslado interno o un ajuste— debe generar un registro de movimiento con los siguientes campos mínimos: identificador único del movimiento, timestamp (fecha y hora exacta), UserID del operario responsable, tipo de transacción, SKU y código serial involucrado (cuando aplique), ubicación de origen, ubicación de destino, cantidad, stock previo y stock resultante, así como una nota o justificación en caso de ajustes o discrepancias. Este registro es inmutable una vez cerrada la ventana de corrección.

# 5. Requerimientos Funcionales

Los requerimientos funcionales describen los comportamientos específicos que el sistema debe exhibir ante determinadas condiciones de operación. Se organizan por módulo operativo.

## 5.1 Módulo de Autenticación y Gestión de Credenciales

El sistema debe implementar un mecanismo de autenticación seguro que permita el ingreso individual de cada usuario mediante credenciales únicas (usuario y contraseña). El Almacenista tendrá la facultad exclusiva de crear nuevas cuentas, asignar roles, modificar contraseñas y deshabilitar accesos cuando sea necesario. El sistema debe redirigir automáticamente a cada usuario a la vista correspondiente a su rol una vez autenticado. Para los Auxiliares de Despacho, el sistema debe verificar la franja horaria al momento del inicio de sesión y bloquear el acceso si se intenta ingresar fuera del horario permitido.

## 5.2 Módulo de Gestión de Inventario

Este módulo centraliza la consulta y visualización del estado actual del stock. Debe ofrecer una interfaz con filtros dinámicos multinivel que permitan navegar desde la categoría general hasta el SKU específico (por ejemplo: Categoría "Agujas" → Subcategoría "Agujas de Punción Seca" → SKU específico). Esta capacidad de filtrado es crítica para agilizar la atención al cliente durante negociaciones comerciales, donde el vendedor necesita consultar disponibilidad en tiempo real.

El sistema debe mostrar el stock por ubicación (Vitrina, Bodega 1, Bodega 2) y el stock total consolidado. Adicionalmente, debe desplegar alertas visuales persistentes sobre los productos que requieren cadena de frío o manejo especial por ser equipos eléctricos, como parte de las medidas de seguridad operativa.

## 5.3 Módulo de Recepción de Mercancía (Entradas)

Este módulo gestiona el ingreso de productos al inventario, ya sea por compra a proveedor externo o por reposición de marca propia. El flujo de recepción contempla los siguientes pasos y validaciones:

1. El operario inicia el registro de entrada seleccionando el producto mediante escaneo de código de barras o búsqueda por nombre con autocompletado. Ambas vías deben estar disponibles de forma equivalente, de modo que si no se dispone de lector, la búsqueda por nombre sea igualmente eficiente.
2. El sistema solicita la cantidad recibida. El operario la ingresa y el sistema la compara con la cantidad facturada o esperada según la orden de compra. Si existe discrepancia (llegó menos o más de lo acordado), el sistema debe permitir registrar una nota de discrepancia obligatoria que quede vinculada al movimiento de entrada.
3. Si el producto pertenece a la categoría de Electroterapia, el sistema exige el ingreso del número de serie de cada unidad antes de confirmar la entrada. Este campo es mandatorio y el sistema no debe permitir registrar la entrada si está vacío para esta categoría.
4. El operario debe seleccionar la ubicación de destino (Vitrina, Bodega 1 o Bodega 2) para cada producto recibido. El sistema actualiza el stock de esa ubicación y recalcula el stock total.
5. El sistema registra el movimiento con todos los atributos descritos en la entidad "Movimiento de Inventario", incluyendo el UserID del operario y el timestamp exacto.

## 5.4 Módulo de Despacho y Salidas

Este módulo gestiona todos los egresos de productos desde el inventario de ICM. Cada salida debe clasificarse obligatoriamente en una de las siguientes categorías, ya que cada tipo tiene implicaciones distintas en la auditoría y los reportes:

* Venta al por Mayor: Requiere el registro completo del cliente receptor (nombre o razón social, correo, teléfono, dirección). El sistema suma el peso unitario de todos los ítems del despacho y emite una advertencia si la carga total excede la capacidad máxima del vehículo de transporte configurado para esa ruta.
* Venta al por Menor: Salida unitaria o en pequeñas cantidades hacia la Vitrina o directamente al cliente minorista. El registro del cliente es opcional.
* Daño: Baja de producto por deterioro físico detectado en bodega. Debe incluir una nota descriptiva del daño y el número de unidades afectadas. El stock se descuenta pero el movimiento queda registrado como baja por daño, no como venta.
* Vencimiento: Baja de producto por caducidad. El sistema debe facilitar esta operación mostrando los productos próximos a vencer según las alertas configuradas. El registro incluye la fecha de vencimiento del lote afectado.

Independientemente del tipo de salida, el sistema debe ejecutar una validación cruzada entre el producto solicitado en la orden y el código escaneado físicamente al momento del despacho. Si el código escaneado no coincide con el SKU de la orden, el sistema debe bloquear la operación y mostrar un mensaje de error descriptivo. Esta validación es el mecanismo central para prevenir errores de despacho como el envío de un producto por otro similar.

**Integración con lector de código de barras para registro de salidas por venta:** El sistema debe soportar la conexión de un lector de código de barras externo operando en modo HID (Human Interface Device), por conexión USB o Bluetooth. En este modo, el lector se comporta como un teclado virtual: al escanear el código impreso en el empaque del producto, el dispositivo escribe automáticamente el valor del código de barras en el campo activo del formulario de despacho. El sistema recibe ese valor como texto, lo consulta contra el atributo “Código de barras” registrado en la ficha del producto, resuelve internamente la correspondencia con el SKU y autocompleta los demás datos del ítem (nombre, categoría, ubicación de origen, stock disponible) sin intervención manual adicional. Es fundamental entender que el código de barras no reemplaza al SKU ni a ningún otro identificador del producto: es simplemente un alias de escaneo almacenado como atributo adicional en la entidad Producto, que el sistema utiliza como puente entre el mundo físico (etiqueta impresa) y el mundo digital (SKU interno). Cuando el lector no está disponible, el operario puede ingresar el producto por cualquiera de las siguientes vías de forma equivalente: escribir manualmente el código de barras, ingresar el SKU directamente, ingresar cualquier otro código de identificación asociado al producto (como el código serial en el caso de Electroterapia), o buscar por nombre con autocompletado. Todas estas vías deben desembocar en el mismo resultado: la identificación unívoca del producto y el autocompletado del formulario. Si el lector no es reconocido por el navegador o no está conectado, el sistema debe notificarlo de forma visible pero no debe interrumpir el flujo de despacho bajo ninguna circunstancia.

**Generación y exportación de factura digital en PDF:** Una vez confirmado el despacho —independientemente del tipo de salida (Venta al por Mayor, Venta al por Menor, Daño o Vencimiento)— el sistema debe generar automáticamente un documento de factura o remisión en formato digital, almacenarlo de forma persistente y ponerlo a disposición del usuario para su descarga inmediata en formato PDF. El documento debe incluir como mínimo: número de factura o remisión generado automáticamente y de forma secuencial, fecha y hora exacta del despacho, datos del operario que confirmó la salida (nombre y rol), datos del cliente receptor cuando aplique (nombre o razón social, correo, dirección), listado detallado de los productos despachados con su SKU, descripción, cantidad y ubicación de origen, y el peso total calculado del despacho. El sistema debe conservar el historial de facturas generadas, permitiendo su consulta posterior desde el módulo de reportes filtrando por período, tipo de salida o cliente. Esta funcionalidad garantiza la trazabilidad documental de cada operación de egreso y facilita la integración con los procesos contables externos de ICM.

## 5.5 Módulo de Movimientos Internos

Los traslados internos corresponden al flujo de productos entre los puntos de almacenamiento de ICM (Vitrina, Bodega 1 y Bodega 2) sin que ello implique una venta o salida definitiva de la empresa. Este tipo de movimiento actualiza la ubicación del producto en el sistema, restando la cantidad de la ubicación de origen y sumándola a la ubicación de destino, pero no modifica el stock total global de ICM.

El registro de un traslado interno debe incluir: producto, cantidad, ubicación de origen, ubicación de destino, UserID del operario y timestamp. El sistema debe impedir que un traslado genere stock negativo en la ubicación de origen, validando disponibilidad antes de confirmar la operación.

## 5.6 Módulo de Devoluciones

Las devoluciones representan el reingreso de productos al inventario de ICM provenientes de clientes externos. Esta operación está sujeta a una restricción de negocio de alta importancia: únicamente los productos de la categoría Electroterapia o Electrónicos pueden ser objeto de devolución. El sistema debe bloquear automáticamente cualquier intento de registrar una devolución para productos de manoterapia (agujas, geles, etc.) o mesas de fisioterapia, informando al operario la causa del bloqueo.

Toda devolución de producto eléctrico debe pasar por un proceso de auditoría previo a la reincorporación al stock. El sistema debe generar un log inmutable de cada devolución que incluya: el producto devuelto (SKU y número de serie), el motivo declarado por el cliente, el estado del producto al recibirlo, el UserID del operario que registró la devolución y el timestamp. La reincorporación definitiva al stock disponible debe requerir aprobación del Almacenista.

## 5.7 Módulo de Ajustes de Inventario

Los ajustes de inventario permiten corregir discrepancias entre el stock físico real y el registrado en el sistema, cuando dichas diferencias no pueden resolverse mediante las operaciones estándar de entrada, salida o traslado. Este módulo está restringido al rol de Almacenista (Coordinador), quien es el único habilitado para ejecutar ajustes.

Cada ajuste debe incluir una justificación obligatoria que explique la causa de la discrepancia (por ejemplo: "Error humano en despacho: pelotas redondas por ovaladas" o "Diferencia detectada en conteo físico periódico"). El sistema debe generar un log inmutable del ajuste con todos los campos de la entidad Movimiento de Inventario, incluyendo el delta entre el stock previo y el stock ajustado. No existe posibilidad de eliminar un ajuste registrado; cualquier corrección de un ajuste erróneo debe realizarse mediante un nuevo ajuste con su correspondiente justificación.

Existe una ventana de autocorrección para los Auxiliares de Despacho: si un error se detecta dentro de la misma franja horaria en que ocurrió (07:00–12:00 o 14:00–17:00), el propio auxiliar puede editar el registro antes de que se cierre la ventana. Una vez cerrada la franja horaria, el registro queda inmutable y cualquier corrección posterior debe tramitarse como un Ajuste de Inventario formal por parte del Almacenista.

## 5.8 Módulo de Reportes e Indicadores

El sistema debe contar con un módulo de reportes y dashboard gerencial que transforme los datos operativos en información estratégica de valor. Los reportes deben ser accesibles para el rol de Administrador/Jefe y el Almacenista, y deben poder exportarse en formato Excel o CSV para ser integrados con el software contable externo de ICM. Adicionalmente, el módulo debe centralizar el historial de facturas y remisiones generadas desde el módulo de despacho, permitiendo su consulta, filtrado por período o tipo de salida, y descarga individual en formato PDF.

Los tipos de reporte disponibles deben incluir como mínimo: reporte de ventas por período (diario, semanal, mensual o con rango personalizado); historial de movimientos por operario, que permita consultas del tipo "Historial de agujas despachadas por operario X"; reporte de rotación de inventario por categoría; reporte de productos próximos a vencer; y reporte de productos con stock por debajo del punto de reorden.

Los indicadores clave de operación (KPIs) que el dashboard debe consolidar son: índice de rotación de inventario por categoría (con gráficos de tendencia); porcentaje de ocupación por zona de almacenamiento; nivel de servicio (porcentaje de pedidos despachados completos y a tiempo); y panel de alertas operativas en tiempo real (vencimientos, stock mínimo, pedidos pendientes).

## 5.9 Módulo de Alertas Proactivas

El sistema debe emitir alertas automáticas ante condiciones operativas que requieran atención inmediata o preventiva. Las alertas definidas son las siguientes:

* Alerta de stock mínimo: El sistema calcula el punto de reorden de cada producto basándose en su rotación mensual. Cuando el stock total de un SKU cae por debajo del umbral definido, el sistema emite una notificación visible en el dashboard y en el módulo de inventario.
* Alerta de vencimiento próximo: El sistema emite notificaciones a 60 y a 30 días antes de la fecha de vencimiento de cualquier lote registrado, permitiendo planificar la rotación o baja del producto con anticipación.
* Alerta de cadena de frío: Para productos que requieren refrigeración, el sistema despliega un aviso visual persistente y de alta visibilidad cada vez que se registra un movimiento que involucra dichos productos, recordando al operario las condiciones especiales de manejo.
* Alerta de seguridad eléctrica: De manera análoga a la cadena de frío, el sistema emite una advertencia visual al registrar movimientos de equipos eléctricos, informando sobre los protocolos de manejo seguro aplicables.

# 6. Requerimientos No Funcionales

Los requerimientos no funcionales definen los atributos de calidad que el sistema debe cumplir para ser operativamente viable en el contexto real de ICM.

## 6.1 Usabilidad

El sistema debe diseñarse bajo el principio KISS (Keep It Simple, Stupid), priorizando una interfaz intuitiva que pueda ser operada por personal de bodega sin formación técnica especializada. La búsqueda de productos debe ser ágil y accesible tanto por código de barras como por nombre con autocompletado. La interfaz debe ser responsiva y optimizada para dispositivos móviles, dado que los operarios realizarán consultas y registros directamente desde la bodega usando tabletas o teléfonos con lector de código integrado.

## 6.2 Disponibilidad

El sistema debe garantizar disponibilidad continua durante las franjas horarias de operación de los Auxiliares de Despacho (07:00–12:00 y 14:00–17:00), siendo estas las ventanas críticas donde cualquier interrupción impacta directamente el cumplimiento de despachos. Para el Almacenista y el Administrador, el sistema debe estar disponible las 24 horas del día, los 7 días de la semana.

## 6.3 Seguridad e Integridad de Datos

El sistema debe implementar cifrado de datos sensibles tanto en tránsito como en reposo. El modelo RBAC descrito en la sección 3 garantiza que ningún usuario acceda a funcionalidades fuera de su alcance. Los logs de auditoría deben ser inmutables: ningún usuario, incluyendo el Almacenista, debe poder eliminar o modificar un registro histórico una vez confirmado. La trazabilidad nominal es un atributo de calidad no negociable del sistema.

## 6.4 Rendimiento

Las consultas de stock en tiempo real deben responder en un tiempo razonable que no interrumpa el flujo de trabajo durante la atención al cliente. Dado que el catálogo comprende entre 220 y 250 productos y los tres puntos de almacenamiento, las consultas de inventario no deberían superar los 2 segundos bajo condiciones normales de uso.

## 6.5 Mantenibilidad y Estándares Técnicos

El código del sistema debe desarrollarse siguiendo los principios SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation y Dependency Inversion), garantizando que el MVP sea extensible sin necesidad de reescrituras estructurales. Los endpoints del backend deben estar documentados mediante Swagger/OpenAPI. El sistema debe construirse como una aplicación web con arquitectura separada de frontend y backend, con comunicación mediante APIs REST.

## 6.6 Cumplimiento Legal

El tratamiento de datos operativos y comerciales de ICM, así como los datos de clientes capturados durante las ventas mayoristas, debe cumplir estrictamente con la Ley 1581 de 2012 (Ley de Protección de Datos Personales de Colombia). Es responsabilidad del equipo de desarrollo implementar las políticas de privacidad y consentimiento correspondientes, y obtener autorización expresa de ICM para el uso de sus datos operativos en el contexto académico del proyecto.

# 7. Consolidación de Reglas de Negocio

A continuación se listan todas las reglas de negocio identificadas durante la elicitación, organizadas para servir como referencia directa durante el diseño y desarrollo del sistema:

* BR-01 (Identidad única): Prohibido el uso de cuentas compartidas. Cada transacción debe estar vinculada a un UserID único.
* BR-02 (Gestión de credenciales): Solo el Almacenista puede crear, modificar o deshabilitar cuentas de usuario.
* BR-03 (Restricción horaria): Los Auxiliares de Despacho solo acceden al sistema entre las 07:00–12:00 y 14:00–17:00.
* BR-04 (Obligatoriedad de serial en Electroterapia): El campo "Número de Serie" es mandatorio en toda entrada de productos de la categoría Electroterapia.
* BR-05 (Devoluciones restringidas): Solo los productos de la categoría Electroterapia o Electrónicos admiten devoluciones. El sistema bloquea automáticamente cualquier devolución de otro tipo de producto.
* BR-06 (Ventana de autocorrección): Un Auxiliar de Despacho puede editar un movimiento que registró dentro de la misma franja horaria activa. Al cerrar la franja, el registro se vuelve inmutable.
* BR-07 (Ajuste con justificación): Todo ajuste de inventario fuera de la ventana de autocorrección requiere justificación obligatoria y es ejecutado exclusivamente por el Almacenista.
* BR-08 (Validación cruzada en despacho): El sistema verifica que el código escaneado en el despacho coincida con el SKU de la orden antes de confirmar la salida. Si no coincide, bloquea la operación.
* BR-09 (Nota de discrepancia en recepción): Si la cantidad recibida difiere de la facturada, el operario debe registrar una nota de discrepancia antes de confirmar la entrada.
* BR-10 (Inmutabilidad del log): Los registros históricos de movimientos, ajustes, devoluciones y auditorías no pueden ser eliminados ni modificados por ningún usuario.
* BR-11 (Stock por ubicación): El stock total es la sumatoria dinámica de las cantidades en Vitrina, Bodega 1 y Bodega 2. Los traslados internos no modifican el stock total global.
* BR-12 (Prefijo de marca propia): Los productos de la marca "Can" deben llevar el prefijo "CAN-" en su código SKU.
* BR-13 (Código de barras como alias de escaneo y factura digital): Cada producto del catálogo puede tener registrado un código de barras físico como atributo adicional en su ficha (junto al SKU, código serial y demás identificadores). Este código actúa como alias de escaneo: cuando un lector HID lo captura, el sistema lo resuelve internamente al SKU correspondiente y autocompleta el formulario. El operario también puede ingresarlo de forma manual, junto con el SKU, el nombre u otros códigos asociados, como vías de entrada equivalentes que no rompen el modelo de datos existente. La ausencia del lector físico no debe bloquear ningún flujo del sistema. Adicionalmente, todo despacho confirmado debe generar automáticamente una factura o remisión digital con numeración secuencial, almacenarla de forma persistente y ponerla a disposición del usuario para su descarga en formato PDF. El historial de facturas debe ser consultable desde el módulo de reportes.

# 8. Hoja de Ruta de Implementación

El proyecto se ejecuta bajo el marco de trabajo Scrum, con sprints alineados a los tres cortes académicos del período comprendido entre el 21 de abril y el 26 de junio de 2026. Los estudiantes de Ingeniería Industrial actúan como Product Owners y participan en las ceremonias de Scrum (planning, review y retrospectiva).

## Corte 1 — Análisis, Arquitectura y Prototipos

En esta fase se define la arquitectura base del sistema, se elabora el Product Backlog priorizado, se diseñan los wireframes y prototipos interactivos de las pantallas principales, y se implementa el sistema de autenticación y gestión de roles (frontend y backend funcional). La asignatura de Pruebas de Software entrega el Plan Maestro de Pruebas y la Matriz de Trazabilidad requisitos-pruebas. Los entregables son validados por los estudiantes de Ingeniería Industrial como usuarios funcionales del dominio.

## Corte 2 — Núcleo Funcional y Primeras Pruebas

Se implementan los módulos de gestión de inventario, recepción y despacho con sus respectivas interfaces. Se validan los principios arquitectónicos KISS, DRY y YAGNI. Pruebas de Software ejecuta las primeras pruebas unitarias y de integración, generando un informe de cobertura y un registro estructurado de defectos clasificados por severidad y prioridad.

## Corte 3 — Integración, Reportes, Pruebas de Aceptación y Despliegue

Se completa el módulo de indicadores, reportes y alertas operativas en tiempo real. Se documenta la API con Swagger. Arquitectura de Software I verifica la aplicación de principios SOLID y produce un informe de refactorización y deuda técnica. Pruebas de Software ejecuta el plan completo (funcionales, rendimiento, seguridad y aceptación), con las pruebas de aceptación conducidas por los estudiantes de Ingeniería Industrial en el entorno operativo real de ICM. Se realiza el despliegue del MVP y se genera el informe final de calidad.

# 9. Consideraciones Éticas y Disciplinarias

El desarrollo de este sistema implica el manejo de información operativa y comercial sensible de ICM. El equipo de desarrollo debe obtener autorización expresa de la empresa para el uso de datos operativos en el contexto académico y debe cumplir con la Ley 1581 de 2012. Se garantizará la seguridad de la información mediante cifrado en tránsito y en reposo, roles de acceso diferenciados y políticas de respaldo. El diseño de la interfaz se realizará bajo principios de accesibilidad universal alineados con los estándares WCAG 2.1. Todo el trabajo entregado debe ser original; el plagio constituye una falta grave con consecuencias académicas.

# 10. Bibliografía

* Pressman, R. S. y Maxim, B. R. (2021). Ingeniería del software: Un enfoque práctico (9.a ed.). McGraw-Hill.
* Bass, L., Clements, P. y Kazman, R. (2021). Software Architecture in Practice (4.a ed.). Addison-Wesley.
* Myers, G. J., Sandler, C. y Badgett, T. (2011). The Art of Software Testing (3.a ed.). Wiley.
* Ballou, R. H. (2004). Logística: Administración de la cadena de suministro (5.a ed.). Pearson Educación.
* Schwaber, K. y Sutherland, J. (2020). La Guía Scrum. https://scrumguides.org
* Congreso de Colombia. (2012). Ley 1581 de 2012 — Protección de Datos Personales. Diario Oficial.