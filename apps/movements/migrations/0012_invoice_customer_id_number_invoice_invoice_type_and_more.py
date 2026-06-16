import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movements", "0011_remove_invoice_customer_id_number_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="customer_id_number",
            field=models.CharField(
                blank=True,
                help_text="NIT/CC del cliente.",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="invoice_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("retail", "Venta menor (retail)"),
                    ("wholesale", "Venta mayor (wholesale)"),
                ],
                help_text="Tipo de venta: retail o wholesale.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="is_voided",
            field=models.BooleanField(
                default=False,
                help_text="True si la factura fue anulada.",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="void_reason",
            field=models.TextField(
                blank=True,
                help_text="Motivo de anulación.",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="voided_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="invoice",
            name="voided_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invoices_voided",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="movement",
            name="movement_type",
            field=models.CharField(
                choices=[
                    ("ENTRADA", "Entrada"),
                    ("SALIDA_VENTA_MAYOR", "Salida venta mayor"),
                    ("SALIDA_VENTA_MENOR", "Salida venta menor"),
                    ("SALIDA_DANO", "Salida por daño"),
                    ("SALIDA_VENCIMIENTO", "Salida por vencimiento"),
                    ("TRASLADO", "Traslado interno"),
                    ("AJUSTE", "Ajuste"),
                    ("DEVOLUCION", "Devolución"),
                    ("SALIDA_COMBO", "Salida por combo"),
                    ("ANULACION", "Anulación de factura"),
                ],
                max_length=32,
            ),
        ),
    ]
