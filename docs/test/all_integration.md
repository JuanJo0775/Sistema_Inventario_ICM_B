

<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_alerts_list_uses_is_resolved_filter.md -->

# test_alerts_list_uses_is_resolved_filter

## Nombre del test

`tests/test_api_integration.py::test_alerts_list_uses_is_resolved_filter`

## Propósito

Comprobar que el listado de `alerts` devuelve elementos y que el filtro `is_resolved` se aplica correctamente.

## Inputs

- Fixtures: `authenticated_almacenista_client`, `sample_product`
- Crea una `Alert` con `is_resolved=False` antes de la petición.

## Resultado esperado

Código 200 y `len(r.data["results"]) >= 1`.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_alerts_list_uses_is_resolved_filter -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_auth_login_with_email_returns_jwt.md -->

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


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_auth_login_with_username_returns_jwt_and_profile.md -->

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


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window.md -->

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


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_auth_token_refresh_auxiliar_outside_hours_forbidden.md -->

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


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_auth_user_disable_route.md -->

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


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_catalog_resolve_identifier_param.md -->

# test_catalog_resolve_identifier_param

## Nombre del test

`tests/test_api_integration.py::test_catalog_resolve_identifier_param`

## Propósito

Comprobar que la consulta `catalog-resolve` acepta el parámetro `identifier` y devuelve el SKU correspondiente.

## Inputs

- Fixtures: `authenticated_almacenista_client`, `sample_product`

## Resultado esperado

Código 200 y `r.data["sku"] == sample_product.sku`.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_catalog_resolve_identifier_param -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_inventory_full_list_authenticated.md -->

# test_inventory_full_list_authenticated

## Nombre del test

`tests/test_api_integration.py::test_inventory_full_list_authenticated`

## Propósito

Validar que el endpoint `inventory-full` está disponible para un cliente autenticado y devuelve `results`.

## Inputs

- Fixtures: `authenticated_almacenista_client`, `sample_product`

## Resultado esperado

Código 200 y la respuesta contiene `results`.

## Link directo al test

```bash
pytest tests/test_api_integration.py::test_inventory_full_list_authenticated -v
```

Código: [tests/test_api_integration.py](tests/test_api_integration.py)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_reports_kpi_almacenista_200.md -->

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


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\integration\tests__test_api_integration.py__test_reports_kpi_requires_auth.md -->

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
