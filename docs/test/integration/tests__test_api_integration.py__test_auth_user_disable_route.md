# test_auth_user_disable_route

## Nombre del test

`tests/test_api_integration.py::test_auth_user_disable_route`

## Propósito

Verificar que la ruta `auth-user-disable` permite a un `almacenista` desactivar a otro usuario (`auxiliar`) y que el cambio persiste en la BD.

## Inputs

- Fixtures: `api_client`, `almacenista_user`, `auxiliar_user`

## Resultado esperado

Código 204, y `auxiliar_user.is_active` pasa a `False` tras `refresh_from_db()`.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_auth_user_disable_route -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
