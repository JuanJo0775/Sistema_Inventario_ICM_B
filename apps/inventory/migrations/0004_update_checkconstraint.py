"""Replace CheckConstraint kwargs to use `condition` (Django 6 compatibility).

This migration removes the old constraint and re-adds it using the
`condition=` argument to be explicit and avoid deprecation warnings.
"""

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0003_seed_default_locations"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="stockbylocation",
            name="stock_non_negative",
        ),
        migrations.AddConstraint(
            model_name="stockbylocation",
            constraint=models.CheckConstraint(
                check=Q(current_stock__gte=0), name="stock_non_negative"
            ),
        ),
    ]
