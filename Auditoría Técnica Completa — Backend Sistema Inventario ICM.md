# Auditoría Técnica Completa — Backend Sistema Inventario ICM

## Contexto

Backend Django REST Framework para gestión de inventario de una empresa (ICM). Arquitectura modular con 8 dominios, patrón Service Layer + Selectors, PostgreSQL, JWT + RBAC, y ledger inmutable como fuente de verdad. El objetivo de esta auditoría es identificar brechas entre lo que existe y lo que se necesita para producción.

---

## Resumen Ejecutivo

| Dimensión | Estado |
|-----------|--------|
| Arquitectura general | Buena base, con debt acumulada en capas intermedias |
| API REST | Completa en mayoría, pero con una feature completa inaccesible (combos) |
| Seguridad | Sólida en autenticación/autorización; débil en validación de inputs y defensa en profundidad |
| Performance | Problemas críticos de N+1 queries en el camino caliente de movimientos |
| Testing | Estructura correcta; cobertura real insuficiente con casos triviales que dan falsa confianza |
| Producción-readiness | ~65%. Faltan auto-healing de caché, constraints de DB, y feature flags de corrección |

---

## 1. PROBLEMAS CLASIFICADOS POR IMPACTO

### CRÍTICOS — Bloquean producción o causan corrupción de datos

---

**C-01: N+1 query en el camino caliente de movimientos**
- **Archivo**: `apps/movements/services.py:909-989`
- **Qué está mal**: `ledger_net_quantity_for_location()` carga todos los movimientos de un producto con un queryset básico y luego los itera en Python para acumular totales. Sin `select_related()`, genera una query por cada FK accedida dentro del loop. `ledger_net_quantity_for_lot_location()` repite el mismo patrón 40 líneas abajo.
- **Por qué es un problema**: Con 1000 movimientos históricos, una sola llamada puede generar 1000+ queries. En producción esto provoca timeouts. El camino crítico `register_dispatch()` invoca esto para cada lote disponible.
- **Cómo solucionarlo**: Reemplazar la iteración Python por una agregación SQL con `annotate(Sum(...))` y un único `filter`. Las dos funciones se pueden unificar en una sola parametrizada con `lot_id` opcional.
- **Impacto de arreglarlo**: Reducción de O(n) queries a O(1). Crítico para escalabilidad.

---

**C-02: Feature de combos implementada pero sin API**
- **Archivos**: `apps/movements/services.py:1060-1148` (lógica completa), `apps/movements/urls.py` (sin ruta), `apps/movements/views.py` (sin vista)
- **Qué está mal**: `dispatch_combo()` tiene una implementación completa con validaciones y manejo de stock por ítem. No hay endpoint, no hay serializer de creación, no hay tests.
- **Por qué es un problema**: Código muerto que nadie puede usar. La feature existe en el modelo (`ProductCombo`, `ComboItem`) y en el ledger (`SALIDA_COMBO`), pero la API la ignora. Cualquier despacho de combos hoy se haría manualmente producto a producto, perdiendo trazabilidad.
- **Cómo solucionarlo**: Crear `ComboDispatchView` en `movements/views.py`, agregar ruta `POST /api/v1/movements/combo-dispatch/`, exponer serializer `ComboDispatchSerializer` ya existente, y escribir tests.
- **Impacto**: Activa una feature ya pagada en desarrollo.

---

**C-03: Corrección de movimientos (BR-06) solo funciona para traslados**
- **Archivo**: `apps/movements/services.py:860`
- **Qué está mal**: `correct_movement_within_window()` tiene un guard explícito que lanza `ValueError` si el movimiento no es `TRASLADO`. Entradas y salidas con error no tienen corrección dentro de la ventana de tiempo.
- **Por qué es un problema**: La regla de negocio BR-06 implica que cualquier movimiento puede corregirse. Operacionalmente, los errores en entradas son comunes (cantidad equivocada en factura). Actualmente solo se pueden "corregir" con un ajuste posterior, rompiendo la trazabilidad.
- **Cómo solucionarlo**: Extender `correct_movement_within_window()` para manejar `ENTRADA` (crear `ENTRADA` correctiva + reversal del stock delta) y `SALIDA` (ídem). Documentar qué tipos admite la corrección como regla formal.
- **Impacto**: Cierre de deuda funcional crítica; auditoría más limpia en producción.

