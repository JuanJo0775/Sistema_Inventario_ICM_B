import pytest

from apps.catalog.views import (
    CategoryListCreateView,
    ProductBarcodeView,
    ProductListCreateView,
    ResolveIdentifierView,
)


def test_catalog_views_are_available():
    assert CategoryListCreateView is not None
    assert ProductListCreateView is not None
    assert ProductBarcodeView is not None
    assert ResolveIdentifierView is not None


@pytest.mark.django_db
def test_product_barcode_endpoint_returns_ready_to_consume_payload(
    authenticated_almacenista_client, sample_product
):
    url = f"/api/v1/catalog/products/{sample_product.id}/barcode/"

    response = authenticated_almacenista_client.get(url)

    assert response.status_code == 200
    assert response.data["product_id"] == str(sample_product.id)
    assert response.data["barcode"] == sample_product.barcode
    assert response.data["barcode_type"] == "Code128"
    assert response.data["render_format"] == "svg"
    assert response.data["barcode_svg"].startswith("<?xml")
    assert response.data["barcode_svg_data_uri"].startswith(
        "data:image/svg+xml;base64,"
    )
