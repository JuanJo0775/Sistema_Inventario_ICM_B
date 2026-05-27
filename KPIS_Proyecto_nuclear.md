**IMPORT CORPORAL MED S.A.**

**Especificación de KPIs para el Software de Gestión de Inventario**

*Comercialización e importación de indumentos de fisioterapia – Colombia*

# **KPI 1: Rotación de Inventario**

### **Definición**

La rotación de inventario indica cuántas veces se renueva completamente el stock en un período determinado. En el contexto de una empresa de productos médicos como Import Corporal Med, este indicador es crítico para garantizar que los insumos y dispositivos de fisioterapia no permanezcan almacenados más tiempo del necesario, evitando vencimientos y obsolescencia.

### **Fórmula**

|  |
| --- |
| **Rotación de Inventario = Costo de Mercancía Vendida (CMV) / Inventario Promedio** |

|  |
| --- |
| **Inventario Promedio = (Inventario Inicial + Inventario Final) / 2** |

### **Datos de entrada para el software**

* Costo total de los productos despachados o vendidos en el período (CMV).
* Valor del inventario al inicio del período.
* Valor del inventario al cierre del período (o en tiempo real: el valor actual).

### **Comportamiento esperado del sistema**

El software debe recalcular este KPI en tiempo real con cada movimiento de salida de inventario. El resultado debe mostrarse como un número (por ejemplo: 6,2 veces) e indicar el período de referencia (día, mes, año acumulado).

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **< 4 veces/año** | **Baja rotación** | Exceso de stock. El capital está inmovilizado y se incrementa el riesgo de vencimiento u obsolescencia. |
| **4 – 8 veces/año** | **Nivel aceptable** | Balance adecuado entre disponibilidad y movimiento de mercancía. |
| **> 8 veces/año** | **Alta eficiencia** | Vigilar posibles quiebres de stock y garantizar el stock mínimo de seguridad. |

**Nota:** *en productos médicos, mantener cierto nivel de stock de seguridad es obligatorio por regulación INVIMA. La rotación alta debe balancearse con el stock mínimo requerido.*

# **KPI 2: Índice de Productos Dañados**

### **Definición**

Mide el porcentaje del inventario que resulta dañado, vencido o en mal estado respecto al total de unidades manejadas en el período. Este KPI es especialmente sensible, ya que un producto dañado o vencido no solo representa una pérdida económica sino también un riesgo para el paciente o cliente.

### **Fórmula**

|  |
| --- |
| **Índice de Productos Dañados (%) = (Unidades dañadas / Total unidades manejadas) × 100** |

### **Datos de entrada que el software debe registrar**

* Número de unidades reportadas como dañadas, vencidas o no aptas en el período.
* Motivo del daño (campo opcional pero recomendado: vencimiento, manipulación, almacenamiento, transporte).

### **Comportamiento esperado del sistema**

El software debe actualizar este KPI cada vez que un usuario registre una baja de producto por daño o vencimiento. El resultado debe expresarse en porcentaje (por ejemplo: 1,43%).

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **< 1%** | **Excelente** | Control de manipulación y almacenaje óptimo. |
| **1% – 3%** | **Aceptable** | Revisar procesos de carga, descarga y condiciones de almacén. |
| **> 3%** | **Crítico** | Se deben identificar y corregir las causas raíz de forma inmediata. |

# **KPI 3: Utilización de Almacén**

### **Definición**

Mide qué porcentaje de la capacidad total del almacén se encuentra ocupado en un momento dado. Este indicador permite identificar tanto la subutilización del espacio (costos fijos ociosos) como la sobrecarga (riesgo operativo), lo cual es especialmente relevante para productos médicos que requieren condiciones específicas de almacenamiento.

### **Fórmula**

|  |
| --- |
| **Utilización de Almacén (%) = (Posiciones ocupadas / Capacidad total) × 100** |

### **Datos de entrada que el software debe registrar**

* Capacidad total del almacén (definida al configurar el sistema: en m², m³, pallets o posiciones de rack).
* Espacio o posiciones actualmente ocupadas (actualizado con cada entrada o salida de inventario).

### **Comportamiento esperado del sistema**

