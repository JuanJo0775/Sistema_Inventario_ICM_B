"""Migración inicial: CompanyInfo singleton."""

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list = []

    operations = [
        migrations.CreateModel(
            name="CompanyInfo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "company_name",
                    models.CharField(
                        default="Import Corporal Medical S.A.S", max_length=200
                    ),
                ),
                ("nit", models.CharField(blank=True, max_length=50)),
                ("address", models.TextField(blank=True)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.EmailField(blank=True)),
                ("dian_resolution", models.TextField(blank=True)),
                ("dian_range_from", models.PositiveIntegerField(blank=True, null=True)),
                ("dian_range_to", models.PositiveIntegerField(blank=True, null=True)),
                ("invoice_series", models.CharField(default="ICM", max_length=10)),
                ("invoice_footer", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Información de empresa",
                "verbose_name_plural": "Información de empresa",
            },
        ),
    ]
