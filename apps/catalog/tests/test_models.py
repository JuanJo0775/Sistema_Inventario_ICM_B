from apps.catalog.models import Category, Product


def test_product_sku_field():
    assert Product._meta.get_field("sku").max_length == 100


def test_category_slug_unique():
    assert Category._meta.get_field("slug").unique
