"""Tests de integración del importer (requieren BD)."""

from __future__ import annotations

import pytest

from scripts.import_catalog.importer import ImportResult, import_rows
from scripts.import_catalog.transformer import ImportRow


def make_import_row(
    sku: str = "CT-0001",
    name: str = "Camilla Test",
    category: str = "Camillas Test",
    generated: bool = False,
    transformed: bool = False,
    original_sku: str = "",
) -> ImportRow:
    return ImportRow(
        category_name=category,
        sku=sku,
        name=name,
        sku_was_generated=generated,
        sku_was_transformed=transformed,
        original_sku=original_sku,
    )


@pytest.mark.django_db
class TestImportRows:
    def test_creates_categories_and_products(self, almacenista_user):
        rows = [
            make_import_row("CT-0001", "Camilla A", "Camillas Import"),
            make_import_row("CT-0002", "Camilla B", "Camillas Import"),
        ]
        result = import_rows(almacenista_user, rows)
        assert result.categories_created == 1
        assert result.categories_skipped == 0
        assert result.products_created == 2
        assert result.products_skipped == 0
        assert result.errors == []

    def test_idempotent_second_run(self, almacenista_user):
        rows = [make_import_row("BD-0001", "Banda Test", "Bandas Import")]
        result1 = import_rows(almacenista_user, rows)
        result2 = import_rows(almacenista_user, rows)
        assert result1.products_created == 1
        assert result2.products_created == 0
        assert result2.products_skipped == 1

    def test_no_stock_created(self, almacenista_user):
        from apps.inventory.models import StockByLocation

        initial = StockByLocation.objects.count()
        rows = [make_import_row("AG-0001", "Aguja Test", "Agujas Import")]
        import_rows(almacenista_user, rows)
        assert StockByLocation.objects.count() == initial

    def test_no_subcategory_assigned(self, almacenista_user):
        from apps.catalog.models import Product

        rows = [make_import_row("PL-0001", "Pelota Test", "Pelotas Import")]
        import_rows(almacenista_user, rows)
        product = Product.objects.get(sku="PL-0001")
        assert product.subcategory is None

    def test_dry_run_makes_no_db_changes(self, almacenista_user):
        from apps.catalog.models import Category, Product

        cat_count_before = Category.objects.count()
        prod_count_before = Product.objects.count()

        rows = [make_import_row("DR-0001", "Dry Run Test", "Dry Run Category")]
        result = import_rows(almacenista_user, rows, dry_run=True)

        assert result.products_created == 1
        assert Category.objects.count() == cat_count_before
        assert Product.objects.count() == prod_count_before

    def test_error_in_one_row_does_not_cancel_others(self, almacenista_user):
        from apps.catalog.models import Product

        rows = [
            make_import_row("OK-0001", "Producto Válido A", "Multi Error Test"),
            # SKU demasiado largo → causará error en create_product
            make_import_row("TOOLONG-99999", "Producto Inválido", "Multi Error Test"),
            make_import_row("OK-0002", "Producto Válido B", "Multi Error Test"),
        ]
        result = import_rows(almacenista_user, rows)
        assert result.products_created == 2
        assert len(result.errors) == 1
        assert Product.objects.filter(sku="OK-0001").exists()
        assert Product.objects.filter(sku="OK-0002").exists()
        assert not Product.objects.filter(sku="TOOLONG-99999").exists()

    def test_categories_shared_across_products(self, almacenista_user):
        rows = [
            make_import_row("SA-0001", "Producto A", "Shared Cat"),
            make_import_row("SA-0002", "Producto B", "Shared Cat"),
            make_import_row("SA-0003", "Producto C", "Shared Cat"),
        ]
        result = import_rows(almacenista_user, rows)
        assert result.categories_created == 1
        assert result.products_created == 3

    def test_generated_sku_tracked_in_result(self, almacenista_user):
        rows = [
            make_import_row(
                "FL-0032",
                "Flexbar Amarillo",
                "Terapias Import",
                generated=True,
                original_sku="S/C",
            )
        ]
        result = import_rows(almacenista_user, rows)
        assert "FL-0032" in result.products_generated_sku

    def test_transformed_sku_tracked_in_result(self, almacenista_user):
        rows = [
            make_import_row(
                "MPCA-01",
                "Masajeador Talla L",
                "Masajeadores Import",
                transformed=True,
                original_sku="MPC-01A",
            )
        ]
        result = import_rows(almacenista_user, rows)
        assert ("MPC-01A", "MPCA-01") in result.products_transformed_sku

    def test_products_have_is_active_true(self, almacenista_user):
        from apps.catalog.models import Product

        rows = [make_import_row("AC-0001", "Producto Activo Test", "Activos Import")]
        import_rows(almacenista_user, rows)
        product = Product.objects.get(sku="AC-0001")
        assert product.is_active is True
