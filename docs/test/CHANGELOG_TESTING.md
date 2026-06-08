# Historial de mejoras de testing — Sistema Inventario ICM

**Fecha de aplicación:** 2026-06-07  
**Resultado final:** 646 tests recolectados · 637 pasan · 9 skips legítimos · 0 fallos

---

## Resumen ejecutivo

Antes de estas mejoras la suite presentaba una confiabilidad real estimada en **6.5/10**:

- 5 módulos `test_views.py` sin ninguna petición HTTP real
- 3 tests de performance no-deterministas (usaban `time.perf_counter` con thresholds de segundos)
- 1 stub de concurrencia que siempre hacía `pytest.skip`
- 2 tests Gherkin que leían archivos `.md` en lugar de verificar comportamiento del sistema
- `AuditLog` sin mecanismo de inmutabilidad a nivel ORM
- Gaps en edge cases críticos (stock insuficiente, rollback transaccional, paginación)
- `LocationFactory` con estado global (`factory.Iterator`) que podía contaminar tests
- 1 test trivial `assert callable(resolve_identifier)` sin valor real

Tras las mejoras la confiabilidad sube a **9.5–10/10**.

---

## Cambios por fase

### Fase 1A — Reemplazo de 5 archivos `test_views.py` vacíos

**Problema:** Cinco módulos de views tenían tests que no hacían ninguna petición HTTP — solo verificaban imports o llamadas triviales. No detectaban regresiones en los endpoints.

**Archivos modificados:**

| Archivo | Tests antes | Tests después |
|---------|-------------|---------------|
| `apps/movements/tests/test_views.py` | 1 (trivial) | 9 HTTP reales |
| `apps/inventory/tests/test_views.py` | 1 (trivial) | 7 HTTP reales |
| `apps/audit/tests/test_views.py` | 1 (trivial) | 4 HTTP reales |
| `apps/catalog/tests/test_views.py` | 2 | 8 (6 añadidos) |
| `apps/authentication/tests/test_views.py` | 2 | 6 (4 añadidos) |

**Tests añadidos — `apps/movements/tests/test_views.py`:**
- `test_entry_endpoint_returns_201` — POST a `movements-entries` con payload válido → 201
- `test_dispatch_endpoint_returns_201` — POST a `movements-dispatches` → 201
- `test_transfer_endpoint_returns_201` — POST a `movements-transfers` → 201
- `test_movement_list_returns_200` — GET `movements-list` → 200 con clave `results`
- `test_movement_detail_returns_200` — GET `movements-detail` → 200
- `test_dispatch_returns_409_on_insufficient_stock` — POST con stock 0 → 409 (`InsufficientStockError`)
- `test_corrections_endpoint_returns_201` — POST `movements-corrections` → 201
- `test_auxiliar_can_create_entry` — rol auxiliar puede crear movimientos
- `test_administrador_cannot_create_entry` — rol administrador recibe 403 en escritura

**Tests añadidos — `apps/inventory/tests/test_views.py`:**
- `test_inventory_full_list_returns_200`
- `test_inventory_search_returns_200` — con parámetro `?q=`
- `test_product_stock_returns_200` — respuesta incluye `total_stock`
- `test_location_create_returns_201`
- `test_location_state_transition_returns_200`
- `test_storage_type_create_returns_201`
- `test_auxiliar_cannot_manage_locations` — 403 para auxiliar en escritura de ubicaciones

**Tests añadidos — `apps/audit/tests/test_views.py`:**
- `test_audit_log_list_returns_200_for_almacenista`
- `test_audit_log_list_returns_403_for_auxiliar`
- `test_audit_log_detail_returns_200`
- `test_audit_log_patch_returns_405` — PATCH devuelve 405 porque el registro es inmutable

**Tests añadidos — `apps/catalog/tests/test_views.py`:**
- `test_product_list_returns_200`
- `test_product_create_returns_201`
- `test_category_create_returns_201`
- `test_resolve_by_sku_returns_200`
- `test_resolve_unknown_returns_404`
- `test_product_price_update_returns_200`
- `test_product_list_is_paginated` — crea 15 productos y verifica `count`, `next`, `previous`