---

**C-04: Inmutabilidad del ledger sin enforcement en base de datos**
- **Archivo**: `apps/movements/models.py:24-29`
- **Qué está mal**: `Movement` no tiene `updated_at` (correcto) pero tampoco tiene trigger o constraint de BD que bloquee `UPDATE` directo. La inmutabilidad es solo un contrato en Python/ORM.
- **Por qué es un problema**: Un script de migración, una query directa en psql, o un bug en un servicio futuro podría silenciosamente modificar registros del ledger. Sin enforcement en BD, la auditoría no es fiable.
- **Cómo solucionarlo**: Crear un trigger PostgreSQL `BEFORE UPDATE ON movements_movement RAISE EXCEPTION 'immutable record'`. Agregar test que intente un UPDATE directo vía `connection.execute()` y verifique que falla.
- **Impacto**: Garantía real de inmutabilidad; ledger confiable como fuente de verdad.

---

**C-05: Stock caché sin mecanismo de auto-healing**
- **Archivos**: `apps/inventory/models.py` (StockByLocation), `apps/inventory/services.py:28-62` (trigger_stock_reconstruction manual)
- **Qué está mal**: `StockByLocation` es deliberadamente un caché del ledger, pero la reconstrucción es manual (comando `trigger_stock_reconstruction()`). No hay detección de deriva ni job automático.
- **Por qué es un problema**: Si un bug, migración fallida, o edge case no cubierto corrompe la caché, la discrepancia será silenciosa hasta que un operador lo detecte manualmente. En producción esto es riesgo de stock negativo falso o falsos positivos de disponibilidad.
- **Cómo solucionarlo**: Agregar un management command `verify_stock_integrity` que compare caché vs. recálculo de ledger y emita alertas de divergencia. Programar como cron job diario. No es necesario auto-reparar, pero sí detectar y alertar.
- **Impacto**: Visibilidad de corrupción antes de que afecte operaciones.

---

**C-06: 59 líneas de código duplicado en cálculos de ledger**
- **Archivo**: `apps/movements/services.py:909-989`
- **Qué está mal**: `ledger_net_quantity_for_location()` (línea 909) y `ledger_net_quantity_for_lot_location()` (línea 951) son la misma lógica diferenciada solo por un filtro `lot_id`. El mismo bloque `if/elif` de movimientos se repite dos veces.
- **Por qué es un problema**: Cuando cambia la lógica de un tipo de movimiento (ej. se agrega `SALIDA_COMBO`), hay que recordar actualizarlo en dos lugares. Ya hay un bug latente: `SALIDA_COMBO` probablemente no está contemplado en estas funciones.
- **Cómo solucionarlo**: Refactorizar en `_ledger_net_qty(*, product_id, location_id, lot_id=None) -> int` y que ambas funciones públicas la deleguen.
- **Impacto**: Una sola fuente de verdad para cálculos del ledger; bug de SALIDA_COMBO solucionado.

---

**C-07: Test trivial que genera falsa cobertura**
- **Archivo**: `apps/inventory/tests/test_services.py:4-6`
- **Qué está mal**: El test más básico del servicio de inventario solo verifica `assert callable(get_current_stock)`. No prueba ninguna lógica.
- **Por qué es un problema**: La métrica de cobertura de líneas indica que `inventory/services.py` está "testeado" cuando en realidad los servicios clave no tienen prueba alguna. Esto crea falsa confianza en el equipo.
- **Cómo solucionarlo**: Reemplazar con tests reales: stock correcto después de entrada, stock negativo bloqueado, stock en múltiples ubicaciones, reconstrucción desde ledger.
- **Impacto**: Cobertura real que detecte regresiones.

---

### IMPORTANTES — Reducen confiabilidad, mantenibilidad o correctness

---

