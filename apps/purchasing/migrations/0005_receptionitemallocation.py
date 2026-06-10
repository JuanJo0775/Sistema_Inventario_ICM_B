import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchasing", "0004_alter_supplier_pais"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReceptionItemAllocation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Fecha y hora de creación (UTC).",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Fecha y hora de última modificación (UTC).",
                    ),
                ),
                ("quantity_received", models.PositiveIntegerField()),
                ("lot_code", models.CharField(blank=True, max_length=100, null=True)),
                ("lot_expiration_date", models.DateField(blank=True, null=True)),
                (
                    "movement",
                    models.OneToOneField(
                        blank=True,
                        help_text="Movimiento ENTRADA generado para esta porción de recepción.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reception_allocation_link",
                        to="movements.movement",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reception_item_allocations",
                        to="inventory.location",
                    ),
                ),
                (
                    "reception_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allocations",
                        to="purchasing.receptionitem",
                    ),
                ),
            ],
            options={
                "verbose_name": "Distribución de ítem de recepción",
                "verbose_name_plural": "Distribuciones de ítems de recepción",
                "ordering": ("created_at", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="receptionitemallocation",
            constraint=models.CheckConstraint(
                check=models.Q(quantity_received__gt=0),
                name="ria_qty_received_positive",
            ),
        ),
    ]
