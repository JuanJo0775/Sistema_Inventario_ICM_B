import pytest

from apps.catalog.serializers import ProductDetailSerializer
from apps.catalog.services import create_product, resolve_identifier, update_product
from shared.utils.barcode import build_product_barcode
from tests.factories import CategoryFactory


def test_catalog_service_exports_identifier_resolver():
    assert callable(resolve_identifier)


@pytest.mark.django_db
def test_create_product_auto_generates_stable_barcode(almacenista_user):
    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {
            "sku": "ABC-1234",
            "name": "Producto de prueba",
            "category_id": category.id,
        },
    )

    assert product.barcode == build_product_barcode(product.id)

    detail = ProductDetailSerializer(product).data
    assert detail["barcode"] == product.barcode
    assert detail["barcode_type"] == "Code128"
    assert detail["barcode_payload"] == {
        "type": "Code128",
        "value": product.barcode,
    }
    assert detail["barcode_svg"].startswith("<?xml")
    assert detail["barcode_svg_data_uri"].startswith(
        "data:image/svg+xml;base64,"
    )


@pytest.mark.django_db
def test_update_product_keeps_existing_barcode(almacenista_user):
    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {
            "sku": "DEF-1234",
            "name": "Producto actualizado",
            "category_id": category.id,
        },
    )

    updated = update_product(
        almacenista_user,
        product.id,
        {"name": "Producto actualizado 2", "barcode": "OTRO-CODIGO"},
    )

    assert updated.barcode == product.barcode
    assert resolve_identifier(product.barcode).id == product.id


@pytest.mark.django_db
def test_update_product_backfills_missing_barcode(almacenista_user):
    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {
            "sku": "GHI-1234",
            "name": "Producto sin barcode",
            "category_id": category.id,
            "barcode": None,
        },
    )

    product.barcode = None
    product.save(update_fields=("barcode",))

    updated = update_product(
        almacenista_user,
        product.id,
        {"name": "Producto sin barcode 2"},
    )

    assert updated.barcode == build_product_barcode(product.id)