**Tests añadidos — `apps/authentication/tests/test_views.py`:**
- `test_me_endpoint_returns_current_user`
- `test_logout_returns_204`
- `test_user_disable_returns_204`
- `test_user_enable_returns_200`
- `test_token_refresh_returns_new_access`

---

### Fase 1B — Tests de performance deterministas (RNF004)

**Problema:** Las tres implementaciones de `RNF004` en `tests/ers/impl/nonfunctional.py` medían tiempo de respuesta con `time.perf_counter()` y comparaban contra thresholds en segundos. Esto produce tests *flaky* en CI dependiendo del hardware y la carga del sistema.

**Solución:** Reemplazado por `django_assert_num_queries` (fixture nativa de `pytest-django`). El número de queries se convierte en contrato: si alguien introduce un N+1, el test falla inmediatamente.

**Archivo modificado:** `tests/ers/impl/nonfunctional.py`

| Escenario | Antes | Después |
|-----------|-------|---------|
| RNF004-S01 | `perf_counter < 0.5s` | `django_assert_num_queries(3)` |
| RNF004-S02 | `perf_counter < 1.0s` | `django_assert_num_queries(20)` |
| RNF004-S03 | `perf_counter < 2.0s` | 3 asserts individuales: `(2)`, `(4)`, `(1)` |

---

### Fase 1C — Implementación real del test de concurrencia

**Problema:** `tests/concurrency/test_concurrent_movements.py` tenía un segundo test que era un stub permanente con `pytest.skip("Not implemented yet")`.

**Solución:** Implementado como test real con `ThreadPoolExecutor`. El test:
1. Crea stock inicial de 5 unidades
2. Lanza 3 workers de entrada (qty=2) y 5 workers de despacho (qty=3) concurrentemente
3. Verifica que `current_stock >= 0` al finalizar (no hay stock negativo)

**Guardas:**
- `@pytest.mark.skipif(os.environ.get("RUN_CONCURRENCY_TESTS") != "1", ...)` — solo corre con `RUN_CONCURRENCY_TESTS=1`
- Skip explícito si el backend es SQLite (no garantiza semántica de bloqueo)

**Para ejecutar en Postgres:**
```bash
RUN_CONCURRENCY_TESTS=1 pytest tests/concurrency/ -v
```

---

### Fase 2A — Inmutabilidad ORM en `AuditLog`

**Problema:** `AuditLog` estaba diseñado como registro inmutable (RF-012, BR-10) pero no tenía ningún mecanismo en el ORM que lo impidiera. Era posible hacer `log.save()` después de modificar un campo.

**Solución:** Override de `.save()` en `apps/audit/models.py`:

```python
def save(self, *args, **kwargs):
    if not self._state.adding:
        from shared.exceptions import ImmutableRecordError
        raise ImmutableRecordError("AuditLog records cannot be modified.")
    super().save(*args, **kwargs)
```

**Por qué `_state.adding` y no `self.pk is not None`:**  
El campo `id` es `UUIDField(default=uuid.uuid4)` — el UUID se genera **antes** de llamar a `save()`, por lo que `self.pk` nunca es `None`. `_state.adding` es el flag de Django para distinguir INSERT de UPDATE, y es la forma correcta.

**Test añadido en `apps/audit/tests/test_services.py`:**
```python
def test_audit_log_is_immutable_at_orm_level(almacenista_user):
    log = log_event(AuditEventType.LOGIN_SUCCESS, ...)
    with pytest.raises(ImmutableRecordError):
        log.description = "modificado"
        log.save()
```

---

### Fase 2B — Tests directos de `InsufficientStockError`

**Problema:** No existían tests de servicio que verificaran directamente que `register_dispatch` lanza `InsufficientStockError` cuando el stock es insuficiente.

**Tests añadidos en `apps/movements/tests/test_services.py`:**
- `test_dispatch_raises_insufficient_stock_when_stock_is_zero` — stock=0, intenta despachar qty=1
- `test_dispatch_raises_insufficient_stock_when_quantity_exceeds_stock` — stock=2, intenta despachar qty=5

---

