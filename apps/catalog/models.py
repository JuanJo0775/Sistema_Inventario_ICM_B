"""Catálogo de productos (RF-003, BR-04, BR-05, BR-12, BR-13)."""

from __future__ import annotations

from django.db import models

from shared.models import BaseModel


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

    class Meta:
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"
        ordering = ("category_id", "name")
        constraints = [
            models.UniqueConstraint(fields=("category", "slug"), name="uniq_subcategory_slug_per_category"),
        ]
        unique_together = ("category", "name")

    def __str__(self) -> str:
        return f"{self.category.name} / {self.name}"


class Product(BaseModel):
    """
    Producto/SKU central del dominio (RF-003, BR-12, BR-13).

    # BR-12: prefijo CAN- para marca propia; validado en catalog/services.py::create_product.
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
    weight_grams = models.PositiveIntegerField(null=True, blank=True)
    requires_cold_chain = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    # RF-011 / ERS: umbral global para alerta de stock bajo (no sustituye lógica en services).
    reorder_point = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ("name",)
        indexes = [
            models.Index(fields=("sku",)),
            models.Index(fields=("barcode",)),
            models.Index(fields=("category",)),
        ]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"


class ProductCombo(BaseModel):
    """Kit o combo: varios SKUs bajo un identificador (RF-003)."""

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(Product, through="ComboItem", related_name="product_combos")

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
            models.UniqueConstraint(fields=("combo", "product"), name="uniq_combo_product_item"),
        ]

    def __str__(self) -> str:
        return f"{self.combo.sku} × {self.product.sku} ({self.quantity})"
