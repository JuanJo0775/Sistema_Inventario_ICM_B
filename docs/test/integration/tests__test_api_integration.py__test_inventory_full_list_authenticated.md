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
