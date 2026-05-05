# test_audit_model_exposes_event_types

## Nombre del test

`apps/audit/tests/test_models.py::test_audit_model_exposes_event_types`

## Propósito

Prueba unitaria o de integración del backend ICM (fuera del mapeo 1:1 ERS Gherkin en `tests/ers/test_gherkin_dynamic.py`). Consultar docstring en el código fuente para el detalle del caso.

## Requisito o caso de negocio asociado

Ver docstring del test y módulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementación.

## Resultado esperado

Aserciones del test (`assert`); ver código en la línea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_models.py::test_audit_model_exposes_event_types -v
```

Código: [`apps/audit/tests/test_models.py`](../../apps/audit/tests/test_models.py) (aprox. línea 4)