El software debe recalcular este KPI en tiempo real con cada entrada o salida de mercancía. El resultado debe mostrarse como un porcentaje (por ejemplo: 74%) y reflejar el estado actual del almacén.

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **< 60%** | **Subutilización** | Los costos fijos no están siendo aprovechados. |
| **60% – 85%** | **Nivel óptimo** | Existe margen operativo para maniobrar con seguridad. |
| **> 85%** | **Sobrecarga** | Riesgo de errores, accidentes y deterioro de otros KPIs. |

# **KPI 4: Cumplimiento en Despacho de Mercancía (OTIF)**

### **Definición**

El indicador OTIF (On Time In Full) mide el porcentaje de pedidos despachados a tiempo y completos respecto al total de pedidos procesados en el período. Para Import Corporal Med, que comercializa indumentos de fisioterapia a clínicas, consultorios y profesionales independientes, este KPI es vital porque un retraso o un despacho incompleto puede paralizar tratamientos médicos y deteriorar la relación comercial.

Dado que la empresa cuenta con 10 empleados y opera bajo el régimen de Sociedad Anónima en Colombia, este indicador permite además medir la productividad del equipo logístico frente al volumen de operación.

### **Fórmula**

|  |
| --- |
| **OTIF (%) = (Pedidos entregados a tiempo Y completos / Total pedidos del período) × 100** |

**Para análisis más detallado, se puede descomponer en:**

|  |
| --- |
| **On Time (%) = (Pedidos entregados en la fecha pactada / Total pedidos) × 100** |

|  |
| --- |
| **In Full (%) = (Pedidos entregados completos / Total pedidos) × 100** |

### **Datos de entrada que el software debe registrar**

* Número de orden de pedido y cliente asociado.
* Fecha y hora de generación del pedido.
* Fecha pactada de entrega (acuerdo comercial).
* Fecha y hora real de despacho desde la bodega.
* Cantidad solicitada vs. cantidad efectivamente despachada por cada ítem.
* Transportadora asignada y número de guía.
* Responsable interno del alistamiento (uno de los 10 empleados).
* Motivo del incumplimiento, si lo hubo (faltante de stock, error de alistamiento, retraso del transportador, etc.).

### **Comportamiento esperado del sistema**

El software debe calcular el OTIF en tiempo real y permitir filtrar por cliente, por tipo de producto (electroterapia, vendajes, equipos de ultrasonido, etc.), por transportadora y por empleado responsable. Debe generar alertas automáticas cuando un pedido se acerque a su fecha pactada sin haber sido despachado (por ejemplo, 24 horas antes).

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **< 85%** | **Crítico** | Existen fallas estructurales en la logística. Revisar urgentemente procesos de alistamiento, stock y alianzas con transportadoras. |
| **85% – 94%** | **Aceptable** | Hay oportunidades claras de mejora. Identificar el cuello de botella (tiempo o completitud) y corregir. |
| **95% – 98%** | **Bueno** | Nivel competitivo para el sector salud en Colombia. Mantener la disciplina operativa. |
| **≥ 99%** | **Excelente** | Clase mundial. Apalancar este indicador en la propuesta comercial con clínicas e instituciones. |

**Aplicación práctica para Import Corporal Med:** *considerando el tamaño de la empresa (10 empleados), se recomienda revisar este KPI en reunión semanal de los lunes, asignando un responsable rotativo del análisis. La meta inicial sugerida es alcanzar y sostener un OTIF ≥ 95% durante tres meses consecutivos.*

# **KPI 5: Tasa de Descarte de Mercancía Defectuosa**

### **Definición**

Mide el porcentaje de mercancía que debe ser dada de baja (descartada definitivamente del inventario disponible para venta) por presentar defectos de fabricación, daños durante el transporte de importación, vencimiento, ruptura del empaque estéril o cualquier otra causa que impida su comercialización segura. Es un indicador clave para Import Corporal Med porque, al ser importadora, recibe mercancía de larga distancia y debe poder cuantificar las pérdidas asociadas al traslado internacional para negociar mejores condiciones con proveedores y aseguradoras.

