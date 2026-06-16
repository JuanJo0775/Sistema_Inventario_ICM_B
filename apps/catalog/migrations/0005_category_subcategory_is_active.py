# Generated manually on 2026-05-31

from django.db import migrations, models


class Migration(migrations.Migration):
    """Agrega campo is_active a Category y Subcategory para soporte de soft delete."""

    dependencies = [
        ("catalog", "0004_pg_trgm_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="subcategory",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