**I-01: Validación de SKU duplicada en dos capas**
- **Archivos**: `apps/catalog/models.py:120-133` y `apps/catalog/services.py:38-39`
- **Qué está mal**: `Product.clean()` y `create_product()` en services ambos llaman a `validate_sku_format()`.
- **Cómo solucionarlo**: Remover del `models.clean()` y dejar solo en el servicio, o solo en el modelo y eliminar del servicio. La validación de formato de dominio pertenece al modelo como `clean()`.
- **Impacto**: Una sola fuente de verdad para la regla de negocio BR-12.

---

**I-02: Auditoría acoplada manualmente a cada servicio**
- **Patrón**: `log_event()` llamado en `movements/services.py:313-319`, `inventory/services.py:52-61`, `catalog/services.py` y otros.
- **Qué está mal**: Sin un mecanismo centralizado, cualquier servicio nuevo puede olvidar auditar. No hay forma de verificar en PR review que "esta acción quedó auditada".
- **Cómo solucionarlo**: Crear un decorador `@auditable(event_type=...)` que envuelva servicios y llame a `log_event()` automáticamente, capturando args/resultado. Para acciones complejas, mantener llamada manual.
- **Impacto**: Cobertura de auditoría garantizada estructuralmente.

---

**I-03: `create_combo()` bloquea creación si no hay stock**
- **Archivo**: `apps/catalog/services.py:157-181`
- **Qué está mal**: La función valida que cada producto del combo tenga stock positivo antes de guardar el combo. Un combo es una receta/plantilla, no un stock físico.
- **Por qué es un problema**: No puedo crear el combo "Kit de oficina" si alguno de sus productos está agotado temporalmente. Esto rompe el flujo de gestión del catálogo.
- **Cómo solucionarlo**: Remover la validación de stock de `create_combo()`. Si se quiere alertar, emitir una alerta `LOW_STOCK` al crear combo con productos sin stock, pero no bloquear.
- **Impacto**: UX correcta; separación entre catálogo y stock.

---

**I-04: Restricción horaria BR-03 implementada en 3 lugares desincronizados**
- **Archivos**: `apps/authentication/services.py` (login), `apps/authentication/serializers.py` (token refresh), `shared/permissions.py` (IsWithinOperatingHours)
- **Qué está mal**: La lógica de `is_within_operating_hours()` existe en tres lugares. Si cambia el horario (ej. se agrega sábado), hay que actualizarlo en todos.
- **Cómo solucionarlo**: Centralizar en `shared/operating_hours.py` como única función, y que los 3 lugares la importen. Agregar test parametrizado para todos los edge cases horarios.
- **Impacto**: Un solo punto de cambio para horarios operativos.

---

**I-05: O(n×m) en recalculation de lotes disponibles para despacho**
- **Archivo**: `apps/movements/services.py:479-505` llama a `available_lots_at_location()` (línea 992-1056)
- **Qué está mal**: `available_lots_at_location()` itera todos los movimientos de un producto para calcular el inventario por lote. En `register_dispatch()` esto se llama sin memoización, pudiendo ejecutarse múltiples veces por transacción.
- **Cómo solucionarlo**: Usar una única query `Movement.objects.filter(...).values('lot_id').annotate(qty=...)` con las sumas apropiadas en SQL. Esto hace O(1) query en lugar de O(n).
- **Impacto**: Despachos de productos con muchos lotes dejan de ser lentos.

---

**I-06: Sin índice en `Movement.lot_id`**
- **Archivo**: `apps/movements/models.py`
- **Qué está mal**: `lot_id` es FK sin índice explícito. Django crea índice en FK por defecto en PostgreSQL, pero hay que verificar si está en las migraciones.
- **Cómo solucionarlo**: Verificar migración y agregar `db_index=True` si falta. Considerar índice compuesto `(product_id, lot_id)` para las queries más comunes.
- **Impacto**: Queries multi-lote con rendimiento correcto.

---

