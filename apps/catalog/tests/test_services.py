import pytest

from apps.audit.models import AuditEventType, AuditLog
from apps.catalog.models import Brand, Category
from apps.catalog.serializers import ProductDetailSerializer
from apps.catalog.services import (
    create_combo,
    create_product,
    disable_brand_for_assignment,
    disable_category_for_assignment,
    enable_brand_for_assignment,
    enable_category_for_assignment,
    resolve_identifier,
    restore_brand,
    restore_category,
    soft_delete_brand,
    soft_delete_category,
    update_combo,
    update_product,
)
from shared.exceptions import DomainValidationError
from shared.utils.barcode import build_product_barcode
from tests.factories import BrandFactory, CategoryFactory, ProductFactory


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


@pytest.mark.django_db
def test_create_product_duplicate_sku_raises_domain_error(almacenista_user):
    from tests.factories import CategoryFactory, ProductFactory

    category = CategoryFactory()
    ProductFactory(sku="DUP-0001", category=category)
    with pytest.raises(DomainValidationError) as exc_info:
        create_product(
            almacenista_user,
            {
                "sku": "DUP-0001",
                "name": "Producto duplicado",
                "category_id": category.id,
            },
        )
    assert "DUP-0001" in str(exc_info.value)
    assert "ya existe" in str(exc_info.value)


