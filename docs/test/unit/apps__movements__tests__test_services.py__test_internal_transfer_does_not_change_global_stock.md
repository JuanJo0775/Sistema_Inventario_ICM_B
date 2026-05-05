# test_internal_transfer_does_not_change_global_stock

## Nombre del test

`apps/movements/tests/test_services.py::test_internal_transfer_does_not_change_global_stock`

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
pytest apps/movements/tests/test_services.py::test_internal_transfer_does_not_change_global_stock -v
```

Código: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. línea 97)
