**IMPORT CORPORAL MED S.A.**

**Especificación de KPIs para el Software de Gestión de Inventario**

*Comercialización e importación de indumentos de fisioterapia – Colombia*

## **Dictamen tecnico de implementacion**

Este documento no debe leerse como una lista uniforme de indicadores listos para backend. Los 7 KPIs mezclan dominios distintos: inventario, costos, calidad, logística, servicio al cliente e IoT. La arquitectura actual del repositorio ya soporta reportes de solo lectura y agregaciones sobre ledger, stock y alertas, pero no contiene todos los hechos de negocio que varios KPIs necesitan para ser calculados con precisión.

### **Estado global**

| KPI | Decision | Estado actual en backend | Endpoints / contrato relacionado | Dependencias o cambios requeridos |
| --- | --- | --- | --- | --- |
| KPI 1 Rotacion de Inventario | No implementar como KPI formal aun | Parcial, sin costo/valoracion | No existe endpoint especifico. Hoy solo hay panel ejecutivo en `/api/v1/dashboard/overview/` y dataset historico en `/api/v1/reports/data/?kind=kpi` | Faltan costo unitario, inventario valorizado, snapshots de cierre y/o capa contable. Mejor como BI financiero o KPI de un subdominio de costing |
| KPI 2 Indice de Productos Danados | Implementacion parcial con datos backend disponibles | Parcial, pero utilizable como hechos derivados | `/api/v1/dashboard/kpis/`, `/api/v1/reports/quality-operational/`, `/api/v1/reports/data/?kind=quality-operational` | El backend entrega movimientos de daño/vencimiento y el frontend debe calcular la tasa final. Faltan incidente formal de calidad, catálogo de causas y trazabilidad de recuperación |
| KPI 3 Utilizacion de Almacen | Implementado en backend con ajuste de definicion | Viable con el modelo actual si se interpreta como ocupacion por capacidad logica | `/api/v1/dashboard/kpis/`, `/api/v1/reports/warehouse-utilization/`, `/api/v1/reports/data/?kind=warehouse-utilization`, `/api/v1/inventory/summary/` | Requiere mantener `Location.max_capacity` configurado y aclarar que la unidad es operacional, no fisica. La métrica ya sale por API de solo lectura |
| KPI 4 Cumplimiento en Despacho OTIF | No implementar OTIF como calculo backend; exponer solo hechos operativos | Parcial: hay resumen de despacho y facturas, pero no dominio de pedidos | `/api/v1/dashboard/kpis/`, `/api/v1/reports/dispatch-operational/`, `/api/v1/reports/data/?kind=dispatch-operational` | Faltan ordenes, promesas de entrega, transportadora, guia, confirmacion de entrega y estados logisticos. El backend solo entrega hechos para que frontend o BI calcule OTIF |
| KPI 5 Tasa de Descarte de Mercancia Defectuosa | Implementacion parcial con datos backend disponibles | Parcial, utilizable como hechos derivados | `/api/v1/dashboard/kpis/`, `/api/v1/reports/quality-operational/`, `/api/v1/reports/data/?kind=quality-operational` | El backend entrega salidas por daño, vencimiento y devoluciones como hechos operativos; el frontend calcula la tasa y el costo proxy. Faltan doble autorización formal, causal normalizada, adjuntos y acta de descarte |
| KPI 6 Tasa de Devoluciones + PQRSF | Separar en dos problemas | Devoluciones: parcial en backend. PQRSF: fuera de alcance actual | `/api/v1/dashboard/kpis/`, `/api/v1/reports/quality-operational/`, `/api/v1/reports/data/?kind=quality-operational` | El backend entrega devoluciones como hecho derivado; el frontend calcula tasa y tiempos. PQRSF requiere otro dominio, con formulario, cronómetro legal y trazabilidad propia |
| KPI 7 Cumplimiento de Cadena de Frio | No implementar como KPI completo aun | Parcial: hay bandera de producto y alertas, pero no telemetria | `/api/v1/dashboard/kpis/` y alertas operativas; no existe endpoint de sensores ni de lecturas | Faltan sensores, lecturas historicas, estado de cuarentena, reglas de excursion termica, integracion IoT y reporte por lote |

### **Lectura tecnica por KPI**

#### **KPI 1: Rotacion de Inventario**

No debe implementarse hoy como KPI oficial del backend. La formula depende de costo de mercancia vendida e inventario promedio valorizado, pero el backend solo conserva movimientos y stock derivado, no valores economicos de inventario ni cierres contables. Si se fuerza su calculo, el resultado sera una aproximacion fragil y discutible.

