"""Migrate existing serials on Movement to ProductSerial model."""

from __future__ import annotations

from django.db import migrations


def _migrate_serials(apps, schema_editor):
    Movement = apps.get_model("movements", "Movement")
    ProductSerial = apps.get_model("catalog", "ProductSerial")
    Product = apps.get_model("catalog", "Product")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    # Ensure ProductSerial permissions exist
    ct, _ = ContentType.objects.get_or_create(
        app_label="catalog", model="productserial"
    )
    for codename, name in [
        ("add_productserial", "Can add product serial"),
        ("change_productserial", "Can change product serial"),
        ("delete_productserial", "Can delete product serial"),
        ("view_productserial", "Can view product serial"),
    ]:
        Permission.objects.get_or_create(
            content_type=ct, codename=codename, defaults={"name": name}
        )

    created = 0
    updated = 0

    # 1. Create ProductSerial from ENTRADA movements with serial
    for m in Movement.objects.filter(
        serial_number__isnull=False,
        movement_type="ENTRADA",
    ).exclude(serial_number=""):
        serial = m.serial_number.strip()
        if not serial:
            continue
        ps, was_created = ProductSerial.objects.get_or_create(
            product_id=m.product_id,
            serial_number=serial,
            defaults={
                "status": "available",
                "current_location_id": m.destination_location_id,
                "last_movement": m,
            },
        )
        if was_created:
            created += 1

    # 2. Mark as dispatched for SALIDA movements
    for m in Movement.objects.filter(
        serial_number__isnull=False,
        movement_type__in=[
            "SALIDA_VENTA_MAYOR",
            "SALIDA_VENTA_MENOR",
            "SALIDA_DANO",
            "SALIDA_VENCIMIENTO",
            "SALIDA_COMBO",
        ],
    ).exclude(serial_number=""):
        serial = m.serial_number.strip()
        if not serial:
            continue
        updated_count = ProductSerial.objects.filter(
            product_id=m.product_id,
            serial_number=serial,
            status="available",
        ).update(
            status="dispatched",
            current_location=None,
            last_movement=m,
        )
        updated += updated_count

    # 3. Update location for TRASLADO movements
    for m in Movement.objects.filter(
        serial_number__isnull=False,
        movement_type__in=["TRASLADO"],
    ).exclude(serial_number=""):
        serial = m.serial_number.strip()
        if not serial:
            continue
        updated_count = ProductSerial.objects.filter(
            product_id=m.product_id,
            serial_number=serial,
        ).update(
            current_location_id=m.destination_location_id,
            last_movement=m,
        )
        updated += updated_count

    # 4. Mark as adjusted for AJUSTE movements
    for m in Movement.objects.filter(
        serial_number__isnull=False,
        movement_type__in=["AJUSTE"],
    ).exclude(serial_number=""):
        serial = m.serial_number.strip()
        if not serial:
            continue
        updated_count = ProductSerial.objects.filter(
            product_id=m.product_id, serial_number=serial
        ).update(
            status="adjusted",
            last_movement=m,
        )
        updated += updated_count

    # 5. Reactivate for DEVOLUCION movements
    for m in Movement.objects.filter(
        serial_number__isnull=False,
        movement_type__in=["DEVOLUCION"],
    ).exclude(serial_number=""):
        serial = m.serial_number.strip()
        if not serial:
            continue
        updated_count = ProductSerial.objects.filter(
            product_id=m.product_id, serial_number=serial
        ).update(
            status="available",
            current_location_id=m.destination_location_id,
            last_movement=m,
        )
        updated += updated_count

    if created or updated:
        print(
            f"  ProductSerial migration: {created} created, {updated} status-updated."
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "movements",
            "0007_rename_movements_invoice_number_idx_movements_i_number_dec47a_idx_and_more",
        ),
        ("catalog", "0011_add_productserial_model"),
    ]

    operations = [
        migrations.RunPython(_migrate_serials, migrations.RunPython.noop),
    ]
