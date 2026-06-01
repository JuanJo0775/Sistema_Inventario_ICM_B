"""Agrega campos de precio snapshot y customer_snapshot al modelo Movement."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("movements", "0004_add_lot_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="movement",
            name="unit_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Precio unitario de venta congelado al momento del despacho.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="unit_cost",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Costo unitario congelado al momento del despacho.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="discount_pct",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                help_text="Porcentaje de descuento aplicado (0-100).",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="discount_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Monto de descuento calculado.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="subtotal",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=14,
                null=True,
                help_text="unit_price × quantity.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="tax_rate_pct",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                help_text="Tasa de IVA congelada al momento del despacho.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="tax_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Monto de IVA calculado sobre la base imponible.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="total_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=14,
                null=True,
                help_text="Total a cobrar: subtotal - discount_amount + tax_amount.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="currency",
            field=models.CharField(
                blank=True,
                max_length=3,
                null=True,
                help_text="Moneda ISO 4217 del despacho.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="price_type",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                help_text="Tipo de precio: retail | wholesale | cost | combo.",
            ),
        ),
        migrations.AddField(
            model_name="movement",
            name="customer_snapshot",
            field=models.JSONField(
                blank=True,
                null=True,
                help_text="Datos del cliente al momento del despacho (R-02).",
            ),
        ),
    ]
