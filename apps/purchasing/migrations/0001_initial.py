import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0009_merge_20260531_2237"),
        ("inventory", "0009_add_location_reorder_point"),
        ("movements", "0007_rename_movements_invoice_number_idx_movements_i_number_dec47a_idx_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PurchaseOrderCounter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("last_number", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Contador de OC",
                "verbose_name_plural": "Contadores de OC",
            },
        ),
        migrations.CreateModel(
            name="Supplier",
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
                ("nombre_comercial", models.CharField(max_length=200)),
                ("razon_social", models.CharField(max_length=200)),
                (
                    "nit",
                    models.CharField(
                        help_text="NIT del proveedor incluyendo dígito de verificación.",
                        max_length=20,
                        unique=True,
                    ),
                ),
                ("contacto", models.CharField(blank=True, max_length=100)),
                ("correo", models.EmailField(blank=True, max_length=254)),
                ("telefono", models.CharField(blank=True, max_length=20)),
                ("ciudad", models.CharField(blank=True, max_length=100)),
                ("direccion", models.CharField(blank=True, max_length=300)),
                ("is_active", models.BooleanField(default=True)),
                ("observaciones", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="suppliers_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Proveedor",
                "verbose_name_plural": "Proveedores",
                "ordering": ("nombre_comercial",),
            },
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
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
                (
                    "number",
                    models.CharField(
                        help_text="Número secuencial OC-XXXX, generado automáticamente.",
                        max_length=20,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("borrador", "Borrador"),
                            ("pendiente", "Pendiente"),
                            ("parcialmente_recibida", "Parcialmente recibida"),
                            ("completada", "Completada"),
                            ("cancelada", "Cancelada"),
                        ],
                        default="borrador",
                        max_length=30,
                    ),
                ),
                ("expected_delivery", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("cancellation_reason", models.TextField(blank=True)),
                (
                    "cancelled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders_cancelled",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "confirmed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders_confirmed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="purchasing.supplier",
                    ),
                ),
            ],
            options={
                "verbose_name": "Orden de Compra",
                "verbose_name_plural": "Órdenes de Compra",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="PurchaseOrderItem",
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
                (
                    "quantity_ordered",
                    models.PositiveIntegerField(
                        help_text="Cantidad solicitada al proveedor."
                    ),
                ),
                (
                    "unit_cost",
                    models.DecimalField(
                        decimal_places=4,
                        help_text="Costo unitario acordado con el proveedor.",
                        max_digits=12,
                    ),
                ),
                ("notes", models.CharField(blank=True, max_length=300)),
                (
                    "quantity_received",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Acumulado de unidades recibidas en recepciones confirmadas.",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_order_items",
                        to="catalog.product",
                    ),
                ),
                (
                    "purchase_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="purchasing.purchaseorder",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ítem de OC",
                "verbose_name_plural": "Ítems de OC",
            },
        ),
        migrations.CreateModel(
            name="Reception",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("borrador", "Borrador"),
                            ("confirmada", "Confirmada"),
                            ("cancelada", "Cancelada"),
                        ],
                        default="borrador",
                        max_length=15,
                    ),
                ),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "destination_location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receptions",
                        to="inventory.location",
                    ),
                ),
                (
                    "purchase_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receptions",
                        to="purchasing.purchaseorder",
                    ),
                ),
                (
                    "received_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receptions_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Recepción",
                "verbose_name_plural": "Recepciones",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="ReceptionItem",
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
                ("lot_code", models.CharField(blank=True, max_length=100)),
                ("lot_expiration_date", models.DateField(blank=True, null=True)),
                (
                    "discrepancy_note",
                    models.TextField(
                        blank=True,
                        help_text="Obligatorio cuando la cantidad recibida difiere de la esperada.",
                    ),
                ),
                (
                    "movement",
                    models.OneToOneField(
                        blank=True,
                        help_text="Movimiento ENTRADA generado al confirmar la recepción.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reception_item_link",
                        to="movements.movement",
                    ),
                ),
                (
                    "purchase_order_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reception_items",
                        to="purchasing.purchaseorderitem",
                    ),
                ),
                (
                    "reception",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="purchasing.reception",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ítem de Recepción",
                "verbose_name_plural": "Ítems de Recepción",
            },
        ),
        # Indexes
        migrations.AddIndex(
            model_name="supplier",
            index=models.Index(fields=["nit"], name="purchasing_supplier_nit_idx"),
        ),
        migrations.AddIndex(
            model_name="supplier",
            index=models.Index(
                fields=["is_active", "nombre_comercial"],
                name="purchasing_supplier_active_name_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="purchaseorder",
            index=models.Index(
                fields=["status", "created_at"],
                name="purchasing_po_status_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="purchaseorder",
            index=models.Index(
                fields=["supplier", "status"],
                name="purchasing_po_supplier_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="purchaseorder",
            index=models.Index(
                fields=["number"], name="purchasing_po_number_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="reception",
            index=models.Index(
                fields=["purchase_order", "status"],
                name="purchasing_reception_po_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="reception",
            index=models.Index(
                fields=["received_by", "confirmed_at"],
                name="purchasing_reception_rcvby_conf_idx",
            ),
        ),
        # Unique constraints
        migrations.AlterUniqueTogether(
            name="purchaseorderitem",
            unique_together={("purchase_order", "product")},
        ),
        migrations.AlterUniqueTogether(
            name="receptionitem",
            unique_together={("reception", "purchase_order_item")},
        ),
        # Check constraints
        migrations.AddConstraint(
            model_name="purchaseorderitem",
            constraint=models.CheckConstraint(
                check=models.Q(quantity_ordered__gt=0),
                name="poi_qty_ordered_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="purchaseorderitem",
            constraint=models.CheckConstraint(
                check=models.Q(quantity_received__gte=0),
                name="poi_qty_received_nonneg",
            ),
        ),
        migrations.AddConstraint(
            model_name="receptionitem",
            constraint=models.CheckConstraint(
                check=models.Q(quantity_received__gte=0),
                name="ri_qty_received_nonneg",
            ),
        ),
    ]
