"""Agrega campos de precio y estrategia de pricing al modelo ProductCombo."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_product_pricing"),
    ]

    operations = [
        migrations.AddField(
            model_name="productcombo",
            name="price_strategy",
            field=models.CharField(
                choices=[
                    ("derived", "Derivado de componentes"),
                    ("fixed", "Precio fijo del combo"),
                ],
                default="derived",
                max_length=20,
                help_text="derived: suma de precios de componentes. fixed: precio fijo del combo.",
            ),
        ),
        migrations.AddField(
            model_name="productcombo",
            name="fixed_price_retail",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Precio fijo al por menor del combo (si price_strategy=fixed).",
            ),
        ),
        migrations.AddField(
            model_name="productcombo",
            name="fixed_price_wholesale",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=12,
                null=True,
                help_text="Precio fijo al por mayor del combo (si price_strategy=fixed).",
            ),
        ),
    ]
