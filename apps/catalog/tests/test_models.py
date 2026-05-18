import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Category, Product
from tests.factories import CategoryFactory


def test_product_sku_field():
    assert Product._meta.get_field("sku").max_length == 100


def test_category_slug_unique():
    assert Category._meta.get_field("slug").unique


@pytest.mark.django_db
def test_product_full_clean_requires_can_prefix_for_can_brand():
    """RF-003, BR-12 — El SKU debe seguir el patrón 1–4 letras, guion, 1–4 dígitos."""
    cat = CategoryFactory()
    p = Product(
        sku="ELECTRO001",  # formato inválido (falta guion)
        name="Ejemplo",
        category=cat,
        subcategory=None,
        brand="Can",
    )
    with pytest.raises(ValidationError, match="Formato SKU inválido"):
        p.full_clean()