Este KPI se diferencia del Índice de Productos Dañados (KPI 2) en que aquí se mide específicamente la mercancía que sale definitivamente del inventario (baja contable y física), mientras que el KPI 2 considera todas las unidades reportadas como dañadas, incluyendo aquellas que pueden recuperarse o reprocesarse.

### **Fórmula**

|  |
| --- |
| **Tasa de Descarte (%) = (Unidades descartadas / Total unidades en inventario del período) × 100** |

**Adicionalmente, para medir el impacto económico:**

|  |
| --- |
| **Costo del Descarte ($) = Σ (Costo unitario × Unidades descartadas)** |

### **Datos de entrada que el software debe registrar**

* Código del producto y lote afectado.
* Cantidad de unidades descartadas.
* Costo unitario de cada producto descartado (para calcular pérdida en pesos colombianos).
* Causa del descarte, clasificada en categorías estandarizadas:
  + Defecto de fabricación (responsabilidad del proveedor extranjero).
  + Daño en transporte internacional (responsabilidad de transportadora/aseguradora).
  + Daño en almacén local (responsabilidad interna).
  + Vencimiento.
  + Ruptura de empaque estéril o primario.
  + Retiro del mercado por alerta sanitaria del INVIMA.
* Empleado que reporta y empleado que autoriza la baja (control dual).
* Fecha del descarte y soporte fotográfico (recomendado).

### **Comportamiento esperado del sistema**

El software debe exigir doble autorización para registrar una baja de inventario (un empleado reporta, un responsable autoriza), generar un acta de descarte automática con todos los datos del descarte, y acumular las pérdidas por categoría de causa. Debe emitir un reporte mensual segmentado por proveedor extranjero, lo que permite a Import Corporal Med soportar reclamaciones comerciales y de seguros.

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **< 0,5%** | **Excelente** | Control de calidad ejemplar. Proveedores y procesos internos confiables. |
| **0,5% – 1,5%** | **Aceptable** | Nivel normal para el sector de importación de productos médicos. |
| **1,5% – 3%** | **Atención** | Revisar proveedores con mayor incidencia y condiciones de transporte internacional. |
| **> 3%** | **Crítico** | Pérdida económica significativa. Auditar inmediatamente toda la cadena de suministro. |

**Cumplimiento normativo:** *el INVIMA exige conservar trazabilidad de los descartes de productos médicos. El software debe almacenar el historial mínimo por 5 años y permitir la exportación de actas de descarte en formato PDF para auditorías sanitarias.*

# **KPI 6: Tasa de Devoluciones de Clientes (con módulo PQRSF mediante código QR)**

### **Definición**

Mide el porcentaje de unidades o pedidos que los clientes devuelven a Import Corporal Med, así como las razones de dichas devoluciones. Está integrado con un módulo PQRSF (Peticiones, Quejas, Reclamos, Sugerencias y Felicitaciones) accesible mediante un código QR impreso en la factura, el empaque y el comprobante de entrega del producto.

El uso del QR es estratégico: en lugar de obligar al cliente a llamar o escribir un correo, basta con que escanee el código con la cámara de su celular para acceder directamente al formulario PQRSF prediligenciado con los datos del pedido. Esto incrementa drásticamente la tasa de reporte real y permite a la empresa tener información veraz sobre la experiencia del cliente.

### **Fórmulas**

|  |
| --- |
| **Tasa de Devoluciones (%) = (Unidades devueltas / Unidades despachadas) × 100** |

|  |
| --- |
| **Tasa de Respuesta PQRSF = (PQRSF respondidos en plazo legal / PQRSF recibidos) × 100** |

|  |
| --- |
| **Tiempo Promedio de Respuesta = Σ (Días hábiles para responder) / N° PQRSF** |

### **Funcionamiento del módulo QR – PQRSF**

* **Generación automática del QR:** el software genera un código QR único por cada despacho, vinculado al número de pedido, cliente y productos enviados.
* **Impresión en tres puntos:** factura electrónica, sticker en la caja de envío y comprobante físico de entrega.
* **Formulario web responsive:** al escanear, el cliente accede a un formulario con campos prellenados (número de pedido, fecha, productos) y selecciona el tipo de solicitud: Petición, Queja, Reclamo, Sugerencia o Felicitación.
* **Adjuntos:** permite cargar fotos o videos del producto devuelto, lo cual es clave para distinguir devoluciones por defecto de fabricación frente a mal uso.
* **Trazabilidad:** cada PQRSF queda enlazado al pedido, al producto, al lote y al transportador, lo que facilita identificar patrones.