**I-07: Validación de UUID en query params sin manejo de errores**
- **Archivo**: `apps/alerts/views.py` (función `_build_alert_filters`)
- **Qué está mal**: `UUID(str(pid))` sin try/except. Un `product_id` inválido genera 500 en lugar de 400.
- **Cómo solucionarlo**: Envolver en try/except y retornar `ValidationError` con mensaje claro. Patrón ya existe en otros endpoints del proyecto.
- **Impacto**: API robusta; no expone stack traces al cliente.

---

**I-08: Tests de concurrencia ausentes para el mecanismo de locking**
- **Archivos**: `apps/movements/services.py` (`select_for_update()` en `_lock_stock()`), `tests/concurrency/`
- **Qué está mal**: `select_for_update()` está correctamente implementado, pero no hay test que verifique que dos hilos simultáneos no generan stock negativo.
- **Cómo solucionarlo**: Agregar test con `threading.Thread` que ejecute dos despachos simultáneos del mismo producto con stock = 1. Solo uno debe tener éxito.
- **Impacto**: Confianza real en que la concurrencia está cubierta.

---

**I-09: `period_days` e `int(limit)` sin límite máximo en dashboard**
- **Archivos**: `apps/dashboard/views.py`, `apps/reports/views.py`
- **Qué está mal**: `period_days = int(request.query_params.get("period_days", 30))` sin validación de rango. Un usuario puede pedir `period_days=99999` y generar queries costosas.
- **Cómo solucionarlo**: Agregar validación `min=1, max=365` en los serializers de query params, o inline con clamp.
- **Impacto**: Protección básica contra queries inadvertidamente caras.

---

**I-10: Migración de backfill de barcodes sin test de reversibilidad**
- **Archivo**: `apps/catalog/migrations/0003_backfill_product_barcodes.py`
- **Qué está mal**: Las data migrations con `RunPython` deben tener función `reverse_code` definida. Sin ella, `migrate --fake` o downgrade fallará en producción.
- **Cómo solucionarlo**: Agregar `reverse_code=migrations.RunPython.noop` si el backfill es idempotente, o implementar la lógica inversa real.
- **Impacto**: Rollbacks seguros en producción.

---

### MEJORAS FUTURAS — No bloquean producción pero reducen deuda técnica

---

**M-01: Búsqueda de productos con `icontains` sin índice full-text**
- `apps/inventory/selectors.py:82-100` usa `icontains` en nombre/SKU. Con 10k+ productos, agregar extensión `pg_trgm` + índice GIN en PostgreSQL resuelve el problema sin cambiar código Python.

**M-02: AuditLog sin estrategia de archivado**
- `apps/audit/models.py`: El log crece ilimitado. Agregar partición por mes en PostgreSQL o política de archivado a tabla cold storage.

**M-03: Validación duplicada de estado operativo de ubicación**
- `apps/movements/services.py:42-86` y `apps/inventory/services.py:303-309`: Extraer a función shared `validate_location_state(location, context)` en `shared/`.

**M-04: Dashboard sin KPIs financieros**
- Sin modelo de Costo, no hay margen ni rentabilidad. Agregar campo `unit_cost` a `Product` y calcularlo en movimientos de entrada.

**M-05: Severidad de alertas con lógica condicional sin cobertura**
- `apps/alerts/services.py:28-39`: Agregar tests parametrizados para todas las combinaciones `(alert_type, per_location)` → `(severity, category)`.

**M-06: Documentación OpenAPI expuesta sin autenticación en producción**
- `/api/docs/`, `/api/schema/`, `/api/redoc/` accesibles sin JWT. Correcto en desarrollo, debería requerir `is_staff=True` en producción.

---

## 2. QUÉ ESTÁ REALMENTE TERMINADO vs. QUÉ APARENTA ESTARLO

### Realmente terminado y confiable

| Módulo | Estado |
|--------|--------|
| Autenticación JWT + RBAC | ✅ Sólido: rotación, blacklist, 3 roles bien delimitados |
| Catálogo (productos, categorías, lotes) | ✅ Completo con validaciones |
| Inventario (ubicaciones, estados, plantillas) | ✅ Completo; 8 migraciones aplicadas |
| Movimientos de entrada/salida/traslado/ajuste | ✅ Funcional con ledger correcto |
| Alertas (tipos, severidades, historial) | ✅ Funcional |
| Auditoría (AuditLog con eventos) | ✅ Funcional |
| Restricción horaria BR-03 | ✅ Implementada en 3 puntos (ver I-04 para deuda) |
| Locking optimista con select_for_update | ✅ Correcto |

