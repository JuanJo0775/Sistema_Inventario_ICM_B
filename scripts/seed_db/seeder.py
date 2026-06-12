"""
Logica principal del seed ICM — catalogo + movimientos.

Uso directo:
    from scripts.seed_db.seeder import Seeder
    result = Seeder().run(force=True)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable

from django.db import transaction

from scripts.seed_db import config

logger = logging.getLogger(__name__)


@dataclass
class SeedResult:
    categories_created: int = 0
    categories_skipped: int = 0
    subcategories_created: int = 0
    products_created: int = 0
    products_skipped: int = 0
    purchase_orders: int = 0
    movements: int = 0
    stock_rows: int = 0
    movements_by_type: dict[str, int] = field(default_factory=dict)
    stock_by_location: dict[str, dict] = field(default_factory=dict)
    skipped_movement_phase: bool = False


class Seeder:
    """
    Seed unificado: crea el catalogo completo (categorias, marcas, productos)
    y luego siembra movimientos realistas usando exclusivamente la capa de servicios.

    Prerequisito: python manage.py create_almacenista

    Uso:
        Seeder().run()             # idempotente
        Seeder().run(force=True)   # regenera movimientos
    """

    def __init__(
        self,
        write_fn: Callable[[str], None] | None = None,
        warn_fn: Callable[[str], None] | None = None,
    ):
        self._write = write_fn or print
        self._warn_fn = warn_fn or (lambda msg: print(f"  [!] {msg}"))

    # =========================================================================
    # Punto de entrada
    # =========================================================================

    def run(self, force: bool = False) -> SeedResult:
        self._title("SEED ICM -- inicio")
        result = SeedResult()

        almacenista = self._get_almacenista()

        # --- Infraestructura (siempre idempotente) ---
        self._section("Fase 1 -- Usuarios adicionales")
        self._ensure_extra_users(almacenista)

        self._section("Fase 2 -- Ubicaciones")
        locations = self._ensure_locations()

        # --- Catalogo (idempotente por slug/SKU) ---
        self._section("Fase 3 -- Categorias")
        cats = self._ensure_categories(almacenista, result)

        self._section("Fase 4 -- Subcategorias / Marcas")
        subcats = self._ensure_subcategories(almacenista, cats, result)

        self._section("Fase 5 -- Productos")
        products = self._ensure_products(almacenista, cats, subcats, result)

        self._section("Fase 6 -- Proveedores")
        suppliers = self._ensure_suppliers(almacenista)

        self._write(
            f"  Catalogo listo: {result.products_created} creados, "
            f"{result.products_skipped} existentes, "
            f"{len(products)} totales disponibles"
        )

        # --- Movimientos (condicional a idempotencia) ---
        if not force and self._is_seeded():
            self._warn("Movimientos ya sembrados. Usa --force para regenerar.")
            result.skipped_movement_phase = True
        else:
            bodega = locations["bodega"]
            bodega_norte = locations["bodega-norte"]
            vitrina = locations["vitrina"]
            vitrina2 = locations["vitrina-2"]

            by_cat = self._group_by_category(products)

            self._section("Fase 7 -- Stock bodega principal")
            self._seed_stock_bodega(almacenista, suppliers, by_cat, bodega)

            self._section("Fase 8 -- Stock bodega norte")
            self._seed_stock_bodega_norte(almacenista, suppliers, by_cat, bodega_norte)

            self._section("Fase 9 -- Traslados internos")
            self._seed_transfers(almacenista, products, bodega, vitrina, vitrina2)

            self._section("Fase 10 -- Ventas al por menor (vitrina)")
            self._seed_retail_sales(almacenista, vitrina)

            self._section("Fase 11 -- Ventas al por mayor (bodega)")
            self._seed_wholesale_sales(almacenista, by_cat, bodega)

            self._section("Fase 12 -- Ajustes de inventario")
            self._seed_adjustments(almacenista, by_cat, bodega)

            self._section("Fase 13 -- Escenario producto agotado")
            self._seed_stockout(almacenista, by_cat, vitrina)

            self._section("Fase 14 -- Combos de productos")
            self._ensure_combos(almacenista, products)

        self._title("SEED completado")
        self._build_result(result, locations)
        return result

    # =========================================================================
    # Prerequisitos
    # =========================================================================

    def _get_almacenista(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(role="almacenista", is_active=True).first()
        if not user:
            raise RuntimeError(
                "No se encontro almacenista activo. "
                "Ejecuta: python manage.py create_almacenista"
            )
        self._ok(f"Almacenista: {user.username}")
        return user

    # =========================================================================
    # Fase 1: Usuarios adicionales
    # =========================================================================

    def _ensure_extra_users(self, almacenista) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        extra = [
            {
                "username": "auxiliar_despacho_1",
                "email": "auxiliar1@icm.local",
                "first_name": "Maria",
                "last_name": "Lopez Vega",
                "role": "auxiliar_despacho",
            },
            {
                "username": "auxiliar_despacho_2",
                "email": "auxiliar2@icm.local",
                "first_name": "Pedro",
                "last_name": "Garcia Mora",
                "role": "auxiliar_despacho",
            },
            {
                "username": "administrador_icm",
                "email": "admin@icm.local",
                "first_name": "Sofia",
                "last_name": "Martinez Cruz",
                "role": "administrador",
            },
        ]
        for data in extra:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": data["role"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password("Seed2024ICM!")
                user.save(update_fields=["password"])
                self._ok(f"  + Usuario: {user.username} ({user.role})")
            else:
                self._ok(f"  · Usuario existente: {user.username}")

    # =========================================================================
    # Fase 2: Ubicaciones
    # =========================================================================

    def _ensure_locations(self) -> dict[str, Any]:
        from apps.inventory.models import Location

        result: dict[str, Any] = {}
        for code in ("bodega", "vitrina"):
            loc = Location.objects.filter(code=code).first()
            if loc:
                result[code] = loc
                self._ok(f"  · Ubicacion existente: {loc.name}")

        for data in config.EXTRA_LOCATIONS:
            defaults = {
                "name": data["name"],
                "description": data.get("description", ""),
                "is_retail": data.get("is_retail", False),
                "is_active": True,
            }
            if data.get("max_capacity"):
                defaults["max_capacity"] = data["max_capacity"]
            loc, created = Location.objects.get_or_create(
                code=data["code"], defaults=defaults
            )
            if created:
                self._ok(f"  + Ubicacion: {loc.name} [{loc.code}]")
            else:
                self._ok(f"  · Ubicacion existente: {loc.name}")
            result[loc.code] = loc

        missing = [
            c
            for c in ("bodega", "vitrina", "bodega-norte", "vitrina-2")
            if c not in result
        ]
        if missing:
            raise RuntimeError(f"Ubicaciones faltantes en BD: {missing}")
        return result

    # =========================================================================
    # Fase 3: Categorias
    # =========================================================================

    def _ensure_categories(self, almacenista, result: SeedResult) -> dict[str, Any]:
        from apps.catalog.models import Category
        from apps.catalog.services import create_category

        cats: dict[str, Any] = {}
        for data in config.CATEGORIES:
            existing = Category.objects.filter(slug=data["slug"]).first()
            if not existing:
                existing = Category.objects.filter(name__iexact=data["name"]).first()

            if existing:
                cats[data["slug"]] = existing
                result.categories_skipped += 1
                self._ok(f"  · Categoria existente: {existing.name} [{existing.slug}]")
            else:
                cat = create_category(
                    almacenista,
                    name=data["name"],
                    description=data.get("description", ""),
                    requires_serial_number=data.get("requires_serial_number", False),
                    is_returnable=data.get("is_returnable", False),
                )
                cats[data["slug"]] = cat
                result.categories_created += 1
                self._ok(f"  + Categoria: {cat.name}")

        return cats

    # =========================================================================
    # Fase 4: Subcategorias / Marcas
    # =========================================================================

    def _ensure_subcategories(
        self, almacenista, cats: dict, result: SeedResult
    ) -> dict[str, Any]:
        """Retorna dict[(category_slug, brand_name) -> Subcategory]."""
        from apps.catalog.models import Subcategory
        from apps.catalog.services import create_subcategory

        subcats: dict[tuple, Any] = {}
        for cat_slug, brand_name, description in config.SUBCATEGORIES:
            cat = cats.get(cat_slug)
            if not cat:
                self._warn(
                    f"Categoria '{cat_slug}' no encontrada para marca '{brand_name}'"
                )
                continue

            existing = Subcategory.objects.filter(
                category=cat, name__iexact=brand_name
            ).first()
            if existing:
                subcats[(cat_slug, brand_name)] = existing
            else:
                subcat = create_subcategory(
                    almacenista,
                    category_id=cat.id,
                    name=brand_name,
                    description=description,
                )
                subcats[(cat_slug, brand_name)] = subcat
                result.subcategories_created += 1
                self._ok(f"  + Marca: {brand_name} -> {cat.name}")

        created = result.subcategories_created
        total = len(subcats)
        self._ok(f"  Marcas: {created} creadas, {total - created} existentes")
        return subcats

    # =========================================================================
    # Fase 5: Productos (catalogo de referencia con datos completos)
    # =========================================================================

    def _ensure_products(
        self, almacenista, cats: dict, subcats: dict, result: SeedResult
    ) -> dict[str, Any]:
        """Retorna dict[sku -> Product]. Crea solo los que no existen."""
        from apps.catalog.models import Product
        from apps.catalog.services import create_product

        products: dict[str, Any] = {}

        for p_data in config.PRODUCTS:
            sku = p_data["sku"]
            existing = Product.objects.filter(sku__iexact=sku).first()
            if existing:
                products[sku] = existing
                result.products_skipped += 1
                continue

            cat_slug = p_data["category_slug"]
            cat = cats.get(cat_slug)
            if not cat:
                self._warn(f"Categoria '{cat_slug}' no encontrada para {sku} — omitido")
                continue

            brand = p_data.get("brand", "Can")
            subcat = subcats.get((cat_slug, brand))

            try:
                product = create_product(
                    almacenista,
                    {
                        "sku": sku,
                        "name": p_data["name"],
                        "category_id": cat.id,
                        "subcategory_id": subcat.id if subcat else None,
                        "brand": brand,
                        "unit_cost": p_data.get("unit_cost"),
                        "sale_price_retail": p_data.get("sale_price_retail"),
                        "sale_price_wholesale": p_data.get("sale_price_wholesale"),
                        "tax_rate_pct": p_data.get("tax_rate_pct"),
                        "reorder_point": p_data.get("reorder_point", 0),
                        "requires_expiration": p_data.get("requires_expiration", False),
                        "requires_cold_chain": p_data.get("requires_cold_chain", False),
                        "weight_grams": p_data.get("weight_grams"),
                        "notes": p_data.get("notes", ""),
                        "currency": "COP",
                    },
                    request=None,
                )
                products[sku] = product
                result.products_created += 1
                self._ok(f"  + {sku}: {p_data['name'][:50]}")
            except Exception as exc:
                self._warn(f"Producto {sku} error: {exc}")

        return products

    # =========================================================================
    # Fase 6: Proveedores
    # =========================================================================

    def _ensure_suppliers(self, almacenista) -> dict[str, Any]:
        from apps.purchasing.models import Supplier
        from apps.purchasing.services import create_supplier

        result: dict[str, Any] = {}
        for data in config.SUPPLIERS:
            nit = data.get("nit")
            existing = Supplier.objects.filter(nit=nit).first() if nit else None
            if not existing:
                existing = Supplier.objects.filter(
                    nombre_comercial=data["nombre_comercial"]
                ).first()

            if existing:
                self._ok(f"  · Proveedor existente: {existing.nombre_comercial}")
                result[data["nombre_comercial"]] = existing
            else:
                supplier = create_supplier(almacenista, data, request=None)
                self._ok(f"  + Proveedor: {supplier.nombre_comercial}")
                result[data["nombre_comercial"]] = supplier
        return result

    # =========================================================================
    # Idempotencia
    # =========================================================================

    def _is_seeded(self) -> bool:
        from apps.purchasing.models import Supplier

        supplier = Supplier.objects.filter(nit=config.SEED_MARKER_NIT).first()
        if not supplier:
            return False
        return supplier.purchase_orders.filter(status="completada").exists()

    # =========================================================================
    # Helpers de agrupacion
    # =========================================================================

    def _group_by_category(self, products: dict[str, Any]) -> dict[str, list]:
        """Agrupa {sku: Product} en {category_slug: [Product]}."""
        by_cat: dict[str, list] = {}
        for product in products.values():
            slug = product.category.slug
            by_cat.setdefault(slug, []).append(product)
        return by_cat

    def _split_by_serial(
        self,
        by_cat: dict[str, list],
        category_slugs: list[str],
        qty_multiplier: float = 1.0,
    ) -> tuple[list, list]:
        items: list[tuple[Any, int]] = []
        serial_items: list[tuple[Any, int]] = []
        for slug in category_slugs:
            base_qty = config.CATEGORY_QTY.get(slug, config.DEFAULT_QTY)
            qty = max(1, int(base_qty * qty_multiplier))
            for product in by_cat.get(slug, []):
                if product.category.requires_serial_number:
                    serial_items.append((product, qty))
                else:
                    items.append((product, qty))
        return items, serial_items

    # =========================================================================
    # Fase 7: Stock bodega principal
    # =========================================================================

    def _seed_stock_bodega(
        self, almacenista, suppliers: dict, by_cat: dict, bodega
    ) -> None:
        sup_icm = suppliers["ICM Distribuidora Principal SAS"]
        sup_ter = suppliers["Terapias Medicas de Colombia Ltda"]
        sup_ag = suppliers["Distribuidora Agujas y Accesorios SAS"]
        sup_eq = suppliers["Equimed Colombia SAS"]

        # Grupo A: Electroterapia (devices con serial) + Masajeadores
        items_a, serial_a = self._split_by_serial(
            by_cat, ["electroterapia", "masajeadores"]
        )
        if items_a:
            self._purchase_and_receive(
                almacenista, sup_icm, bodega, items_a, "OC-A Electro+Masaje"
            )
        for p, qty in serial_a:
            self._entry_with_serial(almacenista, p, qty, bodega)

        # OC referencial PENDIENTE solo para dispositivos con serial
        serial_pending = [
            (p, config.CATEGORY_QTY.get(p.category.slug, config.DEFAULT_QTY))
            for p in by_cat.get("electroterapia", [])[:3]
            if p.category.requires_serial_number
        ]
        if serial_pending:
            self._create_pending_po(
                almacenista, sup_icm, serial_pending, "OC-REF serial pendiente"
            )

        # Grupo B: Bandas + Cintas + Pelotas
        items_b, serial_b = self._split_by_serial(
            by_cat, ["bandas", "cintas", "pelotas"]
        )
        if items_b:
            self._purchase_and_receive(
                almacenista, sup_ter, bodega, items_b, "OC-B Bandas+Cintas+Pelotas"
            )
        for p, qty in serial_b:
            self._entry_with_serial(almacenista, p, qty, bodega)

        # Grupo C: Agujas + Accesorios (el mas grande del catalogo)
        items_c, serial_c = self._split_by_serial(by_cat, ["agujas", "accesorios"])
        if items_c:
            self._purchase_and_receive(
                almacenista, sup_ag, bodega, items_c, "OC-C Agujas+Accesorios"
            )
        for p, qty in serial_c:
            self._entry_with_serial(almacenista, p, qty, bodega)

        # Grupo D: Camillas + Pedales + Suelo Pelvico + Terapias de Mano
        items_d, serial_d = self._split_by_serial(
            by_cat, ["camillas", "pedales", "suelo-pelvico", "terapias-de-mano"]
        )
        if items_d:
            self._purchase_and_receive(
                almacenista, sup_eq, bodega, items_d, "OC-D Camillas+Pedales+Suelo+Mano"
            )
        for p, qty in serial_d:
            self._entry_with_serial(almacenista, p, qty, bodega)

        total = sum(len(v) for v in by_cat.values())
        self._ok(f"Stock bodega principal: {total} SKUs procesados")

    # =========================================================================
    # Fase 8: Stock bodega norte (alta rotacion)
    # =========================================================================

    def _seed_stock_bodega_norte(
        self, almacenista, suppliers: dict, by_cat: dict, bodega_norte
    ) -> None:
        sup_mr = suppliers["MedRehab Importaciones Ltda."]
        alta_rotacion = ["bandas", "accesorios", "pelotas", "cintas", "agujas"]
        sub_cat = {k: v[:3] for k, v in by_cat.items() if k in alta_rotacion}
        items, serial_items = self._split_by_serial(
            sub_cat, alta_rotacion, qty_multiplier=0.5
        )
        if items:
            self._purchase_and_receive(
                almacenista,
                sup_mr,
                bodega_norte,
                items,
                "OC-Norte Alta-Rotacion",
                delivery_days=12,
            )
        for p, qty in serial_items:
            self._entry_with_serial(almacenista, p, qty, bodega_norte)
        self._ok(f"Stock bodega norte: {len(items)} SKUs recibidos")

    # =========================================================================
    # Fase 9: Traslados internos
    # =========================================================================

    def _seed_transfers(
        self, almacenista, products: dict, bodega, vitrina, vitrina2
    ) -> None:
        from apps.inventory.models import StockByLocation
        from apps.movements.services import register_internal_transfer

        transfer_cats = {
            "bandas": (vitrina, 0.35),
            "cintas": (vitrina, 0.40),
            "pelotas": (vitrina, 0.35),
            "accesorios": (vitrina, 0.30),
            "masajeadores": (vitrina, 0.30),
            "terapias-de-mano": (vitrina, 0.25),
            "agujas": (vitrina2, 0.20),
            "electroterapia": (vitrina2, 0.20),
        }

        count = 0
        for sku, product in products.items():
            cat_slug = product.category.slug
            if cat_slug not in transfer_cats:
                continue
            dest, pct = transfer_cats[cat_slug]
            row = StockByLocation.objects.filter(
                product=product, location=bodega
            ).first()
            if not row or row.current_stock < 2:
                continue
            qty = max(1, int(row.current_stock * pct))
            kwargs: dict[str, Any] = {
                "product_id": product.id,
                "origin_id": bodega.id,
                "destination_id": dest.id,
                "quantity": qty,
            }
            if product.category.requires_serial_number:
                kwargs["serial_number"] = f"SN-TRF-{product.sku}-001"
                kwargs["electrical_safety_acknowledged"] = True
            if product.requires_cold_chain:
                kwargs["cold_chain_acknowledged"] = True
            try:
                register_internal_transfer(almacenista, **kwargs)
                self._ok(f"  <-> {sku} x {qty}: bodega -> {dest.code}")
                count += 1
            except Exception as exc:
                self._warn(f"Traslado {sku} omitido: {exc}")

        self._ok(f"Traslados completados: {count}")

    # =========================================================================
    # Fase 10: Ventas al por menor
    # =========================================================================

    def _seed_retail_sales(self, almacenista, vitrina) -> None:
        from apps.inventory.models import StockByLocation
        from apps.movements.models import MovementType
        from apps.movements.services import register_dispatch

        rows = StockByLocation.objects.filter(
            location=vitrina, current_stock__gt=0
        ).select_related("product__category")

        count = 0
        for row in rows:
            product = row.product
            stock = row.current_stock
            qty = stock if stock <= 3 else (stock - 2 if stock <= 10 else stock - 3)
            if qty <= 0:
                continue
            kwargs: dict[str, Any] = {
                "product_id": product.id,
                "location_id": vitrina.id,
                "quantity": qty,
                "movement_type": MovementType.SALIDA_VENTA_MENOR,
            }
            if product.category.requires_serial_number:
                kwargs["serial_number"] = f"SN-DISP-{product.sku}-001"
                kwargs["electrical_safety_acknowledged"] = True
            if product.requires_cold_chain:
                kwargs["cold_chain_acknowledged"] = True
            try:
                register_dispatch(almacenista, **kwargs)
                self._ok(
                    f"  -> Venta menor {product.sku} x {qty} (queda {stock - qty})"
                )
                count += 1
            except Exception as exc:
                self._warn(f"Venta {product.sku} omitida: {exc}")

        self._ok(f"Ventas al por menor: {count} movimientos")

    # =========================================================================
    # Fase 11: Ventas al por mayor
    # =========================================================================

    def _seed_wholesale_sales(self, almacenista, by_cat: dict, bodega) -> None:
        from apps.inventory.models import StockByLocation
        from apps.movements.models import MovementType
        from apps.movements.services import register_dispatch

        wholesale_cats = [
            "electroterapia",
            "masajeadores",
            "camillas",
            "pedales",
            "suelo-pelvico",
            "terapias-de-mano",
        ]

        customer_idx = 0
        count = 0
        for cat_slug in wholesale_cats:
            for product in by_cat.get(cat_slug, [])[:3]:
                row = StockByLocation.objects.filter(
                    product=product, location=bodega
                ).first()
                if not row or row.current_stock < 2:
                    continue
                qty = min(3, row.current_stock // 3)
                if qty < 1:
                    continue
                customer = config.CUSTOMERS[customer_idx % len(config.CUSTOMERS)]
                customer_idx += 1
                kwargs: dict[str, Any] = {
                    "product_id": product.id,
                    "location_id": bodega.id,
                    "quantity": qty,
                    "movement_type": MovementType.SALIDA_VENTA_MAYOR,
                    "customer_data": customer,
                    "privacy_notice_acknowledged": True,
                }
                if product.category.requires_serial_number:
                    kwargs["serial_number"] = f"SN-MAYOR-{product.sku}-001"
                    kwargs["electrical_safety_acknowledged"] = True
                if product.requires_cold_chain:
                    kwargs["cold_chain_acknowledged"] = True
                try:
                    register_dispatch(almacenista, **kwargs)
                    self._ok(
                        f"  -> Venta mayor {product.sku} x {qty} -- {customer['customer_name']}"
                    )
                    count += 1
                except Exception as exc:
                    self._warn(f"Venta mayor {product.sku} omitida: {exc}")

        self._ok(f"Ventas al por mayor: {count} movimientos")

    # =========================================================================
    # Fase 12: Ajustes de inventario (BR-07)
    # =========================================================================

    def _seed_adjustments(self, almacenista, by_cat: dict, bodega) -> None:
        from apps.inventory.models import StockByLocation
        from apps.movements.services import register_adjustment

        done = 0

        for product in by_cat.get("agujas", [])[:2]:
            row = StockByLocation.objects.filter(
                product=product, location=bodega
            ).first()
            if row and row.current_stock > 5:
                new_qty = row.current_stock - 3
                try:
                    register_adjustment(
                        almacenista,
                        product_id=product.id,
                        location_id=bodega.id,
                        new_quantity=new_qty,
                        justification="Ajuste negativo: 3 unidades embalaje roto en conteo fisico.",
                    )
                    self._ok(f"  +/- Ajuste (-3) {product.sku}: stock -> {new_qty}")
                    done += 1
                except Exception as exc:
                    self._warn(f"Ajuste {product.sku} omitido: {exc}")

        for product in by_cat.get("accesorios", [])[:2]:
            row = StockByLocation.objects.filter(
                product=product, location=bodega
            ).first()
            if row:
                new_qty = row.current_stock + 4
                try:
                    register_adjustment(
                        almacenista,
                        product_id=product.id,
                        location_id=bodega.id,
                        new_quantity=new_qty,
                        justification="Ajuste positivo: 4 unidades halladas sin registrar en ultima recepcion.",
                    )
                    self._ok(f"  +/- Ajuste (+4) {product.sku}: stock -> {new_qty}")
                    done += 1
                except Exception as exc:
                    self._warn(f"Ajuste {product.sku} omitido: {exc}")

        for product in by_cat.get("bandas", [])[:1]:
            row = StockByLocation.objects.filter(
                product=product, location=bodega
            ).first()
            if row and row.current_stock > 8:
                new_qty = row.current_stock - 5
                try:
                    register_adjustment(
                        almacenista,
                        product_id=product.id,
                        location_id=bodega.id,
                        new_quantity=new_qty,
                        justification="Ajuste merma: 5 unidades deterioro por humedad en inspeccion bodega.",
                    )
                    self._ok(f"  +/- Ajuste (-5) {product.sku}: stock -> {new_qty}")
                    done += 1
                except Exception as exc:
                    self._warn(f"Ajuste {product.sku} omitido: {exc}")

        self._ok(f"Ajustes realizados: {done}")

    # =========================================================================
    # Fase 13: Escenario agotamiento
    # =========================================================================

    def _seed_stockout(self, almacenista, by_cat: dict, vitrina) -> None:
        from apps.inventory.models import StockByLocation
        from apps.movements.models import MovementType
        from apps.movements.services import register_dispatch

        count = 0
        for cat_slug in ("cintas", "pelotas"):
            for product in by_cat.get(cat_slug, [])[:1]:
                row = StockByLocation.objects.filter(
                    product=product, location=vitrina
                ).first()
                if not row or row.current_stock == 0:
                    self._ok(f"  · {product.sku} ya agotado en vitrina")
                    continue
                qty = row.current_stock
                try:
                    register_dispatch(
                        almacenista,
                        product_id=product.id,
                        location_id=vitrina.id,
                        quantity=qty,
                        movement_type=MovementType.SALIDA_VENTA_MENOR,
                    )
                    self._ok(f"  -> {product.sku} x {qty} -> AGOTADO en vitrina")
                    count += 1
                except Exception as exc:
                    self._warn(f"Agotamiento {product.sku} omitido: {exc}")

        self._ok(f"Productos agotados en vitrina: {count}")

    # =========================================================================
    # Fase 14: Combos de productos
    # =========================================================================

    def _ensure_combos(self, almacenista, products: dict) -> None:
        from apps.catalog.models import ProductCombo
        from apps.catalog.services import create_combo

        created = 0
        skipped = 0
        for c_data in config.COMBOS:
            sku = c_data["sku"]
            if ProductCombo.objects.filter(sku__iexact=sku).exists():
                self._ok(f"  · Combo existente: {sku}")
                skipped += 1
                continue

            # Verificar que todos los productos del combo existan
            missing = [s for s, _ in c_data["items"] if s not in products]
            if missing:
                self._warn(f"Combo {sku} omitido: faltan productos {missing}")
                continue

            items = [
                {"product_id": products[s].id, "quantity": qty}
                for s, qty in c_data["items"]
            ]
            try:
                combo = create_combo(
                    almacenista,
                    {
                        "sku": sku,
                        "name": c_data["name"],
                        "items": items,
                        "price_strategy": c_data.get("price_strategy", "derived"),
                        "fixed_price_retail": c_data.get("fixed_price_retail"),
                        "fixed_price_wholesale": c_data.get("fixed_price_wholesale"),
                    },
                    request=None,
                )
                self._ok(f"  + Combo: {combo.sku} -- {combo.name}")
                created += 1
            except Exception as exc:
                self._warn(f"Combo {sku} error: {exc}")

        self._ok(f"Combos: {created} creados, {skipped} existentes")

    # =========================================================================
    # Helpers de compras (OC -> Recepcion)
    # =========================================================================

    def _purchase_and_receive(
        self,
        almacenista,
        supplier,
        location,
        items: list[tuple[Any, int]],
        label: str,
        delivery_days: int = 7,
    ) -> Any | None:
        from apps.purchasing.services import (
            confirm_purchase_order,
            confirm_reception,
            create_purchase_order,
            create_reception,
        )

        if not items:
            return None

        po_items = [
            {
                "product_id": p.id,
                "quantity_ordered": qty,
                "unit_cost": p.unit_cost
                or config.CATEGORY_QTY.get(p.category.slug, 50000),
            }
            for p, qty in items
        ]

        with transaction.atomic():
            po = create_purchase_order(
                almacenista,
                {
                    "supplier_id": supplier.id,
                    "expected_delivery": date.today() + timedelta(days=delivery_days),
                    "notes": f"[SEED] {label}",
                    "items": po_items,
                },
                request=None,
            )
            confirm_purchase_order(almacenista, po.id, request=None)

            poi_map = {item.product_id: item for item in po.items.all()}
            reception_items = [
                {
                    "purchase_order_item_id": poi_map[p.id].id,
                    "quantity_received": qty,
                    **(
                        {
                            "lot_code": f"SEED-{p.sku}-L01",
                            "lot_expiration_date": date.today().replace(
                                year=date.today().year + 2
                            ),
                        }
                        if p.requires_expiration
                        else {}
                    ),
                }
                for p, qty in items
                if p.id in poi_map
            ]
            if not reception_items:
                return po

            reception = create_reception(
                almacenista,
                po.id,
                {
                    "destination_location_id": location.id,
                    "notes": f"[SEED] Recepcion {label}",
                    "items": reception_items,
                },
                request=None,
            )
            confirm_reception(almacenista, reception.id, request=None)

        self._ok(
            f"  + OC {po.number} confirmada ({len(items)} items -> {location.name})"
        )
        return po

    def _create_pending_po(
        self,
        almacenista,
        supplier,
        items: list[tuple[Any, int]],
        label: str,
    ) -> Any | None:
        from apps.purchasing.services import (
            confirm_purchase_order,
            create_purchase_order,
        )

        if not items:
            return None

        po_items = [
            {
                "product_id": p.id,
                "quantity_ordered": qty,
                "unit_cost": p.unit_cost or 50000,
            }
            for p, qty in items
        ]

        with transaction.atomic():
            po = create_purchase_order(
                almacenista,
                {
                    "supplier_id": supplier.id,
                    "expected_delivery": date.today() + timedelta(days=14),
                    "notes": f"[SEED] {label}",
                    "items": po_items,
                },
                request=None,
            )
            confirm_purchase_order(almacenista, po.id, request=None)

        self._ok(f"  ~ OC pendiente: {po.number} -- {label}")
        return po

    def _entry_with_serial(self, almacenista, product, qty: int, location) -> None:
        from apps.movements.services import register_entry

        unit_cost = product.unit_cost or 50000
        for n in range(qty):
            serial = f"SN-{product.sku}-{n + 1:04d}"
            register_entry(
                almacenista,
                product_id=product.id,
                quantity=1,
                location_id=location.id,
                serial_number=serial,
                unit_cost=unit_cost,
                electrical_safety_acknowledged=True,
            )
        self._ok(f"  + Serial {product.sku} x {qty} -> {location.name}")

    # =========================================================================
    # Resultado final
    # =========================================================================

    def _build_result(self, result: SeedResult, locations: dict) -> None:
        from django.db.models import Sum

        from apps.inventory.models import StockByLocation
        from apps.movements.models import Movement, MovementType
        from apps.purchasing.models import PurchaseOrder

        result.purchase_orders = PurchaseOrder.objects.count()
        result.movements = Movement.objects.count()
        result.stock_rows = StockByLocation.objects.count()

        for tipo, mt in [
            ("ENTRADA", MovementType.ENTRADA),
            ("SALIDA_MENOR", MovementType.SALIDA_VENTA_MENOR),
            ("SALIDA_MAYOR", MovementType.SALIDA_VENTA_MAYOR),
            ("TRASLADO", MovementType.TRASLADO),
            ("AJUSTE", MovementType.AJUSTE),
        ]:
            n = Movement.objects.filter(movement_type=mt).count()
            if n:
                result.movements_by_type[tipo] = n

        for code, loc in locations.items():
            total = (
                StockByLocation.objects.filter(location=loc).aggregate(
                    s=Sum("current_stock")
                )["s"]
                or 0
            )
            activos = StockByLocation.objects.filter(
                location=loc, current_stock__gt=0
            ).count()
            agotados = StockByLocation.objects.filter(
                location=loc, current_stock=0
            ).count()
            result.stock_by_location[loc.name] = {
                "activos": activos,
                "agotados": agotados,
                "total_units": total,
            }

    # =========================================================================
    # Helpers de salida
    # =========================================================================

    def _title(self, msg: str) -> None:
        self._write(f"\n{'=' * 50}")
        self._write(f"  {msg}")
        self._write(f"{'=' * 50}")

    def _section(self, msg: str) -> None:
        self._write(f"\n--- {msg} ---")

    def _ok(self, msg: str) -> None:
        self._write(f"  {msg}")

    def _warn(self, msg: str) -> None:
        self._warn_fn(msg)