@pytest.mark.django_db
def test_create_combo_duplicate_sku_raises_domain_error(almacenista_user):
    from tests.factories import CategoryFactory

    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {"sku": "PROD-001", "name": "Producto base", "category_id": category.id},
    )
    create_combo(
        almacenista_user,
        {
            "sku": "CMB-001",
            "name": "Combo original",
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    with pytest.raises(DomainValidationError) as exc_info:
        create_combo(
            almacenista_user,
            {
                "sku": "CMB-001",
                "name": "Combo duplicado",
                "items": [{"product_id": product.id, "quantity": 1}],
            },
        )
    assert "CMB-001" in str(exc_info.value)
    assert "ya existe" in str(exc_info.value)


@pytest.mark.django_db
def test_update_combo_duplicate_sku_raises_domain_error(almacenista_user):
    from tests.factories import CategoryFactory

    category = CategoryFactory()
    product = create_product(
        almacenista_user,
        {"sku": "PROD-002", "name": "Producto base", "category_id": category.id},
    )
    combo_a = create_combo(
        almacenista_user,
        {
            "sku": "CMB-002",
            "name": "Combo A",
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    combo_b = create_combo(
        almacenista_user,
        {
            "sku": "CMB-003",
            "name": "Combo B",
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    with pytest.raises(DomainValidationError) as exc_info:
        update_combo(almacenista_user, combo_b.id, {"sku": "CMB-002"})
    assert "CMB-002" in str(exc_info.value)
    assert "ya existe" in str(exc_info.value)


# ===========================================================================
# CATEGORY — Soft Delete service tests
# ===========================================================================


class TestSoftDeleteCategory:
    @pytest.mark.django_db
    def test_soft_delete_sets_deleted_at(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        cat.refresh_from_db()
        assert cat.deleted_at is not None

    @pytest.mark.django_db
    def test_soft_delete_already_deleted_raises(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        with pytest.raises(ValueError, match="ya está eliminada"):
            soft_delete_category(almacenista_user, cat.id)

    @pytest.mark.django_db
    def test_soft_delete_with_active_products_raises(self, almacenista_user):
        cat = CategoryFactory()
        ProductFactory(category=cat, is_active=True)
        with pytest.raises(ValueError, match="producto.*activo"):
            soft_delete_category(almacenista_user, cat.id)

    @pytest.mark.django_db
    def test_soft_delete_with_inactive_products_succeeds(self, almacenista_user):
        cat = CategoryFactory()
        ProductFactory(category=cat, is_active=False)
        soft_delete_category(almacenista_user, cat.id)
        cat.refresh_from_db()
        assert cat.deleted_at is not None

    @pytest.mark.django_db
    def test_soft_delete_logs_audit(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        log = AuditLog.objects.filter(
            event_type=AuditEventType.CATEGORY_SOFT_DELETED
        ).first()
        assert log is not None
        assert cat.name in log.description


class TestRestoreCategory:
    @pytest.mark.django_db
    def test_restore_clears_deleted_at(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        cat.refresh_from_db()
        assert cat.deleted_at is not None
        restore_category(almacenista_user, cat.id)
        cat.refresh_from_db()
        assert cat.deleted_at is None

    @pytest.mark.django_db
    def test_restore_not_deleted_raises(self, almacenista_user):
        cat = CategoryFactory()
        with pytest.raises(ValueError, match="no está eliminada"):
            restore_category(almacenista_user, cat.id)

    @pytest.mark.django_db
    def test_restore_logs_audit(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        restore_category(almacenista_user, cat.id)
        log = AuditLog.objects.filter(
            event_type=AuditEventType.CATEGORY_RESTORED
        ).first()
        assert log is not None
        assert cat.name in log.description


class TestDisableCategoryForAssignment:
    @pytest.mark.django_db
    def test_disable_sets_is_active_false(self, almacenista_user):
        cat = CategoryFactory()
        disable_category_for_assignment(almacenista_user, cat.id)
        cat.refresh_from_db()
        assert cat.is_active is False
        assert cat.deleted_at is None

    @pytest.mark.django_db
    def test_disable_deleted_category_raises(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        with pytest.raises(ValueError, match="eliminada"):
            disable_category_for_assignment(almacenista_user, cat.id)

    @pytest.mark.django_db
    def test_disable_logs_audit(self, almacenista_user):
        cat = CategoryFactory()
        disable_category_for_assignment(almacenista_user, cat.id)
        log = AuditLog.objects.filter(
            event_type=AuditEventType.CATEGORY_DISABLED
        ).first()
        assert log is not None
        assert cat.name in log.description


class TestEnableCategoryForAssignment:
    @pytest.mark.django_db
    def test_enable_sets_is_active_true(self, almacenista_user):
        cat = CategoryFactory(is_active=False)
        enable_category_for_assignment(almacenista_user, cat.id)
        cat.refresh_from_db()
        assert cat.is_active is True

    @pytest.mark.django_db
    def test_enable_deleted_category_raises(self, almacenista_user):
        cat = CategoryFactory()
        soft_delete_category(almacenista_user, cat.id)
        with pytest.raises(ValueError, match="eliminada"):
            enable_category_for_assignment(almacenista_user, cat.id)

    @pytest.mark.django_db
    def test_enable_logs_audit(self, almacenista_user):
        cat = CategoryFactory(is_active=False)
        enable_category_for_assignment(almacenista_user, cat.id)
        log = AuditLog.objects.filter(
            event_type=AuditEventType.CATEGORY_ENABLED
        ).first()
        assert log is not None
        assert cat.name in log.description


# ===========================================================================
# BRAND — Soft Delete service tests
# ===========================================================================


class TestSoftDeleteBrand:
    @pytest.mark.django_db
    def test_soft_delete_sets_deleted_at(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        brand.refresh_from_db()
        assert brand.deleted_at is not None

    @pytest.mark.django_db
    def test_soft_delete_already_deleted_raises(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        with pytest.raises(ValueError, match="ya está eliminada"):
            soft_delete_brand(almacenista_user, brand.id)

    @pytest.mark.django_db
    def test_soft_delete_with_active_products_raises(self, almacenista_user):
        brand = BrandFactory()
        ProductFactory(brand=brand, is_active=True)
        with pytest.raises(ValueError, match="producto.*activo"):
            soft_delete_brand(almacenista_user, brand.id)

    @pytest.mark.django_db
    def test_soft_delete_with_inactive_products_succeeds(self, almacenista_user):
        brand = BrandFactory()
        ProductFactory(brand=brand, is_active=False)
        soft_delete_brand(almacenista_user, brand.id)
        brand.refresh_from_db()
        assert brand.deleted_at is not None

    @pytest.mark.django_db
    def test_soft_delete_logs_audit(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        log = AuditLog.objects.filter(
            event_type=AuditEventType.BRAND_SOFT_DELETED
        ).first()
        assert log is not None
        assert brand.name in log.description


class TestRestoreBrand:
    @pytest.mark.django_db
    def test_restore_clears_deleted_at(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        brand.refresh_from_db()
        assert brand.deleted_at is not None
        restore_brand(almacenista_user, brand.id)
        brand.refresh_from_db()
        assert brand.deleted_at is None

    @pytest.mark.django_db
    def test_restore_not_deleted_raises(self, almacenista_user):
        brand = BrandFactory()
        with pytest.raises(ValueError, match="no está eliminada"):
            restore_brand(almacenista_user, brand.id)

    @pytest.mark.django_db
    def test_restore_logs_audit(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        restore_brand(almacenista_user, brand.id)
        log = AuditLog.objects.filter(event_type=AuditEventType.BRAND_RESTORED).first()
        assert log is not None
        assert brand.name in log.description


class TestDisableBrandForAssignment:
    @pytest.mark.django_db
    def test_disable_sets_is_active_false(self, almacenista_user):
        brand = BrandFactory()
        disable_brand_for_assignment(almacenista_user, brand.id)
        brand.refresh_from_db()
        assert brand.is_active is False
        assert brand.deleted_at is None

    @pytest.mark.django_db
    def test_disable_deleted_brand_raises(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        with pytest.raises(ValueError, match="eliminada"):
            disable_brand_for_assignment(almacenista_user, brand.id)

    @pytest.mark.django_db
    def test_disable_logs_audit(self, almacenista_user):
        brand = BrandFactory()
        disable_brand_for_assignment(almacenista_user, brand.id)
        log = AuditLog.objects.filter(event_type=AuditEventType.BRAND_DISABLED).first()
        assert log is not None
        assert brand.name in log.description


class TestEnableBrandForAssignment:
    @pytest.mark.django_db
    def test_enable_sets_is_active_true(self, almacenista_user):
        brand = BrandFactory()
        brand.is_active = False
        brand.save()
        enable_brand_for_assignment(almacenista_user, brand.id)
        brand.refresh_from_db()
        assert brand.is_active is True

    @pytest.mark.django_db
    def test_enable_deleted_brand_raises(self, almacenista_user):
        brand = BrandFactory()
        soft_delete_brand(almacenista_user, brand.id)
        with pytest.raises(ValueError, match="eliminada"):
            enable_brand_for_assignment(almacenista_user, brand.id)

    @pytest.mark.django_db
    def test_enable_logs_audit(self, almacenista_user):
        brand = BrandFactory()
        brand.is_active = False
        brand.save()
        enable_brand_for_assignment(almacenista_user, brand.id)
        log = AuditLog.objects.filter(event_type=AuditEventType.BRAND_ENABLED).first()
        assert log is not None
        assert brand.name in log.description
