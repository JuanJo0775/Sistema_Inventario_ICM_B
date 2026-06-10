import pytest

from apps.catalog.serializers import ProductDetailSerializer
from apps.catalog.services import create_product, resolve_identifier, update_product
from shared.exceptions import DomainValidationError
from shared.utils.barcode import build_product_barcode
from tests.factories import CategoryFactory


@pytest.mark.django_db
def test_resolve_identifier_by_sku_returns_product():
    from tests.factories import CategoryFactory, ProductFactory

    category = CategoryFactory()
    product = ProductFactory(sku="RES-0001", category=category)
    result = resolve_identifier("RES-0001")
    assert result.id == product.id


@pytest.mark.django_db
def test_resolve_identifier_by_barcode_returns_product():
    from tests.factories import CategoryFactory, ProductFactory

    category = CategoryFactory()
    product = ProductFactory(sku="RES-0002", category=category)
    result = resolve_identifier(product.barcode)
    assert result.id == product.id


@pytest.mark.django_db
def test_resolve_identifier_unknown_raises_not_found():
    from apps.catalog.models import Product

    with pytest.raises(Product.DoesNotExist):
        resolve_identifier("SKU-INEXISTENTE-9999")


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

    assert product.barcode == product.sku
    assert product.barcode == build_product_barcode(product.sku)

    detail = ProductDetailSerializer(product).data
    assert detail["barcode"] == product.barcode
    assert detail["barcode_type"] == "Code128"
    assert detail["barcode_payload"] == {
        "type": "Code128",
        "value": product.barcode,
    }
    assert detail["barcode_svg"].startswith("<?xml")
    assert detail["barcode_svg_data_uri"].startswith("data:image/svg+xml;base64,")


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

    assert updated.barcode == product.sku


@pytest.mark.django_db
def test_create_product_uses_sku_as_barcode_even_if_barcode_provided(
    almacenista_user,
):
    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {
            "sku": "JKL-1234",
            "name": "Producto con colisión",
            "category_id": category.id,
            "barcode": "OTRO-CODIGO",
        },
    )

    assert product.barcode == product.sku


@pytest.mark.django_db
def test_update_product_rejects_sku_changes(almacenista_user):
    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {
            "sku": "MNO-1234",
            "name": "Producto inmutable",
            "category_id": category.id,
        },
    )

    with pytest.raises(DomainValidationError) as exc_info:
        update_product(
            almacenista_user,
            product.id,
            {"sku": "MNO-9999"},
        )

    assert "SKU es inmutable" in str(exc_info.value)
