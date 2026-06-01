"""Crea el modelo Invoice que agrupa Movements bajo un comprobante comercial."""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("movements", "0005_movement_pricing_snapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "number",
                    models.CharField(
                        max_length=20, unique=True, help_text="Número ICM-XXXX."
                    ),
                ),
                ("customer_name", models.CharField(blank=True, max_length=255)),
                ("customer_email", models.EmailField(blank=True)),
                ("customer_phone", models.CharField(blank=True, max_length=50)),
                ("customer_address", models.TextField(blank=True)),
                (
                    "subtotal",
                    models.DecimalField(decimal_places=4, default=0, max_digits=14),
                ),
                (
                    "discount_total",
                    models.DecimalField(decimal_places=4, default=0, max_digits=12),
                ),
                (
                    "tax_total",
                    models.DecimalField(decimal_places=4, default=0, max_digits=12),
                ),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=4, default=0, max_digits=14),
                ),
                ("currency", models.CharField(default="COP", max_length=3)),
                (
                    "pdf",
                    models.FileField(
                        blank=True, null=True, upload_to="invoices/%Y/%m/"
                    ),
                ),
                (
                    "issued_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "issued_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoices_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "movements",
                    models.ManyToManyField(
                        blank=True,
                        related_name="invoices",
                        to="movements.movement",
                    ),
                ),
            ],
            options={
                "verbose_name": "Factura",
                "verbose_name_plural": "Facturas",
                "ordering": ("-issued_at",),
            },
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["number"], name="movements_invoice_number_idx"),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["issued_at"], name="movements_invoice_issued_idx"
            ),
        ),
    ]