### **Datos de entrada que el software debe registrar**

* Número de unidades devueltas y producto específico.
* Pedido y cliente asociados.
* Tipo de solicitud PQRSF (P/Q/R/S/F).
* Causa de la devolución, en categorías estandarizadas:
  + Producto defectuoso o no funcional.
  + Producto distinto al solicitado (error de alistamiento).
  + Cantidad incorrecta.
  + Daño durante el transporte de salida.
  + Cambio de decisión del cliente / arrepentimiento.
  + No cumple expectativas técnicas (talla, voltaje, accesorios).
* Fecha de recepción del PQRSF y fecha de respuesta.
* Responsable asignado dentro de los 10 empleados.
* Resultado: devolución aceptada, cambio, nota crédito, reparación o rechazo justificado.

### **Comportamiento esperado del sistema**

El software debe enviar notificación automática por correo y WhatsApp al área comercial apenas se recibe un PQRSF. Debe llevar un cronómetro visible de los plazos legales colombianos para responder (15 días hábiles según Ley 1755 de 2015 para PQRSF generales; menor para reclamos sanitarios). Debe generar un dashboard con: total de PQRSF por mes, tipo más frecuente, productos más reportados y empleados con mejor tiempo de respuesta.

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **< 2%** | **Excelente** | Calidad de producto y proceso de despacho confiables. |
| **2% – 5%** | **Aceptable** | Dentro del rango normal para comercialización médica. |
| **5% – 8%** | **Atención** | Investigar causas reiteradas y revisar proveedores o procesos. |
| **> 8%** | **Crítico** | Hay un problema sistémico. Posible alerta para retiro de producto. |

**Cumplimiento legal colombiano:** *la Ley 1480 de 2011 (Estatuto del Consumidor) y la Ley 1755 de 2015 obligan a las empresas a responder PQRSF en plazos definidos. El módulo QR no es solo una herramienta de calidad; es un mecanismo de cumplimiento normativo que protege a Import Corporal Med ante eventuales acciones ante la Superintendencia de Industria y Comercio (SIC).*

# **KPI 7: Cumplimiento de Cadena de Frío**

### **Definición**

Mide el porcentaje del tiempo durante el cual los productos que requieren cadena de frío (geles conductores con activos sensibles, parches medicados, ciertos insumos biológicos para fisioterapia y rehabilitación) se han mantenido dentro del rango térmico exigido por el fabricante y por la normativa colombiana del INVIMA. Una ruptura de la cadena de frío puede invalidar el producto, generando pérdidas económicas y riesgo sanitario.

Aunque Import Corporal Med comercializa principalmente indumentos de fisioterapia, algunos productos del portafolio (geles refrigerados, parches transdérmicos con principios activos, ciertos productos biotecnológicos para rehabilitación) requieren conservarse típicamente entre 2°C y 8°C, o en algunos casos entre 15°C y 25°C controlados. Este KPI aplica solo a esos productos y no al inventario general.

### **Fórmulas**

|  |
| --- |
| **Cumplimiento de Cadena de Frío (%) = (Tiempo dentro de rango / Tiempo total monitoreado) × 100** |

|  |
| --- |
| **Excursiones Térmicas = N° de eventos fuera de rango en el período** |

|  |
| --- |
| **Duración Promedio de Excursión = Σ (Minutos fuera de rango) / N° de excursiones** |

### **Datos de entrada que el software debe registrar**

* Identificación de productos sujetos a cadena de frío (marcados con bandera en el maestro de productos).
* Rango térmico requerido por cada producto (mínimo y máximo en °C).
* Lecturas automáticas de temperatura desde sensores IoT o data loggers instalados en:
  + Nevera o cuarto frío del almacén.
  + Vehículo de transporte (envíos urbanos refrigerados).
  + Caja térmica del paquete (data logger desechable para envíos largos).