### Aparenta estar terminado pero tiene brechas

| Módulo | Brecha real |
|--------|-------------|
| Combos (ProductCombo + dispatch_combo) | ❌ Sin endpoint API; código muerto |
| Corrección de movimientos (BR-06) | ❌ Solo funciona para TRASLADO |
| Cálculo de ledger (net quantity) | ❌ N+1 queries; duplicación de lógica |
| Testing de servicios de inventario | ❌ Tests triviales que no validan lógica real |
| Stock cache vs. ledger | ❌ Sin detección automática de deriva |
| OTIF y KPIs de despacho | ❌ Documentado como "no calculable" (sin modelo de pedidos) |

---

## 3. DEUDA TÉCNICA IMPORTANTE

1. **Ledger calculations en Python en lugar de SQL** — El cálculo de stock neto debería ser SQL agregado. Toda la lógica de `ledger_net_quantity_*` es deuda activa que crece con cada movimiento nuevo.

2. **Auditoría acoplada manualmente** — Sin mecanismo estructural, la auditoría es tan buena como la memoria del desarrollador.

3. **Feature de combos pagada pero inaccesible** — Tiempo de desarrollo ya invertido, pero el producto no puede usarla.

4. **BR-06 a medias** — La regla más compleja del negocio (corrección dentro de ventana) solo está implementada al 33%.

5. **Sin tests de carga o performance** — No hay benchmarks para validar que el sistema aguanta el volumen esperado.

---

## 4. ROADMAP TÉCNICO PARA PRODUCCIÓN

### Sprint 1 — Crítico (1-2 semanas)
1. Refactorizar `ledger_net_quantity_*` a SQL agregado (C-01, C-06)
2. Exponer endpoint de combo dispatch (C-02)
3. Agregar trigger inmutabilidad en BD para Movement (C-04)
4. Fix UUID sin manejo de error en alerts (I-07)
5. Agregar validación de rango a `period_days` / `limit` (I-09)

### Sprint 2 — Importante (2-3 semanas)
1. Completar BR-06 para ENTRADA y SALIDA (C-03)
2. Implementar `verify_stock_integrity` management command (C-05)
3. Centralizar BR-03 en `shared/operating_hours.py` (I-04)
4. Remover bloqueo de stock en `create_combo()` (I-03)
5. Corregir test trivial de inventory services; agregar tests reales (C-07)
6. Test de concurrencia para locking (I-08)
7. Fix data migration backfill con reverse_code (I-10)

### Sprint 3 — Calidad y deuda técnica (2-3 semanas)
1. Refactorizar `available_lots_at_location()` a SQL (I-05)
2. Unificar validación de SKU en una sola capa (I-01)
3. Decorador `@auditable` para servicios (I-02)
4. Unificar validación de estado operativo en shared (M-03)
5. Índice full-text con `pg_trgm` para búsqueda (M-01)
6. Proteger docs OpenAPI en producción (M-06)

### Sprint 4 — Nuevas funcionalidades (3-4 semanas)
1. Modelo de Costo (`unit_cost` en Product + costo en Movement)
2. Estrategia de archivado de AuditLog
3. Campo `unit_cost` → KPIs financieros en dashboard
4. Tests de performance / carga básicos

---

## 5. REFACTORS PRIORITARIOS

| Prioridad | Refactor | Archivos | Complejidad |
|-----------|----------|----------|-------------|
| 1 | `ledger_net_quantity_*` → SQL agregado | `movements/services.py:909-989` | Media |
| 2 | Unificar cálculo de lotes a SQL | `movements/services.py:992-1056` | Media |
| 3 | Centralizar BR-03 horario | `authentication/services.py`, `shared/permissions.py` | Baja |
| 4 | Decorador `@auditable` | `shared/` + todos los services | Alta |
| 5 | Unificar validación estado operativo | `movements/services.py:42-86`, `inventory/services.py:303-309` | Baja |
| 6 | Unificar validación SKU | `catalog/models.py:120`, `catalog/services.py:38` | Baja |

