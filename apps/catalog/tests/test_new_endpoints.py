"""Tests para los nuevos endpoints REST del catálogo: detalle, PATCH, PUT, soft delete y restore."""

from __future__ import annotations

import pytest
from django.utils import timezone

from apps.audit.models import AuditEventType, AuditLog
from apps.catalog.models import Brand, Category, ComboItem, Product, ProductCombo
from apps.catalog.services import (
    create_brand,
    create_category,
    create_combo,
    disable_brand_for_assignment,
    disable_category_for_assignment,
    enable_brand_for_assignment,
    enable_category_for_assignment,
    soft_delete_brand,
    soft_delete_category,
)
from tests.factories import BrandFactory, CategoryFactory, ProductFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_brand(name: str = "Marca A") -> Brand:
    return Brand.objects.create(
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
        resp = authenticated_almacenista_client.get(
            f"/api/v1/catalog/categories/{cat.id}/"
        )
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
        assert cat.deleted_at is not None

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
        assert "producto" in resp.data["message"].lower()

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
        cat = CategoryFactory()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/categories/{cat.id}/")
        cat.refresh_from_db()
        assert cat.deleted_at is not None
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/categories/{cat.id}/restore/"
        )
        assert resp.status_code == 200
        cat.refresh_from_db()
        assert cat.deleted_at is None

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

    # -- Status filter tests ------------------------------------------------

    @pytest.mark.django_db
    def test_list_status_deleted(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/categories/{cat.id}/")
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/categories/?status=deleted"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(cat.id) in ids

    @pytest.mark.django_db
    def test_list_status_deleted_excludes_active(
        self, authenticated_almacenista_client
    ):
        active = CategoryFactory(name="Activa")
        cat = CategoryFactory()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/categories/{cat.id}/")
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/categories/?status=deleted"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(cat.id) in ids
        assert str(active.id) not in ids

    @pytest.mark.django_db
    def test_list_status_inactive(self, authenticated_almacenista_client):
        inactive = CategoryFactory(name="Inactiva", is_active=False)
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/categories/?status=inactive"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(inactive.id) in ids

    @pytest.mark.django_db
    def test_list_status_all_includes_deleted(self, authenticated_almacenista_client):
        active = CategoryFactory(name="Activa")
        inactive = CategoryFactory(name="Inactiva", is_active=False)
        cat = CategoryFactory()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/categories/{cat.id}/")
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/categories/?status=all"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) in ids
        assert str(cat.id) in ids

    # -- Disable / Enable for assignment ------------------------------------

    @pytest.mark.django_db
    def test_disable_category_for_assignment(self, authenticated_almacenista_client):
        cat = CategoryFactory()
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/categories/{cat.id}/disable/"
        )
        assert resp.status_code == 200
        assert resp.data["is_active"] is False
        cat.refresh_from_db()
        assert cat.is_active is False
        assert cat.deleted_at is None

    @pytest.mark.django_db
    def test_enable_category_for_assignment(self, authenticated_almacenista_client):
        cat = CategoryFactory(is_active=False)
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/categories/{cat.id}/enable/"
        )
        assert resp.status_code == 200
        assert resp.data["is_active"] is True
        cat.refresh_from_db()
        assert cat.is_active is True

    @pytest.mark.django_db
    def test_disable_deleted_category_returns_409(
        self, authenticated_almacenista_client
    ):
        cat = CategoryFactory()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/categories/{cat.id}/")
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/categories/{cat.id}/disable/"
        )
        assert resp.status_code == 409

    @pytest.mark.django_db
    def test_enable_deleted_category_returns_409(
        self, authenticated_almacenista_client
    ):
        cat = CategoryFactory()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/categories/{cat.id}/")
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/categories/{cat.id}/enable/"
        )
        assert resp.status_code == 409


# ===========================================================================
# BRAND — GET detail, PUT, PATCH, DELETE, restore, include_inactive
# ===========================================================================