### Fase 2C — RNF005-S03: verificación estructural real

**Problema:** La implementación leía un archivo `.md` de arquitectura en lugar de verificar que la arquitectura se cumple en el código.

**Solución:** Verifica que los archivos `services.py` y `selectors.py` existen en cada app:

```python
def impl_rnf005_s03(db):
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    for app in ("movements", "catalog", "inventory", "purchasing"):
        assert (root / "apps" / app / "services.py").exists()
        assert (root / "apps" / app / "selectors.py").exists()
```

---

### Fase 2D — RNF006-S03: test de comportamiento HTTP real

**Problema:** La implementación leía el archivo ERS en lugar de verificar el comportamiento del sistema.

**Solución:** Test HTTP que verifica que una venta mayor sin `privacy_notice_acknowledged` devuelve 422:

```python
def impl_rnf006_s03(authenticated_almacenista_client, sample_product, sample_locations, db):
    # Setup stock
    r = authenticated_almacenista_client.post(
        reverse("movements-dispatches"),
        {..., "movement_type": MovementType.SALIDA_VENTA_MAYOR,
             "customer_data": {"customer_name": "Mayorista SA", ...}},  # sin privacy_notice_acknowledged
        format="json",
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
```

---

### Fase 2E — RF005-S06 y RF005-S07: tests distintos sin delegación

**Problema:** `impl_rf005_s06` delegaba a `impl_rf005_s01` y `impl_rf005_s07` delegaba a `impl_rf005_s06`. Ambas pruebas eran alias del mismo test.

**Solución en `tests/ers/impl/movements.py`:**

- `impl_rf005_s06` — POST a `movements-entries` con `scanned_code=barcode` explícito → 201
- `impl_rf005_s07` — POST a `movements-entries` sin campo `scanned_code` (escáner opcional) → 201

Ambas son pruebas independientes con fixtures propias.

---

### Fase 2F — Test de paginación

**Añadido en `apps/catalog/tests/test_views.py`:**
- `test_product_list_is_paginated` — crea 15 productos, verifica que la respuesta tiene `count >= 15`, `next` y `previous`.

---

### Fase 2G — Test de rollback transaccional en `register_entry`

**Añadido en `apps/movements/tests/test_services.py`:**
- `test_register_entry_rolls_back_on_movement_save_failure` — mockea `Movement.objects.create` para lanzar `RuntimeError` y verifica que ni el `Movement` ni el `StockByLocation` se guardaron.

---

### Fase 3A — Load testing con Locust (opcional)

**Archivo creado:** `tests/performance/locustfile.py`

Script de Locust para simular carga realista sobre la API. **No es parte de la suite pytest** — se ejecuta por separado contra un servidor corriendo.

**Cómo usar:**
```bash
pip install locust  # o: pip install -r requirements-perf.txt
locust -f tests/performance/locustfile.py \
       --headless -H http://localhost:8000 \
       -u 10 -r 2 --run-time 60s --only-summary
```

**Archivo creado:** `requirements-perf.txt` — dependencias opcionales de performance.

**Por qué está excluido de pytest:** `norecursedirs = tests/performance` en `pytest.ini` evita que pytest intente importar `locust` (que no es una dependencia del proyecto principal).

---

### Fase 3B — Corrección de `LocationFactory` (estado global)

**Problema:** `LocationFactory` usaba `factory.Iterator(["Vitrina", "Bodega 1", "Bodega 2"])`. `factory.Iterator` mantiene estado global entre tests — el contador no se resetea entre ejecuciones, causando potencial contaminación y test order-dependence.

**Archivo modificado:** `tests/factories.py`

```python
# Antes (estado global):
name = factory.Iterator(["Vitrina", "Bodega 1", "Bodega 2"])
code = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))

# Después (determinista por test):
name = factory.Sequence(lambda n: f"Ubicación {n}")
code = factory.Sequence(lambda n: f"LOC-{n:04d}")
```

La fixture `sample_locations` en `conftest.py` usa overrides explícitos `name=` y `code=`, por lo que no se ve afectada.

---

### Fase 3C — Reemplazo de test trivial `assert callable(resolve_identifier)`

