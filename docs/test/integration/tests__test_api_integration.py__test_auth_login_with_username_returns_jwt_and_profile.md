# test_auth_login_with_username_returns_jwt_and_profile

## Nombre del test

`tests/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile`

## Propósito

Verificar que el login por `username` devuelve `access` y `refresh` y el perfil de usuario en la respuesta.

## Inputs

- Fixtures: `api_client`, `almacenista_user`

## Resultado esperado

Código 200, contiene `access`, `refresh` y campos de `user` (username, email, phone, role).

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
