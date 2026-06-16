"""Agrega campos de precio a Product y crea modelo ProductPriceHistory."""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_category_subcategory_is_active"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Campos de precio en Product (todos nullable para compatibilidad con datos existentes)
        migrations.AddField(
            model_name="product",
            name="unit_cost",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Costo de adquisición por unidad (COGS).",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="sale_price_retail",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Precio de venta al por menor (vitrina).",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="sale_price_wholesale",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Precio de venta al por mayor.",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="tax_rate_pct",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                help_text="Tasa de IVA aplicable (ej: 19.00 para 19%).",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="currency",
            field=models.CharField(
                default="COP",
                max_length=3,
                help_text="Moneda ISO 4217 (COP por defecto).",
            ),
        ),
        # Modelo ProductPriceHistory
        migrations.CreateModel(
            name="ProductPriceHistory",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        serialize=False,
                        editable=False,
                        default=uuid.uuid4,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "field_changed",
                    models.CharField(
                        max_length=64,
                        help_text="Nombre del campo de precio modificado.",
                    ),
                ),
                (
                    "old_value",
                    models.DecimalField(
                        blank=True, decimal_places=4, max_digits=12, null=True
                    ),
                ),
                (
                    "new_value",
                    models.DecimalField(
                        blank=True, decimal_places=4, max_digits=12, null=True
                    ),
                ),
                ("currency", models.CharField(default="COP", max_length=3)),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="price_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="price_history",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Historial de precio",
                "verbose_name_plural": "Historial de precios",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="productpricehistory",
            index=models.Index(
                fields=["product", "field_changed", "created_at"],
                name="catalog_pph_prod_field_idx",
            ),
        ),
    ]
