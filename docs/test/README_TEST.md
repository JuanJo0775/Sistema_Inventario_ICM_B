# Documentación de pruebas — Sistema Inventario ICM

## Fuentes de verdad

1. **`docs/ERS_ICM_Requisitos.md`** — RF/RNF y criterios **Gherkin** (Given / When / Then).
2. **`docs/ICM_Informe_Elicitacion_v2_plus.docx.md`** — contexto de negocio ICM.
3. **`docs/README_ARQUITECTURA.md`**, **`docs/README_API.md`**.

## Estructura de documentación por test

| Ubicación | Contenido |
|-----------|------------|
| `docs/test/scenarios/` | **Un archivo `.md` por cada escenario Gherkin del ERS** (95 archivos). Formato: nombre del test, propósito, requisito, inputs (extracto ERS), resultado esperado, link `pytest` y estado de automatización. |
| `docs/test/unit/` | **Un archivo `.md` por cada test** fuera de la suite Gherkin dinámica (p. ej. `apps/*/tests/*.py`, `tests/test_api_integration.py`). |
| `docs/test/gherkin_scenarios.json` | Metadatos parseados del ERS (título, cuerpo Gherkin por escenario). |
| `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` | Matriz resumida RF ↔ tests (referencia viva). |

## Suite Gherkin (1 test = 1 escenario ERS)

- **Código:** `tests/ers/test_gherkin_dynamic.py` genera **95** funciones `test_RFxxx_Sxx` / `test_RNFxxx_Sxx`.
- **Implementación:** `tests/ers/gherkin_impl.py` — diccionario `IMPLEMENTATIONS` enlaza escenario → función Python. Si un escenario no está en el diccionario, el test hace **`pytest.skip`** con motivo (UI pura, exportación Excel, concurrencia multi-hilo, aprobación de devoluciones no modelada, etc.).
- **Regenerar escenarios y MD** tras cambios en el ERS:

```bash
python scripts/parse_ers_gherkin.py
```

- **Sincronizar lista de escenarios implementados:** editar `_IMPL_IDS` en `scripts/parse_ers_gherkin.py` y el dict `IMPLEMENTATIONS` en `tests/ers/gherkin_impl.py` (deben coincidir).

## Tests unitarios / integración (no Gherkin dinámico)

Regenerar documentación:

```bash
python scripts/generate_non_gherkin_test_docs.py
```

## Ejecución pytest

```bash
# Toda la suite (incluye Gherkin + apps + tests)
pytest -q

# Solo escenarios ERS
pytest tests/ers/test_gherkin_dynamic.py -v

# Solo implementados (sin skip) — ejemplo filtro por nombre
pytest tests/ers/test_gherkin_dynamic.py -k "RF001" -v

# Un escenario concreto
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S01 -v

# Por app clásica
pytest apps/movements/tests/ -v
```

## Definition of Done (testing)

- `pytest` completo en verde; skips solo en escenarios Gherkin **explícitamente pendientes** de backend.
- Nuevas automatizaciones Gherkin: añadir función en `gherkin_impl.py`, registrar en `IMPLEMENTATIONS`, actualizar `_IMPL_IDS` en `parse_ers_gherkin.py` y regenerar MD.
- Contratos RF/BR nuevos reflejados en docstrings y, si aplica, en `TRAZABILIDAD_ERS_GHERKIN.md`.

## Mantenimiento

- Añadir implementación: función en `tests/ers/gherkin_impl.py` + clave en `IMPLEMENTATIONS` + id en `_IMPL_IDS` en `scripts/parse_ers_gherkin.py`  
  → `python scripts/parse_ers_gherkin.py`

- Regenerar docs de tests unitarios:  
  `python scripts/generate_non_gherkin_test_docs.py`