class TestBrandDetail:
    @pytest.mark.django_db
    def test_get_detail_returns_200(self, authenticated_almacenista_client):
        brand = _make_brand("Marca Test")
        resp = authenticated_almacenista_client.get(
            f"/api/v1/catalog/brands/{brand.id}/"
        )
        assert resp.status_code == 200
        assert resp.data["id"] == str(brand.id)
        assert resp.data["name"] == "Marca Test"
        assert "is_active" in resp.data

    @pytest.mark.django_db
    def test_patch_updates_name(self, authenticated_almacenista_client):
        brand = _make_brand("Original")
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/brands/{brand.id}/",
            {"name": "Actualizada"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Actualizada"
        brand.refresh_from_db()
        assert brand.name == "Actualizada"

    @pytest.mark.django_db
    def test_put_updates_brand(self, authenticated_almacenista_client):
        brand = _make_brand("Vieja")
        resp = authenticated_almacenista_client.put(
            f"/api/v1/catalog/brands/{brand.id}/",
            {"name": "Nueva"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Nueva"

    @pytest.mark.django_db
    def test_delete_soft_deletes(self, authenticated_almacenista_client):
        brand = _make_brand()
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/brands/{brand.id}/"
        )
        assert resp.status_code == 204
        brand.refresh_from_db()
        assert brand.deleted_at is not None

    @pytest.mark.django_db
    def test_delete_with_active_products_returns_409(
        self, authenticated_almacenista_client
    ):
        brand = _make_brand()
        ProductFactory(brand=brand, is_active=True)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/brands/{brand.id}/"
        )
        assert resp.status_code == 409

    @pytest.mark.django_db
    def test_restore_reactivates(self, authenticated_almacenista_client):
        brand = _make_brand()
        authenticated_almacenista_client.delete(f"/api/v1/catalog/brands/{brand.id}/")
        brand.refresh_from_db()
        assert brand.deleted_at is not None
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/brands/{brand.id}/restore/"
        )
        assert resp.status_code == 200
        brand.refresh_from_db()
        assert brand.deleted_at is None

    @pytest.mark.django_db
    def test_list_excludes_inactive_by_default(self, authenticated_almacenista_client):
        active = _make_brand("Marca Activa")
        inactive = _make_brand("Marca Inactiva")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get("/api/v1/catalog/brands/")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.data["results"]]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    @pytest.mark.django_db
    def test_list_includes_inactive_with_param(self, authenticated_almacenista_client):
        inactive = _make_brand("Marca Inactiva 2")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/brands/?include_inactive=true"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.data["results"]]
        assert str(inactive.id) in ids

    # -- Status filter tests ------------------------------------------------

    @pytest.mark.django_db
    def test_list_brand_status_deleted(self, authenticated_almacenista_client):
        brand = _make_brand("Marca a eliminar")
        authenticated_almacenista_client.delete(f"/api/v1/catalog/brands/{brand.id}/")
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/brands/?status=deleted"
        )
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.data["results"]]
        assert str(brand.id) in ids

    @pytest.mark.django_db
    def test_list_brand_status_inactive(self, authenticated_almacenista_client):
        inactive = _make_brand("Marca Inactiva 3")
        inactive.is_active = False
        inactive.save()
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/brands/?status=inactive"
        )
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.data["results"]]
        assert str(inactive.id) in ids

    @pytest.mark.django_db
    def test_list_brand_status_all(self, authenticated_almacenista_client):
        active = _make_brand("Marca Activa All")
        brand = _make_brand("Marca a borrar")
        authenticated_almacenista_client.delete(f"/api/v1/catalog/brands/{brand.id}/")
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/brands/?status=all"
        )
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.data["results"]]
        assert str(active.id) in ids
        assert str(brand.id) in ids

    # -- Disable / Enable for assignment ------------------------------------

    @pytest.mark.django_db
    def test_delete_soft_deletes_combo(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = _make_combo("KIT-0005", sample_product)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/combos/{combo.id}/"
        )
        assert resp.status_code == 204
        combo.refresh_from_db()
        assert combo.deleted_at is not None

    @pytest.mark.django_db
    def test_combo_restore_reactivates(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = _make_combo("KIT-0006", sample_product)
        combo.deleted_at = timezone.now()
        combo.save()
        resp = authenticated_almacenista_client.post(
            f"/api/v1/catalog/combos/{combo.id}/restore/"
        )
        assert resp.status_code == 200
        combo.refresh_from_db()
        assert combo.deleted_at is None

    @pytest.mark.django_db
    def test_list_excludes_deleted_by_default(
        self, authenticated_almacenista_client, sample_product
    ):
        active = _make_combo("KIT-0007", sample_product, "Activo")
        deleted = _make_combo("KIT-0008", sample_product, "Eliminado")
        deleted.deleted_at = timezone.now()
        deleted.save()
        resp = authenticated_almacenista_client.get("/api/v1/catalog/combos/")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(active.id) in ids
        assert str(deleted.id) not in ids

    @pytest.mark.django_db
    def test_list_excludes_deleted_always(
        self, authenticated_almacenista_client, sample_product
    ):
        """Combos eliminados nunca aparecen en listados (no hay include_deleted)."""
        active = _make_combo("KIT-0009", sample_product, "Activo")
        deleted = _make_combo("KIT-0010", sample_product, "Eliminado")
        deleted.deleted_at = timezone.now()
        deleted.save()

        # Sin parámetros: no incluye eliminados
        resp = authenticated_almacenista_client.get("/api/v1/catalog/combos/")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(active.id) in ids
        assert str(deleted.id) not in ids

        # Con include_deleted=true: tampoco incluye eliminados (no soportado)
        resp = authenticated_almacenista_client.get(
            "/api/v1/catalog/combos/?include_deleted=true"
        )
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.data["results"]]
        assert str(active.id) in ids
        assert str(deleted.id) not in ids


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