Si en el futuro se incorpora una capa de costing, la API deberia salir desde un endpoint de reportes de solo lectura, por ejemplo un dataset nuevo bajo `/api/v1/reports/`, con parametros de periodo y con valores ya consolidados. Hasta entonces, este KPI es mejor candidato para BI o analitica financiera.

#### **KPI 2: Indice de Productos Danados**

Este KPI ya puede alimentarse desde backend como hechos derivados, pero no como incidente formal. El backend expone las salidas por daño y vencimiento en el ledger y también un resumen operativo agregado para frontend; con eso el frontend puede calcular la tasa, segmentar por periodo y visualizar tendencias. Lo que no existe aún es la entidad primaria de incidente de calidad, la causal normalizada y la trazabilidad de recuperación o reproceso.

La mejor opción a mediano plazo sigue siendo un modelo de incidente de calidad o baja por daño, con causas normalizadas y relación al producto/lote. Hasta entonces, este KPI debe mostrarse como una métrica derivada y no como auditoría sanitaria completa.

#### **KPI 3: Utilizacion de Almacen**

Es el KPI mas cercano a la implementacion actual. `StockByLocation` ya permite conocer ocupacion por ubicacion y `Location.max_capacity` existe como capacidad maxima. Sin embargo, la definicion del documento habla de m2, m3, pallets o posiciones de rack, y el modelo actual no distingue esas unidades. Por tanto, el KPI es implementable solo si se formaliza la unidad de capacidad y se acepta que la medicion es operacional, no fisica.

La exposicion recomendada ya encaja con la arquitectura: un selector de reportes que agregue stock por ubicacion y compare contra capacidad configurada. Puede colgar de `/api/v1/inventory/summary/` o de un dataset de reportes. No requiere jobs, solo recalculo al consultar o despues de eventos de movimiento.

#### **KPI 4: Cumplimiento en Despacho de Mercancia OTIF**

No debe implementarse OTIF como calculo backend en el estado actual. OTIF requiere pedido, fecha comprometida, despacho, entrega, transportadora, guia y estado de completitud por item. El repositorio no tiene un dominio de pedidos ni de entregas; el ledger de movimientos no es suficiente para inferir a tiempo, completo y en contexto comercial.

Lo correcto hoy es exponer hechos de despacho y facturacion por API para consumo del frontend o de un BI externo. El backend ya puede servir `/api/v1/reports/dispatch-operational/` y `/api/v1/reports/data/?kind=dispatch-operational` con volumen de despachos, facturas vinculadas y productos top, pero deja el calculo final de OTIF a la capa que posea pedidos, promesas de entrega y confirmacion de entrega.

**NUEVO (contrato operativo):** el endpoint `dispatch-operational` ahora expone campos adicionales pensados para facilitar el cálculo de OTIF por parte del frontend:

- `shipments`: conteo de movimientos de salida de venta en el período.
- `invoice_linked_dispatches`: conteo de despachos con factura vinculada.
- `invoice_linked_ratio`: porcentaje (0-100) de despachos con factura sobre el total de `shipments`.
- `top_products`: listado de productos más despachados.
- `order_proxy`: campo libre (lista) pensado para que integraciones o futuros dominios inyecten datos por pedido cuando existan (hoy vacío).
- `carriers`: campo libre (objeto) pensado para agregar información de transportadoras cuando se integre ese dominio.

Con estos hechos el frontend puede:

- Unir localmente con su fuente de pedidos (si la tiene) por fecha/cliente y calcular `On Time` y `In Full` por pedido.
- Mostrar dashboards operativos que muestren volumen, facturación proxy y productos críticos.

Si el frontend no tiene la fuente de pedidos, el `dispatch-operational` sirve como resumen visual y de apoyo para BI, pero no puede producir OTIF fiable por sí solo.

#### **KPI 5: Tasa de Descarte de Mercancia Defectuosa**

El backend sí puede alimentar este KPI como hechos derivados, pero no como flujo formal de descarte. Hoy el sistema entrega salidas por daño, vencimiento y devoluciones como base operativa; con eso el frontend puede calcular tasa de descarte y tendencias. Lo que no existe aún es el modelo de descarte formal con doble autorización, causal normalizada, soporte documental y relación con proveedor.

Se puede construir sobre `Movement` como ledger, pero conviene separar "baja de inventario" de "descartar" y modelarlo en un servicio dedicado si el negocio decide formalizarlo. Sin ese cambio, el KPI debe presentarse como una métrica derivada para frontend, no como baja contable o sanitaria cerrada.

#### **KPI 6: Tasa de Devoluciones de Clientes y PQRSF**

