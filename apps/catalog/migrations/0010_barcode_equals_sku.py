from __future__ import annotations

from django.db import migrations, models


def forwards(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.exclude(barcode=models.F("sku")).update(barcode=models.F("sku"))


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_merge_20260531_2237"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
