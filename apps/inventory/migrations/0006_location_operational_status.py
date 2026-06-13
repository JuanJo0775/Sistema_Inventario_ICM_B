from django.db import migrations, models


def backfill_operational_status(apps, schema_editor):
    Location = apps.get_model("inventory", "Location")
    Location.objects.filter(is_active=False).update(operational_status="archived")
    Location.objects.filter(is_active=True).update(operational_status="active")


def reverse_operational_status_backfill(apps, schema_editor):
    Location = apps.get_model("inventory", "Location")
    Location.objects.filter(operational_status="archived").update(is_active=False)
    Location.objects.exclude(operational_status="archived").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0005_storage_type_model_and_location_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="operational_status",
            field=models.CharField(
                choices=[
                    ("active", "Activa"),
                    ("maintenance", "Mantenimiento"),
                    ("restricted", "Restringida"),
                    ("blocked", "Bloqueada"),
                    ("archived", "Archivada"),
                ],
                db_index=True,
                default="active",
                help_text="Estado operativo de la ubicación para reglas de movimientos.",
                max_length=20,
            ),
        ),
        migrations.RunPython(
            backfill_operational_status,
            reverse_operational_status_backfill,
        ),
    ]
