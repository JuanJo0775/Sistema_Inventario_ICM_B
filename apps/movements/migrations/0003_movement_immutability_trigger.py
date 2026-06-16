"""Trigger PostgreSQL que impide UPDATE directo sobre el ledger de movimientos."""

from django.db import migrations

_CREATE_SQL = """
CREATE OR REPLACE FUNCTION prevent_movement_update()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'immutable_record: Los registros de Movement no pueden modificarse (id=%%). Use un movimiento de corrección.', OLD.id;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER movement_immutability
BEFORE UPDATE ON movements_movement
FOR EACH ROW EXECUTE FUNCTION prevent_movement_update();
"""

_DROP_SQL = """
DROP TRIGGER IF EXISTS movement_immutability ON movements_movement;
DROP FUNCTION IF EXISTS prevent_movement_update();
"""


def _apply_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(_CREATE_SQL)


def _drop_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(_DROP_SQL)


class Migration(migrations.Migration):
    dependencies = [
        ("movements", "0002_movement_lot_alter_movement_movement_type"),
    ]

    operations = [
        migrations.RunPython(_apply_trigger, reverse_code=_drop_trigger),
    ]