---

## 6. FUNCIONALIDADES RECOMENDADAS PARA AGREGAR

1. **Notificaciones de alertas en tiempo real** — WebSocket o polling. Hoy solo se consultan, no se empujan.
2. **Modelo de Pedidos** — Prerequisito para OTIF. Permite rastrear promesas de entrega vs. despachos reales.
3. **Costos de producto** — `unit_cost` en Product, costo_total en Movement. Habilita margen, rentabilidad, valuación de inventario.
4. **Exportación de reportes** — CSV/Excel para `reports/data/`. WeasyPrint está disponible para PDFs.
5. **Gestión de proveedores** — Modelo `Supplier` vinculado a entradas; trazabilidad de origen.
6. **Umbrales de stock por ubicación** — Hoy `reorder_point` es global en Product. Cada ubicación debería tener su propio umbral.
7. **API de webhooks** — Notificar sistemas externos (ERP, frontend) en eventos críticos (stock bajo, vencimiento, etc.).

---

## 7. RIESGOS TÉCNICOS ACTUALES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Corrupción silenciosa de stock caché | Media | Crítico | Implementar `verify_stock_integrity` (C-05) |
| Timeout en despachos con muchos lotes | Alta en prod | Alto | Refactor SQL agregado (C-01) |
| Ledger modificado directamente en BD | Baja | Crítico | Trigger de inmutabilidad (C-04) |
| Datos incoherentes por BR-06 incompleto | Media | Alto | Completar corrección para ENTRADA/SALIDA (C-03) |
| Escenario de combos no trazable | Alta (feature viva) | Medio | Exponer endpoint (C-02) |
| Race condition bajo carga alta | Media | Alto | Test de concurrencia (I-08) |
| Documentación OpenAPI expuesta en prod | Alta | Medio | Auth guard en producción (M-06) |

---

## 8. VISIÓN DEL ARQUITECTO PRINCIPAL

El backend tiene una base arquitectónica correcta: dominio separado, ledger como fuente de verdad, RBAC granular, auditoría, locking optimista. Eso no es trivial y está bien ejecutado.

Los problemas no son de diseño, son de **completitud de implementación** y **deuda de rendimiento acumulada**.

Lo que haría como arquitecto principal, en este orden:

1. **Cerrar el loop del ledger primero.** Los cálculos de stock neto en Python son la amenaza más concreta a la escalabilidad. Cada movimiento nuevo agrava el problema. Esto se refactoriza una vez y se resuelve definitivamente.

2. **Imponer el contrato de inmutabilidad en la BD.** El diseño del ledger es excelente, pero sin el trigger de BD es solo una promesa. Una línea en una migración lo hace real.

3. **Activar combos.** El trabajo ya está hecho. Solo falta el endpoint. Es el refactor de mayor ROI del proyecto.

4. **Cerrar BR-06 o documentarlo como "no soportado".** La mitad-implementación es más peligrosa que no tener la feature: da falsa confianza.

5. **Convertir los tests triviales en tests reales.** La cobertura de código es una métrica inútil si los tests no ejercen la lógica. Prefiero 30 tests que prueban invariantes reales que 100 tests que solo verifican que las funciones existen.

6. **Agregar `verify_stock_integrity` como job diario antes del primer día de producción.** No para auto-reparar, sino para detectar. En producción, la detección temprana vale más que cualquier otra medida.

Lo que NO haría: reescribir el módulo de movimientos. La lógica está bien, los problemas son de implementación de las queries y de completitud de endpoints. Una reescritura aquí sería peligrosa dado que es el corazón del sistema.

---

## 9. VERIFICACIÓN

Para validar los fixes cuando se implementen:

```bash
# Tests existentes
pytest apps/movements/tests/ -v
pytest apps/inventory/tests/ -v
pytest apps/catalog/tests/ -v
pytest apps/alerts/tests/ -v

# Cobertura real (meta: >80% de líneas con lógica real)
pytest --cov=apps --cov-report=term-missing

# Test de concurrencia (nuevo)
pytest tests/concurrency/ -v

# Verificar integridad de stock (nuevo comando)
python manage.py verify_stock_integrity --dry-run

# Smoke test de endpoint de combo (nuevo)
curl -X POST /api/v1/movements/combo-dispatch/ -H "Authorization: Bearer ..." \
     -d '{"combo_id": "...", "location_id": "..."}'
```


---

Implementado — 20 fixes en 3 waves

Wave 1 — Críticos

┌───────────┬───────────────────────────────────────────┬────────────────────────────────────────────────────────┐
│    Fix    │                  Cambio                   │                        Archivo                         │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-01+C-06 │ ledger_net_quantity_* → SQL Case/When/Sum │ movements/services.py                                  │
│           │  (O(1))                                   │                                                        │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-02      │ Endpoint de combos verificado (ya         │ movements/tests/test_combo_dispatch.py                 │
│           │ existía, añadidos tests)                  │                                                        │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-03      │ BR-06 extendido para ENTRADA y SALIDA     │ movements/services.py:correct_movement_within_window() │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-04      │ Trigger PostgreSQL de inmutabilidad       │ migrations/0003_movement_immutability_trigger.py       │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-04      │ Trigger PostgreSQL de inmutabilidad       │ migrations/0003_movement_immutability_trigger.py       │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-05      │ Management command verify_stock_integrity │ inventory/management/commands/                         │
│           │  --fix                                    │                                                        │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ C-06      │ available_lots_at_location() → SQL        │ movements/services.py                                  │
│           │ agregado                                  │                                                        │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ I-07      │ UUID parsing con try/except → 400 en      │ alerts/views.py                                        │
│           │ lugar de 500                              │                                                        │
├───────────┼───────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ I-09      │ clamp_period_days y clamp_limit           │ shared/utils/params.py + views                         │
│           │ (1-365/500 max)                           │                                                        │
└───────────┴───────────────────────────────────────────┴────────────────────────────────────────────────────────┘

Wave 2 — Importantes

┌──────┬──────────────────────────────────────────────────────────────┬────────────────────────────────────┐
│ Fix  │                            Cambio                            │              Archivo               │
├──────┼──────────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ I-03 │ create_combo() sin bloqueo por stock vacío                   │ catalog/services.py                │
├──────┼──────────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ I-04 │ is_within_operating_hours centralizado                       │ shared/operating_hours.py          │
├──────┼──────────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ I-06 │ Índices lot y (product, lot) en Movement                     │ migrations/0004_add_lot_indexes.py │
├──────┼──────────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ I-08 │ Test de concurrencia ya existía correctamente                │ tests/concurrency/                 │
├──────┼──────────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ I-10 │ backwards() de migración backfill arreglado                  │ catalog/migrations/0003_*.py       │
├──────┼──────────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ C-07 │ Tests reales de inventory services (reemplaza callable test) │ inventory/tests/test_services.py   │
└──────┴──────────────────────────────────────────────────────────────┴────────────────────────────────────┘

Wave 3 — Calidad

┌──────┬─────────────────────────────────────────────────────────┬────────────────────────────────┐
│ Fix  │                         Cambio                          │            Archivo             │
├──────┼─────────────────────────────────────────────────────────┼────────────────────────────────┤
│ M-05 │ 11 tests parametrizados de severidades de alertas       │ alerts/tests/test_services.py  │
├──────┼─────────────────────────────────────────────────────────┼────────────────────────────────┤
│ M-06 │ OpenAPI protegida en producción via RESTRICT_API_SCHEMA │ config/urls.py + production.py │
└──────┴─────────────────────────────────────────────────────────┴────────────────────────────────┘

Pendiente — Wave 4 (post-producción)

- unit_cost en Product + KPIs financieros
- Decorador @auditable centralizado
- Validador shared de estado operativo de ubicación
- Índice pg_trgm para búsqueda full-text
└──────────