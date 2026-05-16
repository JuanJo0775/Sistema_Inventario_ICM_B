# test_auth_token_refresh_auxiliar_outside_hours_forbidden

## Nombre del test

`tests/test_api_integration.py::test_auth_token_refresh_auxiliar_outside_hours_forbidden`

## Propósito

RF-001, BR-03 — Asegurar que un `auxiliar` no puede renovar token fuera de la franja horaria permitida; la renovación debe aplicar la misma restricción que el login.

## Inputs

- Fixtures: `api_client`, `auxiliar_user`
- Uso de `patch` para simular tiempos (dentro y fuera de franja Bogotá).

## Resultado esperado

La renovación con `refresh` devuelve 403 cuando la hora actual está fuera de la franja permitida.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_auth_token_refresh_auxiliar_outside_hours_forbidden -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
