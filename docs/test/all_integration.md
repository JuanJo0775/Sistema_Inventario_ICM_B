<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\index.md -->

# Ãndice de tests (integraciÃ³n)
| CÃ³digo | Test | Archivo |
|---|---|---|
| INT-0001 | test_alerts_list_uses_is_resolved_filter | [INT-0001.md](./INT-0001.md) |
| INT-0002 | test_auth_login_with_email_returns_jwt | [INT-0002.md](./INT-0002.md) |
| INT-0003 | test_auth_login_with_username_returns_jwt_and_profile | [INT-0003.md](./INT-0003.md) |
| INT-0004 | test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window | [INT-0004.md](./INT-0004.md) |
| INT-0005 | test_auth_token_refresh_auxiliar_outside_hours_forbidden | [INT-0005.md](./INT-0005.md) |
| INT-0006 | test_auth_user_disable_route | [INT-0006.md](./INT-0006.md) |
| INT-0007 | test_catalog_resolve_identifier_param | [INT-0007.md](./INT-0007.md) |
| INT-0008 | test_inventory_full_list_authenticated | [INT-0008.md](./INT-0008.md) |
| INT-0009 | test_reports_kpi_almacenista_200 | [INT-0009.md](./INT-0009.md) |
| INT-0010 | test_reports_kpi_requires_auth | [INT-0010.md](./INT-0010.md) |


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0001.md -->

**CÃ³digo:** INT-0001

# test_alerts_list_uses_is_resolved_filter

## Nombre del test

`tests/integration/test_api_integration.py::test_alerts_list_uses_is_resolved_filter`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_alerts_list_uses_is_resolved_filter -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 137)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0002.md -->

**CÃ³digo:** INT-0002

# test_auth_login_with_email_returns_jwt

## Nombre del test

`tests/integration/test_api_integration.py::test_auth_login_with_email_returns_jwt`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_auth_login_with_email_returns_jwt -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 62)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0003.md -->

**CÃ³digo:** INT-0003

# test_auth_login_with_username_returns_jwt_and_profile

## Nombre del test

`tests/integration/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 46)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0004.md -->

**CÃ³digo:** INT-0004

# test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window

## Nombre del test

`tests/integration/test_api_integration.py::test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 101)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0005.md -->

**CÃ³digo:** INT-0005

# test_auth_token_refresh_auxiliar_outside_hours_forbidden

## Nombre del test

`tests/integration/test_api_integration.py::test_auth_token_refresh_auxiliar_outside_hours_forbidden`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_auth_token_refresh_auxiliar_outside_hours_forbidden -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 74)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0006.md -->

**CÃ³digo:** INT-0006

# test_auth_user_disable_route

## Nombre del test

`tests/integration/test_api_integration.py::test_auth_user_disable_route`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_auth_user_disable_route -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 127)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0007.md -->

**CÃ³digo:** INT-0007

# test_catalog_resolve_identifier_param

## Nombre del test

`tests/integration/test_api_integration.py::test_catalog_resolve_identifier_param`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_catalog_resolve_identifier_param -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 38)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0008.md -->

**CÃ³digo:** INT-0008

# test_inventory_full_list_authenticated

## Nombre del test

`tests/integration/test_api_integration.py::test_inventory_full_list_authenticated`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_inventory_full_list_authenticated -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 30)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0009.md -->

**CÃ³digo:** INT-0009

# test_reports_kpi_almacenista_200

## Nombre del test

`tests/integration/test_api_integration.py::test_reports_kpi_almacenista_200`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_reports_kpi_almacenista_200 -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 22)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\INT-0010.md -->

**CÃ³digo:** INT-0010

# test_reports_kpi_requires_auth

## Nombre del test

`tests/integration/test_api_integration.py::test_reports_kpi_requires_auth`

## PropÃ³sito

Prueba de integraciÃ³n HTTP (API) â€” validar flujos y contratos entre capas.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest tests/integration/test_api_integration.py::test_reports_kpi_requires_auth -v
```

CÃ³digo: [`tests/integration/test_api_integration.py`](../../tests/integration/test_api_integration.py) (aprox. lÃ­nea 16)
