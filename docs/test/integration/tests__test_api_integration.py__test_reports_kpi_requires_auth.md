"""
Documento generado: descripción del test de integración
"""

# test_reports_kpi_requires_auth

## Nombre del test

`tests/test_api_integration.py::test_reports_kpi_requires_auth`

## Propósito

Verificar que el endpoint `reports-kpi` requiere autenticación y devuelve 401 cuando no hay credenciales.

## Inputs

- Fixture: `api_client`

## Resultado esperado

Respuesta HTTP 401 Unauthorized.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_reports_kpi_requires_auth -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
