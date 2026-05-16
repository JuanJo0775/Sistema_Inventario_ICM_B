# test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window

## Nombre del test

`tests/test_api_integration.py::test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window`

## Propósito

RF-001 — Contrastar con el caso auxiliar: un `almacenista` puede renovar token fuera de la ventana auxiliar y obtener `access`.

## Inputs

- Fixtures: `api_client`, `almacenista_user`
- Uso de `patch` para simular tiempos (dentro y fuera de franja Bogotá).

## Resultado esperado

Renovación exitosa (200) y contiene `access` en la respuesta.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
