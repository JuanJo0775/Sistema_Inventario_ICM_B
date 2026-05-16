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
