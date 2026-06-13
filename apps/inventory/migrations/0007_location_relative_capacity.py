from django.db import migrations, models


def backfill_capacity_mode(apps, schema_editor):
    Location = apps.get_model("inventory", "Location")
    Location.objects.filter(
        capacity_mode="none",
        max_capacity__isnull=False,
        max_capacity__gt=0,
    ).update(capacity_mode="absolute_legacy")


def reverse_backfill_capacity_mode(apps, schema_editor):
    Location = apps.get_model("inventory", "Location")
    Location.objects.filter(
        capacity_mode="absolute_legacy",
        max_capacity__isnull=False,
        max_capacity__gt=0,
    ).update(capacity_mode="none")


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0006_location_operational_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="capacity_level",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Escala relativa (1-5) cuando capacity_mode=relative_scale.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="location",
            name="capacity_mode",
            field=models.CharField(
                choices=[
                    ("none", "Sin capacidad"),
                    ("relative_scale", "Escala relativa"),
                    ("absolute_legacy", "Capacidad absoluta (legacy)"),
                ],
                db_index=True,
                default="none",
                help_text="Modo de capacidad para cálculo de ocupación informativa.",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="location",
            name="capacity_score",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Puntaje de capacidad relativo (unidad abstracta, no bloqueante).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="location",
            name="occupancy_estimate_pct",
            field=models.FloatField(
                blank=True,
                help_text="Estimación informativa de ocupación calculada o ajustada.",
                null=True,
            ),
        ),
        migrations.RunPython(
            backfill_capacity_mode,
            reverse_backfill_capacity_mode,
        ),
    ]
