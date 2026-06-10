import uuid

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0009_add_location_reorder_point"),
        ("movements", "0007_rename_movements_invoice_number_idx_movements_i_number_dec47a_idx_and_more"),
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
                (
                    "lot_code",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "lot_expiration_date",
                    models.DateField(blank=True, null=True),
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
                check=Q(quantity_received__gt=0),
                name="ria_qty_received_positive",
            ),
        ),
    ]
