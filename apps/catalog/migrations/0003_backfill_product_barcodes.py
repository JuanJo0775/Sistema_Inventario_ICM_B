from __future__ import annotations

from django.db import migrations


def _build_product_barcode(product_id) -> str:
    import base64

    return f"ICM-{base64.b32encode(product_id.bytes).decode('ascii').rstrip('=')}"


def forwards(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for product in Product.objects.filter(barcode__isnull=True).iterator():
        product.barcode = _build_product_barcode(product.id)
        product.save(update_fields=("barcode",))

    for product in Product.objects.filter(barcode="").iterator():
        product.barcode = _build_product_barcode(product.id)
        product.save(update_fields=("barcode",))


def backwards(apps, schema_editor):
    pass  # El backfill de barcodes es idempotente; no se revierte.


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_product_requires_expiration_lot_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
