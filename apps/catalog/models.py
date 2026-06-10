"""Catálogo de productos (RF-003, BR-04, BR-05, BR-12, BR-13)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from shared.models import BaseModel
from shared.utils.validators import normalize_sku, validate_sku_format


class Category(BaseModel):
    """
    Macrocategoría del catálogo ICM (RF-003).

    `requires_serial_number`: Electroterapia y similares (BR-04).
    `is_returnable`: solo categorías que admiten devolución (BR-05).
    """

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)
    requires_serial_number = models.BooleanField(
        default=False,
        help_text="BR-04: categoría exige número de serie en entradas/salidas.",
    )
    is_returnable = models.BooleanField(
        default=False,
        help_text="BR-05: categoría admite devoluciones (Electroterapia / electrónicos).",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Subcategory(BaseModel):
    """Subcategoría ligada a una macrocategoría (RF-003)."""

    name = models.CharField(max_length=128)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
    )
    slug = models.SlugField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"
        ordering = ("category_id", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("category", "slug"), name="uniq_subcategory_slug_per_category"
            ),
        ]
        unique_together = ("category", "name")

    def __str__(self) -> str:
        return f"{self.category.name} / {self.name}"


class Product(BaseModel):
    """
    Producto/SKU central del dominio (RF-003, BR-12, BR-13).

    # BR-12: SKU definido por usuario; formato validado por shared.utils.validators.validate_sku_format.
    `barcode`: alias de escaneo (BR-13).
    `expiration_date`: base para alertas RF-011 a 30/60 días.
    """

    sku = models.CharField(max_length=100, unique=True, db_index=True)
    barcode = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        db_index=True,  # BR-13
    )
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    subcategory = models.ForeignKey(
        Subcategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    brand = models.CharField(max_length=100, default="Can")
    expiration_date = models.DateField(null=True, blank=True)
    requires_expiration = models.BooleanField(
        default=False,
        help_text="True si el producto requiere control de vencimiento por lote.",
    )
    weight_grams = models.PositiveIntegerField(null=True, blank=True)
    requires_cold_chain = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    # RF-011 / ERS: umbral global para alerta de stock bajo (no sustituye lógica en services).
    reorder_point = models.PositiveIntegerField(default=0)

    # --- Precios (nullable para compatibilidad con productos existentes) ---
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Costo de adquisición por unidad (COGS).",
    )
    sale_price_retail = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Precio de venta al por menor (vitrina).",
    )
    sale_price_wholesale = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Precio de venta al por mayor.",
    )
    tax_rate_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tasa de IVA aplicable (ej: 19.00 para 19%).",
    )
    currency = models.CharField(
        max_length=3,
        default="COP",
        help_text="Moneda ISO 4217 (COP por defecto).",
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ("name",)
        indexes = [
            models.Index(fields=("sku",)),
            models.Index(fields=("barcode",)),
            models.Index(fields=("category",)),
        ]

    def clean(self) -> None:
        """BR-12 — Valida formato de SKU (Admin y ModelForm). La API valida en catalog.services."""
        sku = normalize_sku(self.sku or "")
        if not sku:
            raise ValidationError({"sku": "El SKU es obligatorio."})
        try:
            validate_sku_format(sku)
        except ValueError as exc:
            raise ValidationError({"sku": str(exc)}) from exc

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"


class Lot(BaseModel):
    """
    Lote de inventario asociado a un producto.

    Se usa para trazabilidad de partidas con fechas de vencimiento distintas.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="lots",
    )
    code = models.CharField(max_length=100)
    expiration_date = models.DateField()

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ("expiration_date", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("product", "code"), name="uniq_lot_code_per_product"
            ),
        ]
        indexes = [
            models.Index(fields=("product", "expiration_date")),
            models.Index(fields=("code",)),
        ]

    def __str__(self) -> str:
        return f"{self.product.sku} / {self.code}"


class ProductCombo(BaseModel):
    """Kit o combo: varios SKUs bajo un identificador (RF-003)."""

    class PriceStrategy(models.TextChoices):
        DERIVED = "derived", "Derivado de componentes"
        FIXED = "fixed", "Precio fijo del combo"

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(
        Product, through="ComboItem", related_name="product_combos"
    )

    # --- Pricing del combo ---
    price_strategy = models.CharField(
        max_length=20,
        choices=PriceStrategy.choices,
        default=PriceStrategy.DERIVED,
        help_text="derived: suma de precios de componentes. fixed: precio fijo del combo.",
    )
    fixed_price_retail = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Precio fijo al por menor del combo (si price_strategy=fixed).",
    )
    fixed_price_wholesale = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Precio fijo al por mayor del combo (si price_strategy=fixed).",
    )

    class Meta:
        verbose_name = "Combo de productos"
        verbose_name_plural = "Combos de productos"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class ComboItem(BaseModel):
    """Componente de un combo con cantidad (RF-003)."""

    combo = models.ForeignKey(
        ProductCombo,
        on_delete=models.CASCADE,
        related_name="combo_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="combo_memberships",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Ítem de combo"
        verbose_name_plural = "Ítems de combo"
        constraints = [
            models.UniqueConstraint(
                fields=("combo", "product"), name="uniq_combo_product_item"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.combo.sku} × {self.product.sku} ({self.quantity})"


class ProductPriceHistory(BaseModel):
    """
    Historial inmutable de cambios de precio por producto.

    Cada vez que se actualiza unit_cost, sale_price_retail, sale_price_wholesale
    o tax_rate_pct se registra una fila aquí para trazabilidad contable.
    """

    PRICE_FIELDS = (
        "unit_cost",
        "sale_price_retail",
        "sale_price_wholesale",
        "tax_rate_pct",
        "currency",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="price_history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="price_changes",
    )
    field_changed = models.CharField(
        max_length=64,
        help_text="Nombre del campo de precio modificado.",
    )
    old_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    new_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default="COP")

    class Meta:
        verbose_name = "Historial de precio"
        verbose_name_plural = "Historial de precios"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("product", "field_changed", "created_at")),
        ]

    def __str__(self) -> str:
        return f"{self.product.sku} / {self.field_changed}: {self.old_value} → {self.new_value}"
