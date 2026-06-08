"""
Tests cortos para scripts/seed_db/ — config (sin BD) e integración (seed + clean).

Tiempo esperado: ~30-60 s (la integración siembra movimientos reales).
Para saltar la integración: pytest -m "not slow"
"""

from __future__ import annotations

import re

import pytest

_SKU_RE = re.compile(r"^[A-Za-z]{1,4}-\d{1,4}$")
_QUIET = lambda _: None  # noqa: E731


def _ensure_base_locations() -> None:
    """Garantiza que existan las ubicaciones base que el seed espera."""

    from apps.inventory.models import Location, StorageType

    bodega_type, _ = StorageType.objects.get_or_create(
        code="bodega",
        defaults={
            "name": "Bodega",
            "category": "warehouse",
            "description": "Almacenamiento general de bodega.",
            "capabilities": {},
            "default_is_retail": False,
            "is_system": True,
            "is_active": True,
            "sort_order": 10,
        },
    )
    vitrina_type, _ = StorageType.objects.get_or_create(
        code="vitrina",
        defaults={
            "name": "Vitrina",
            "category": "retail",
            "description": "Punto de exhibición y venta minorista.",
            "capabilities": {},
            "default_is_retail": True,
            "is_system": True,
            "is_active": True,
            "sort_order": 20,
        },
    )

    base_locations = [
        {
            "code": "bodega",
            "name": "Bodega",
            "description": "Almacén principal de mercancía.",
            "is_retail": False,
            "max_capacity": None,
            "storage_type": bodega_type,
        },
        {
            "code": "vitrina",
            "name": "Vitrina",
            "description": "Punto de venta y exhibición principal.",
            "is_retail": True,
            "max_capacity": 100,
            "storage_type": vitrina_type,
        },
    ]

    for data in base_locations:
        loc, created = Location.objects.get_or_create(
            code=data["code"],
            defaults=data,
        )
        changed = created
        for field in ("name", "description", "is_retail", "max_capacity"):
            if getattr(loc, field) != data[field]:
                setattr(loc, field, data[field])
                changed = True
        if loc.storage_type_id != data["storage_type"].id:
            loc.storage_type = data["storage_type"]
            changed = True
        if changed:
            loc.save()


# ── Config (sin BD, muy rápido) ────────────────────────────────────────────


class TestSeedConfig:
    """Valida la integridad estática de scripts/seed_db/config.py."""

    @pytest.fixture(autouse=True)
    def _config(self):
        from scripts.seed_db import config

        self.cfg = config

    def test_no_duplicate_product_skus(self):
        skus = [p["sku"] for p in self.cfg.PRODUCTS]
        dupes = {s for s in skus if skus.count(s) > 1}
        assert not dupes, f"SKUs duplicados: {dupes}"

    def test_all_product_skus_valid_format(self):
        invalid = [p["sku"] for p in self.cfg.PRODUCTS if not _SKU_RE.match(p["sku"])]
        assert not invalid, f"SKUs con formato inválido: {invalid}"

    def test_all_category_slugs_declared(self):
        cat_slugs = {c["slug"] for c in self.cfg.CATEGORIES}
        missing = {
            p["sku"]: p["category_slug"]
            for p in self.cfg.PRODUCTS
            if p["category_slug"] not in cat_slugs
        }
        assert not missing, f"category_slug no declarado: {missing}"

    def test_combo_items_reference_known_skus(self):
        product_skus = {p["sku"] for p in self.cfg.PRODUCTS}
        bad = {
            combo["sku"]: sku
            for combo in self.cfg.COMBOS
            for sku, _ in combo["items"]
            if sku not in product_skus
        }
        assert not bad, f"Combos con SKU inexistente: {bad}"

    def test_electroterapia_requires_serial(self):
        electro = next(c for c in self.cfg.CATEGORIES if c["slug"] == "electroterapia")
        assert electro["requires_serial_number"] is True

    def test_expiration_products_have_valid_skus(self):
        exp_products = [p for p in self.cfg.PRODUCTS if p.get("requires_expiration")]
        assert exp_products, "Debe haber al menos un producto con requires_expiration=True"
        invalid = [p["sku"] for p in exp_products if not _SKU_RE.match(p["sku"])]
        assert not invalid


# ── Integración (requiere BD) ──────────────────────────────────────────────


@pytest.mark.slow
@pytest.mark.django_db(transaction=True)
class TestSeedIntegration:
    """Verifica que el seeder y el cleaner funcionan end-to-end sobre BD real."""

    @pytest.fixture(autouse=True)
    def _setup_base_locations(self):
        _ensure_base_locations()

    def test_seed_creates_catalog_and_movements(self, almacenista_user):
        from apps.catalog.models import Category, Product
        from apps.movements.models import Movement
        from apps.purchasing.models import PurchaseOrder
        from scripts.seed_db.seeder import Seeder

        result = Seeder(write_fn=_QUIET, warn_fn=_QUIET).run(force=False)

        assert result.categories_created == 11
        assert result.products_created == 214
        assert Category.objects.count() == 11
        assert Product.objects.count() == 214
        assert PurchaseOrder.objects.filter(status="completada").exists()
        assert Movement.objects.count() > 0
        assert not result.skipped_movement_phase

    def test_seed_is_idempotent(self, almacenista_user):
        from apps.catalog.models import Product
        from apps.movements.models import Movement
        from scripts.seed_db.seeder import Seeder

        Seeder(write_fn=_QUIET, warn_fn=_QUIET).run(force=False)
        first_products = Product.objects.count()
        first_movements = Movement.objects.count()

        result2 = Seeder(write_fn=_QUIET, warn_fn=_QUIET).run(force=False)

        assert Product.objects.count() == first_products
        assert Movement.objects.count() == first_movements
        assert result2.skipped_movement_phase

    def test_clean_removes_seed_data_preserves_base(self, almacenista_user):
        from django.contrib.auth import get_user_model

        from apps.catalog.models import Category, Product
        from apps.inventory.models import Location
        from apps.movements.models import Movement
        from scripts.seed_db.clean import clean
        from scripts.seed_db.seeder import Seeder

        Seeder(write_fn=_QUIET, warn_fn=_QUIET).run(force=False)
        assert Product.objects.exists()
        assert Movement.objects.exists()

        clean()

        assert not Product.objects.exists()
        assert not Category.objects.exists()
        assert not Movement.objects.exists()
        # Ubicaciones base conservadas
        assert Location.objects.filter(code="bodega").exists()
        assert Location.objects.filter(code="vitrina").exists()
        # Usuario almacenista conservado
        User = get_user_model()
        assert User.objects.filter(username=almacenista_user.username).exists()