# ===========================================================================
# PRODUCT — guard: no desactivar si pertenece a combo activo
# ===========================================================================


class TestProductDeactivateComboGuard:
    @pytest.mark.django_db
    def test_delete_returns_409_when_in_active_combo(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = ProductCombo.objects.create(name="Kit Test", sku="KIT-G001")
        ComboItem.objects.create(combo=combo, product=sample_product, quantity=1)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/products/{sample_product.id}/"
        )
        assert resp.status_code == 409
        assert "combo" in resp.data["message"].lower()
        sample_product.refresh_from_db()
        assert sample_product.deleted_at is None

    @pytest.mark.django_db
    def test_delete_succeeds_when_only_in_deleted_combo(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = ProductCombo.objects.create(name="Kit Eliminado", sku="KIT-G002")
        combo.deleted_at = timezone.now()
        combo.save()
        ComboItem.objects.create(combo=combo, product=sample_product, quantity=1)
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/products/{sample_product.id}/"
        )
        assert resp.status_code == 204
        sample_product.refresh_from_db()
        assert sample_product.deleted_at is not None

    @pytest.mark.django_db
    def test_delete_succeeds_when_not_in_any_combo(
        self, authenticated_almacenista_client, sample_product
    ):
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/products/{sample_product.id}/"
        )
        assert resp.status_code == 204
        sample_product.refresh_from_db()
        assert sample_product.deleted_at is not None

    @pytest.mark.django_db
    def test_soft_delete_logs_product_soft_deleted_event(
        self, authenticated_almacenista_client, sample_product
    ):
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/products/{sample_product.id}/"
        )
        assert resp.status_code == 204
        log = AuditLog.objects.filter(
            event_type=AuditEventType.PRODUCT_SOFT_DELETED
        ).first()
        assert log is not None
        assert sample_product.sku in log.description


# ===========================================================================
# COMBO — deleted_at ignorado en PUT/PATCH; solo cambia vía DELETE/restore
# ===========================================================================


class TestComboUpdateDeletedAtIgnored:
    @pytest.mark.django_db
    def test_patch_with_deleted_at_does_not_deactivate_combo(
        self, authenticated_almacenista_client, sample_product
    ):
        """deleted_at no es un campo editable vía PATCH; debe ser ignorado."""
        combo = _make_combo("KIT-A001", sample_product, "Kit Active Test")
        assert combo.deleted_at is None
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/combos/{combo.id}/",
            {"deleted_at": "2024-01-01T00:00:00Z"},
            format="json",
        )
        assert resp.status_code == 200
        combo.refresh_from_db()
        assert combo.deleted_at is None

    @pytest.mark.django_db
    def test_patch_with_deleted_at_does_not_log_combo_soft_deleted(
        self, authenticated_almacenista_client, sample_product
    ):
        """Audit event COMBO_SOFT_DELETED solo debe existir vía DELETE, nunca vía PATCH."""
        combo = _make_combo("KIT-A002", sample_product, "Kit Audit Check")
        authenticated_almacenista_client.patch(
            f"/api/v1/catalog/combos/{combo.id}/",
            {"deleted_at": "2024-01-01T00:00:00Z"},
            format="json",
        )
        assert not AuditLog.objects.filter(
            event_type=AuditEventType.COMBO_SOFT_DELETED
        ).exists()

    @pytest.mark.django_db
    def test_soft_delete_via_delete_logs_combo_soft_deleted(
        self, authenticated_almacenista_client, sample_product
    ):
        combo = _make_combo("KIT-A003", sample_product, "Kit Audit Test")
        resp = authenticated_almacenista_client.delete(
            f"/api/v1/catalog/combos/{combo.id}/"
        )
        assert resp.status_code == 204
        log = AuditLog.objects.filter(
            event_type=AuditEventType.COMBO_SOFT_DELETED
        ).first()
        assert log is not None
        assert combo.sku in log.description

    @pytest.mark.django_db
    def test_patch_name_still_works_when_deleted_at_sent(
        self, authenticated_almacenista_client, sample_product
    ):
        """Otros campos sí se actualizan aunque venga deleted_at en el payload."""
        combo = _make_combo("KIT-A004", sample_product, "Nombre Viejo")
        resp = authenticated_almacenista_client.patch(
            f"/api/v1/catalog/combos/{combo.id}/",
            {"name": "Nombre Nuevo", "deleted_at": "2024-01-01T00:00:00Z"},
            format="json",
        )
        assert resp.status_code == 200
        combo.refresh_from_db()
        assert combo.name == "Nombre Nuevo"
        assert combo.deleted_at is None
