# test_only_almacenista_creates_users

## Nombre del test

`apps/authentication/tests/test_services.py::test_only_almacenista_creates_users`

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
pytest apps/authentication/tests/test_services.py::test_only_almacenista_creates_users -v
```

Código: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. línea 24)