* Frecuencia mínima de lectura: cada 5 minutos.
* Eventos de apertura de nevera (sensor de puerta).
* Identificación del empleado responsable del turno durante una excursión.
* Acción tomada ante la excursión: cuarentena del producto, descarte, liberación tras evaluación técnica.

### **Comportamiento esperado del sistema**

El software debe integrarse con los sensores IoT del cuarto frío vía API o vía Wi-Fi/Bluetooth. Debe generar alertas automáticas en tiempo real al celular del responsable (vía SMS, WhatsApp Business o correo) cuando la temperatura salga del rango por más de 10 minutos. Debe poner automáticamente en estado de cuarentena cualquier lote afectado por una excursión, impidiendo que sea despachado hasta que un responsable autorizado lo libere o lo dé de baja.

Adicionalmente, el sistema debe generar el reporte mensual de cadena de frío exigido por el INVIMA y permitir la descarga del histórico térmico por lote, requisito para auditorías sanitarias.

### **Interpretación del resultado**

| **Rango** | **Calificación** | **Interpretación y acción recomendada** |
| --- | --- | --- |
| **100%** | **Cumplimiento total** | Estado ideal. Mantener la disciplina y el mantenimiento preventivo de equipos. |
| **99,5% – 99,9%** | **Aceptable** | Pequeñas excursiones cortas. Revisar causas (apertura de puerta, picos eléctricos). |
| **98% – 99,5%** | **Atención** | Requiere intervención técnica. Evaluar estado de neveras y respaldo eléctrico. |
| **< 98%** | **No conforme** | Riesgo sanitario. Notificar a INVIMA si aplica y revisar todos los lotes potencialmente afectados. |

**Recomendaciones de respaldo:** *para una empresa de 10 empleados, se sugiere implementar UPS (sistema de alimentación ininterrumpida) en el cuarto frío, un termómetro de respaldo calibrado independiente y un protocolo escrito de contingencia ante fallo eléctrico (traslado a nevera secundaria o uso de hielo seco). El software debe documentar la calibración anual de los sensores, requisito de las Buenas Prácticas de Almacenamiento del INVIMA.*

# **Relación e Integración entre los KPIs**

Los siete KPIs descritos están profundamente interconectados. Import Corporal Med debe visualizarlos en un dashboard único, ya que el deterioro de uno frecuentemente anticipa el deterioro de otros:

* **Utilización de Almacén (KPI 3) > 85%** tiende a incrementar el Índice de Productos Dañados (KPI 2) y la Tasa de Descarte (KPI 5), y a reducir la Rotación (KPI 1) y el OTIF (KPI 4) por dificultad para localizar productos.
* **Una caída del OTIF (KPI 4)** suele dispararse al cabo de pocos días en la Tasa de Devoluciones y PQRSF (KPI 6), porque los clientes molestos por demoras tienden a rechazar el pedido al llegar.
* **Las excursiones térmicas (KPI 7)** generan directamente descartes (KPI 5) y, si el producto se despachó antes de detectar la excursión, devoluciones y PQRSF (KPI 6).
* **Una rotación muy alta (KPI 1) mal gestionada** puede deteriorar el OTIF (KPI 4) por quiebres de stock y aumentar las PQRSF por entregas incompletas.

## **Recomendaciones de implementación para Import Corporal Med S.A.**

* Configurar el dashboard integrado de los 7 KPIs en una pantalla visible para el equipo de los 10 empleados (TV en zona común o panel en cada estación de trabajo).
* Asignar a un responsable de Calidad/Logística la revisión semanal de los indicadores y la presentación de resultados en comité mensual de Junta Directiva (obligatorio en S.A.).
* Definir metas trimestrales por KPI alineadas con los objetivos comerciales del año.
* Vincular el desempeño de los KPIs operativos (OTIF, descarte, devoluciones) a esquemas de reconocimiento al personal, lo cual es viable y costo-eficiente en una empresa de 10 empleados.
* Conservar el histórico de los KPIs por mínimo 5 años para cumplir con auditorías del INVIMA, la DIAN y eventualmente la Superintendencia de Sociedades.