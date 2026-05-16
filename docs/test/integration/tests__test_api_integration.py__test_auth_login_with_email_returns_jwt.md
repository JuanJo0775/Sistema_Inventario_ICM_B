# test_auth_login_with_email_returns_jwt

## Nombre del test

`tests/test_api_integration.py::test_auth_login_with_email_returns_jwt`

## Propósito

Verificar que el login por `email` devuelve tokens JWT y el ID de usuario.

## Inputs

- Fixtures: `api_client`, `almacenista_user`

## Resultado esperado

Código 200 y `r.data["user"]["id"] == almacenista_user.id`.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_auth_login_with_email_returns_jwt -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)
