"""Tests para los nuevos endpoints REST del catálogo: detalle, PATCH, PUT, soft delete y restore."""

from __future__ import annotations

import pytest

from apps.catalog.models import Category, ComboItem, Product, ProductCombo, Subcategory
from apps.catalog.services import create_category, create_combo, create_subcategory
from tests.factories import CategoryFactory, ProductFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_subcategory(category: Category, name: str = "Sub A") -> Subcategory:
    return Subcategory.objects.create(
        category=category,
        name=name,
        slug=name.lower().replace(" ", "-"),
    )


def _make_combo(sku: str, product: Product, name: str = "Kit A") -> ProductCombo:
    combo = ProductCombo.objects.create(name=name, sku=sku)
    ComboItem.objects.create(combo=combo, product=product, quantity=1)
    return combo


# ===========================================================================
# CATEGORY — GET detail, PUT, PATCH, DELETE, restore, include_inactive
# ===========================================================================


class TestCategoryDetail:
    @pytest.mark.django_db
    def test_get_detail_returns_200(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        resp = authenticated_almacenista_client.get(f"/api/v1/catalog/categories/{cat.id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == str(cat.id)
        assert resp.data["name"] == cat.name
        assert "is_active" in resp.data

    @pytest.mark.django_db
    def test_get_detail_404_on_missing(self, authenticated_almacenista_client):
        import uuid
        resp = authenticated_almacenista_client.get(
            f"/api/v1/catalog/categories/{uuid.uuid4()}/"
        )
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_patch_updates_name(self, authenticated_almacenista_client):
        cat = CategoryFactory(name="Original")
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/categories/{cat.id}/",
            {"name": "Actualizada"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Actualizada"
        cat.refresh_from_db()
        assert cat.name == "Actualizada"

    @pytest.mark.django_db
    def test_patch_updates_flags(self, authenticated_almacenista_client):
        cat = CategoryFactory(requires_serial_number=False, is_returnable=False)
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/categories/{cat.id}/",
            {"requires_serial_number": True, "is_returnable": True},
            format="json",
        )
        assert resp.status_code == 200
        cat.refresh_from_db()
        assert cat.requires_serial_number is True
        assert cat.is_returnable is True

    @pytest.mark.django_db
    def test_put_replaces_category(self, authenticated_almacenista_client):
        cat = CategoryFactory(name="Vieja", description="desc vieja")
        resp = authenticated_almacenista_client.put(
            f"/api/v1/catalog/categories/{cat.id}/",
            {"name": "Nueva", "description": "nueva desc"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Nueva"
        assert resp.data["description"] == "nueva desc"

    @pytest.mark.django_db
    def test_delete_soft_deletes_category(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/categories/{cat.id}/"
        )
        assert resp.status_code == 204
        cat.refresh_from_db()
        assert cat.is_active is False

    @pytest.mark.django_db
    def test_delete_category_with_active_products_returns_409(
        self, authenticated_almacenista_client
    ):
        cat = CategoryFactory()
        ProductFactory(category=cat, is_active=True)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/categories/{cat.id}/"
        )
        assert resp.status_code == 409
        assert "producto" in resp.data["detail"].lower()

    @pytest.mark.django_db
    def test_delete_category_with_only_inactive_products_succeeds(
        self, authenticated_almacenista_client
    ):
        cat = CategoryFactory()
        ProductFactory(category=cat, is_active=False)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/categories/{cat.id}/"
        )
        assert resp.status_code == 204

    @pytest.mark.django_db
    def test_restore_category_reactivates(self, authenticated_almacenista_client):
        cat = CategoryFactory(is_active=False)
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/categories/{cat.id}/restore/"
        )
        assert resp.status_code == 200
        assert resp.data["is_active"] is True
        cat.refresh_from_db()
        assert cat.is_active is True

    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(self, authenticated_almacenista_client):
        active = CategoryFactory(name="Activa")
        inactive = CategoryFactory(name="Inactiva", is_active=False)
        resp = authenticated_almacenista_client.get("/api/v1/catalog/categories/")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(self, authenticated_almacenista_client):
        inactive = CategoryFactory(is_active=False)
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/categories/?include_inactive=true"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(inactive.id) in ids

    @pytest.mark.django_db
    def test_patch_requires_almacenista(self, authenticated_administrador_client):
        cat = CategoryFactory()
        resp = authenticated_administrador_client.patch(
            f"/api/v1/catalog/categories/{cat.id}/",
            {"name": "X"},
            format="json",
        )
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_delete_requires_almacenista(self, authenticated_administrador_client):
        cat = CategoryFactory()
        resp = authenticated_administrador_client.delete(
            f"/api/v1/catalog/categories/{cat.id}/"
        )
        assert resp.status_code == 403


# ===========================================================================
# SUBCATEGORY — GET detail, PUT, PATCH, DELETE, restore, include_inactive
# ===========================================================================


class TestSubcategoryDetail:
    @pytest.mark.django_db
    def test_get_detail_returns_200(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        sub = _make_subcategory(cat, "Sub Test")
        resp = authenticated_almacenista_client.get(
            f"/api/v1/catalog/subcategories/{sub.id}/"
        )
        assert resp.status_code == 200
        assert resp.data["id"] == str(sub.id)
        assert resp.data["name"] == "Sub Test"
        assert "is_active" in resp.data

    @pytest.mark.django_db
    def test_patch_updates_name(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        sub = _make_subcategory(cat, "Original")
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/subcategories/{sub.id}/",
            {"name": "Actualizada"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Actualizada"
        sub.refresh_from_db()
        assert sub.name == "Actualizada"

    @pytest.mark.django_db
    def test_put_updates_subcategory(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        sub = _make_subcategory(cat, "Vieja")
        resp = authenticated_almacenista_client.put(
            f"/api/v1/catalog/subcategories/{sub.id}/",
            {"name": "Nueva"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Nueva"

    @pytest.mark.django_db
    def test_delete_soft_deletes(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        sub = _make_subcategory(cat)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/subcategories/{sub.id}/"
        )
        assert resp.status_code == 204
        sub.refresh_from_db()
        assert sub.is_active is False

    @pytest.mark.django_db
    def test_delete_with_active_products_returns_409(
        self, authenticated_almacenista_client
    ):
        cat = CategoryFactory()
        sub = _make_subcategory(cat)
        ProductFactory(category=cat, subcategory=sub, is_active=True)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/subcategories/{sub.id}/"
        )
        assert resp.status_code == 409

    @pytest.mark.django_db
    def test_restore_reactivates(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        sub = _make_subcategory(cat)
        sub.is_active = False
        sub.save()
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/subcategories/{sub.id}/restore/"
        )
        assert resp.status_code == 200
        assert resp.data["is_active"] is True
        sub.refresh_from_db()
        assert sub.is_active is True

    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        active = _make_subcategory(cat, "Sub Activa")
        inactive = _make_subcategory(cat, "Sub Inactiva")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get("/api/v1/catalog/subcategories/")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        inactive = _make_subcategory(cat, "Sub Inactiva 2")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/subcategories/?include_inactive=true"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.data["results"]]
        assert str(inactive.id) in ids


# ===========================================================================
# COMBO — GET detail, PUT, PATCH, DELETE, restore, include_inactive
# ===========================================================================


class TestComboDetail:
    @pytest.mark.django_db
    def test_get_detail_returns_200(self, authenticated_almacenista_client, sample_product):
        combo = _make_combo("KIT-0001", sample_product)
        resp = authenticated_almacenista_client.get(
            f"/api/v1/catalog/combos/{combo.id}/"
        )
        assert resp.status_code == 200
        assert resp.data["id"] == str(combo.id)
        assert resp.data["sku"] == "KIT-0001"
        assert len(resp.data["components"]) == 1

    @pytest.mark.django_db
    def test_patch_updates_name(self, authenticated_almacenista_client, sample_product):
        combo = _make_combo("KIT-0002", sample_product, "Kit Original")
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/combos/{combo.id}/",
            {"name": "Kit Actualizado"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Kit Actualizado"
        combo.refresh_from_db()
        assert combo.name == "Kit Actualizado"

    @pytest.mark.django_db
    def test_patch_with_items_replaces_all_items(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = _make_combo("KIT-0003", sample_product)
        new_product = ProductFactory()
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/combos/{combo.id}/",
            {"items": [{"product_id": str(new_product.id), "quantity": 3}]},
            format="json",
        )
        assert resp.status_code == 200
        combo.refresh_from_db()
        items = list(combo.combo_items.all())
        assert len(items) == 1
        assert items[0].product_id == new_product.id
        assert items[0].quantity == 3

    @pytest.mark.django_db
    def test_put_replaces_combo(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = _make_combo("KIT-0004", sample_product, "Kit Viejo")
        new_product = ProductFactory()
        resp = authenticated_almacenista_client.put(
            f"/api/v1/catalog/combos/{combo.id}/",
            {
                "name": "Kit Nuevo",
                "items": [{"product_id": str(new_product.id), "quantity": 2}],
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Kit Nuevo"

    @pytest.mark.django_db
    def test_delete_soft_deletes(self, authenticated_almacenista_client, sample_product):
        combo = _make_combo("KIT-0005", sample_product)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/combos/{combo.id}/"
        )
        assert resp.status_code == 204
        combo.refresh_from_db()
        assert combo.is_active is False

    @pytest.mark.django_db
    def test_restore_reactivates(self, authenticated_almacenista_client, sample_product):
        combo = _make_combo("KIT-0006", sample_product)
        combo.is_active = False
        combo.save()
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/combos/{combo.id}/restore/"
        )
        assert resp.status_code == 200
        assert resp.data["is_active"] is True
        combo.refresh_from_db()
        assert combo.is_active is True

    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(
        self, authenticated_almacenista_client, sample_product
    ):
        active = _make_combo("KIT-0007", sample_product, "Activo")
        inactive = _make_combo("KIT-0008", sample_product, "Inactivo")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get("/api/v1/catalog/combos/")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(
        self, authenticated_almacenista_client, sample_product
    ):
        inactive = _make_combo("KIT-0009", sample_product, "Inactivo 2")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/combos/?include_inactive=true"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(inactive.id) in ids


# ===========================================================================
# PRODUCT — DELETE (soft), restore, include_inactive
# ===========================================================================


class TestProductSoftDeleteAndRestore:
    @pytest.mark.django_db
    def test_delete_deactivates_product(
        self, authenticated_almacenista_client, sample_product
    ):
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/products/{sample_product.id}/"
        )
        assert resp.status_code == 204
        sample_product.refresh_from_db()
        assert sample_product.is_active is False

    @pytest.mark.django_db
    def test_restore_reactivates_product(
        self, authenticated_almacenista_client, sample_product
    ):
        sample_product.is_active = False
        sample_product.save()
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/products/{sample_product.id}/restore/"
        )
        assert resp.status_code == 200
        assert resp.data["is_active"] is True
        sample_product.refresh_from_db()
        assert sample_product.is_active is True

    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(self, authenticated_almacenista_client):
        active = ProductFactory(is_active=True)
        inactive = ProductFactory(is_active=False)
        resp = authenticated_almacenista_client.get("/api/v1/catalog/products/")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(self, authenticated_almacenista_client):
        inactive = ProductFactory(is_active=False)
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/products/?include_inactive=true"
        )
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.data["results"]]
        assert str(inactive.id) in ids

    @pytest.mark.django_db
    def test_delete_requires_almacenista(
        self, authenticated_administrador_client, sample_product
    ):
        resp = authenticated_administrador_client.delete(
            f"/api/v1/catalog/products/{sample_product.id}/"
        )
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_restore_requires_almacenista(
        self, authenticated_administrador_client, sample_product
    ):
        sample_product.is_active = False
        sample_product.save()
        resp = authenticated_administrador_client.post(
            f"/api/v1/catalog/products/{sample_product.id}/restore/"
        )
        assert resp.status_code == 403