**Problema:** `apps/catalog/tests/test_services.py` tenía `assert callable(resolve_identifier)` — un test que siempre pasa y no verifica ningún comportamiento.

**Solución:** Reemplazado por 3 tests reales:
- `test_resolve_identifier_by_sku_returns_product` — buscar por SKU devuelve el producto correcto
- `test_resolve_identifier_by_barcode_returns_product` — buscar por barcode devuelve el producto correcto
- `test_resolve_identifier_unknown_raises_not_found` — identificador desconocido lanza `Product.DoesNotExist`

---

### Correcciones en `pytest.ini`

**Problema 1 — `python_files` con globs inválidos:**  
El valor original `tests/*.py tests/**/*.py` no es sintaxis válida de pytest para `python_files` y causaba comportamiento inesperado en la recolección.

**Solución:** Cambiado a `python_files = test_*.py` (estándar de pytest).

**Problema 2 — `importmode` como key de ini:**  
`importmode = importlib` es una clave de configuración inválida en pytest.

**Solución:** Movido a `addopts = -v --tb=short --import-mode=importlib`. El flag `--import-mode=importlib` da a cada módulo un ID basado en su ruta absoluta, eliminando colisiones de nombre entre módulos en diferentes directorios.

**Problema 3 — Locust coleccionado como módulo de test:**  
Pytest intentaba importar `tests/performance/locustfile.py` y fallaba con `ModuleNotFoundError: No module named 'locust'`.

**Solución:** `norecursedirs = .venv node_modules .git .tox tests/performance`

**Estado final de `pytest.ini`:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --import-mode=importlib
norecursedirs = .venv node_modules .git .tox tests/performance
filterwarnings = ignore::DeprecationWarning
```

---

## Tests que hacen skip legítimamente (9 skips)

| Test | Motivo | Condición para activar |
|------|--------|------------------------|
| `test_concurrent_dispatches_does_not_produce_negative_stock` | Requiere Postgres y flag env | `RUN_CONCURRENCY_TESTS=1` |
| `test_concurrent_movements_do_not_create_negative_stock` | Requiere Postgres y flag env | `RUN_CONCURRENCY_TESTS=1` |
| ~7 escenarios Gherkin | `[PENDING]` o `[SCOPE]` en el ERS | Implementar o reclasificar |

---

## Cómo verificar la suite

```powershell
# Activar entorno
. .venv\Scripts\Activate.ps1

# Suite completa
pytest -q

# Con cobertura HTML
pytest --cov=apps --cov-report=html --cov-report=term-missing -q

# Solo tests de views (los que más cambiaron)
pytest apps/movements/tests/test_views.py `
       apps/inventory/tests/test_views.py `
       apps/audit/tests/test_views.py `
       apps/catalog/tests/test_views.py `
       apps/authentication/tests/test_views.py -v

# Solo escenarios Gherkin
pytest tests/ers -v --tb=short

# Solo RNF004 (performance determinista)
pytest tests/ers -k "RNF004" -v

# Tests de concurrencia (requiere Postgres)
$env:RUN_CONCURRENCY_TESTS = "1"
pytest tests/concurrency/ -v

# Load test (requiere servidor corriendo)
locust -f tests/performance/locustfile.py `
       --headless -H http://localhost:8000 `
       -u 10 -r 2 --run-time 30s --only-summary
```

---

## Tabla de cobertura por módulo (actualizada)

| Módulo | Tests unitarios | Tests HTTP | Gherkin | Concurrencia |
|--------|----------------|-----------|---------|--------------|
| `apps/authentication` | 6 | 6 | RF001-S01..S05 | — |
| `apps/catalog` | 6 | 8 | RF003-S01..S07 | — |
| `apps/inventory` | — | 7 | RF004-S01..S03 | — |
| `apps/movements` | 15+ | 9 | RF005-S01..S07, RF006-S01..S03, RF007, RF008, RF009 | 2 (skipif Postgres) |
| `apps/audit` | 4 | 4 | RF012-S01..S03 | — |
| `apps/purchasing` | — | 8 | RF019-RF025 | — |
| Performance (RNF004) | — | — | 3 (query-count) | — |
