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
    """
    RF-003, BR-12 — Prefijo CAN- en SKU (catálogo / Admin).

    Criterio ERS (Gherkin implícito en RF-003 / reglas BR-12): productos marca Can deben usar CAN-.
    Ver `docs/ERS_ICM_Requisitos.md` sección RF-003 y tabla de trazabilidad BR-12.
    """
    cat = CategoryFactory()
    p = Product(
        sku="ELECTRO-001",
        name="Ejemplo",
        category=cat,
        subcategory=None,
        brand="Can",
    )
    with pytest.raises(ValidationError, match="CAN-"):
        p.full_clean()