El documento mezcla dos dominios que no deberían estar fusionados. Las devoluciones sí pueden apoyarse en `MovementType.DEVOLUCION` y ahora el backend ya las entrega como hecho derivado en el resumen operativo de calidad; el frontend puede calcular la tasa. PQRSF sigue sin existir en el backend actual. Un QR por pedido, cronómetro legal, adjuntos y respuesta formal requieren otra app, otro modelo y otro flujo de atención.

La recomendación arquitectónica sigue siendo separar el KPI en dos: devoluciones como KPI logístico con datos backend, y PQRSF como dominio de servicio al cliente o integración externa. Mantenerlos juntos solo produce un contrato ambiguo y un dashboard poco trazable.

#### **KPI 7: Cumplimiento de Cadena de Frio**

No es implementable como KPI completo con el backend actual. El sistema solo tiene una bandera `requires_cold_chain` y alertas de reconocimiento, pero no ingesta de sensores, historico termico, excursion, cuarentena o liberacion por lote. Eso significa que el backend hoy puede registrar conciencia operativa, pero no cumplimiento real de cadena de frio.

La via correcta es un subdominio de IoT/telemetria con lectura periodica, almacenamiento historico y calculo por lote. Si se quiere exponer por API, primero deben existir los modelos de lectura y los eventos de excursion. Sin eso, el KPI seria una declaracion vacia.

### **Endpoints relacionados en el estado actual**

Los siguientes endpoints ya existen y son la base de los reportes de solo lectura y del dashboard operacional, aunque no cubren todos los KPIs del documento:

- `/api/v1/dashboard/overview/` : agregador del panel ejecutivo con métricas, alertas, KPIs y movimientos recientes.
- `/api/v1/dashboard/metrics/` : métricas superiores del panel.
- `/api/v1/dashboard/alerts/` : alertas activas.
- `/api/v1/dashboard/kpis/` : KPIs operativos con precisión explícita.
- `/api/v1/dashboard/movements/` : movimientos recientes para la UI.
- `/api/v1/reports/kpi/` : compatibilidad histórica con el panel operativo generico.
- `/api/v1/reports/data/?kind=kpi` : dataset unificado para frontend, equivalente al panel anterior.
- `/api/v1/reports/inventory/summary/` : resumen de inventario actual.
- `/api/v1/reports/movements/summary/` : conteo de movimientos por tipo.
- `/api/v1/reports/movements/report/` : agregados por tipo, producto y usuario.
- `/api/v1/reports/movements/history/` : historial de movimientos filtrable.
- `/api/v1/reports/top-products/` : productos mas despachados.
- `/api/v1/reports/warehouse-utilization/` : utilización de almacén por capacidad configurada.
- `/api/v1/reports/quality-operational/` : hechos derivados de daño, vencimiento y devoluciones para cálculo frontend de KPI 2 y KPI 6.
- `/api/v1/reports/invoices/` : historial de salidas con factura.
- `/api/v1/reports/expiring/` : lotes con vencimiento proximo.

**Nota sobre generación de códigos de barra:** el backend expone payloads listos para consumir con la forma `{ type, value, svg, svg_data_uri }` (por ejemplo desde el endpoint de producto). En entornos de test donde la librería de render `python-barcode` no está instalada se devuelve un `svg` placeholder con encabezado XML para mantener la compatibilidad del contrato; en producción recomendamos instalar `python-barcode` para obtener SVG completos y legibles.

### **Pendientes tecnicos explicitos**

- Crear o no crear un dominio de costing antes de intentar KPI 1.
- Definir si el KPI 2 mide incidencias o bajas definitivas, porque hoy el documento mezcla ambos conceptos.
- Formalizar la unidad de capacidad para KPI 3.
- Diseñar dominio de pedidos y entregas para KPI 4.
- Separar descarte sanitario de salida operativa para KPI 5.
- Separar devoluciones de PQRSF para KPI 6.
- Introducir telemetria y cuarentena por lote para KPI 7.
- Centralizar fórmulas y thresholds KPI en un único servicio de dominio para evitar drift entre dashboard y reports.
- Mantener cache corto y contratos composables en dashboard para no convertir el agregado en un endpoint monolítico.

### **Conclusion operativa**

De los 7 KPIs del documento, solo KPI 3 puede considerarse cercano a la implementacion actual del backend, y aun asi con ajuste conceptual. Los KPI 1, 4, 5 y 7 no deberian prometerse como backend listo porque faltan hechos de negocio esenciales. KPI 2 y KPI 6 son implementables solo de forma parcial y requieren separar definiciones para no mezclar eventos distintos bajo un mismo indicador.

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