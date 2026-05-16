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
