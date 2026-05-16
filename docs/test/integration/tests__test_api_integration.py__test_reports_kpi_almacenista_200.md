# test_reports_kpi_almacenista_200

## Nombre del test

`tests/test_api_integration.py::test_reports_kpi_almacenista_200`

## Propósito

Comprobar que un usuario con rol `almacenista` obtiene 200 y el payload incluye `movements_today`.

## Inputs

- Fixture: `authenticated_almacenista_client`

## Resultado esperado

Código 200 y campo `movements_today` presente en la respuesta.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_reports_kpi_almacenista_200 -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
