# test_auth_login_with_username_returns_jwt_and_profile

## Nombre del test

`tests/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile`

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
pytest tests/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile -v
```

Código: [`tests/test_api_integration.py`](../../tests/test_api_integration.py) (aprox. línea 46)
