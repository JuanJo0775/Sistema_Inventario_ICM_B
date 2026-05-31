"""Índices en Movement.lot y (product, lot) para mejorar queries multi-lote."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("movements", "0003_movement_immutability_trigger"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="movement",
            index=models.Index(fields=["lot"], name="movements_movement_lot_idx"),
        ),
        migrations.AddIndex(
            model_name="movement",
            index=models.Index(
                fields=["product", "lot"], name="movements_mov_prod_lot_idx"
            ),
        ),
    ]
