from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("LOGIN_SUCCESS", "Login exitoso"),
                    ("LOGIN_FAILED", "Login fallido"),
                    ("LOGOUT", "Cierre de sesión"),
                    ("USER_CREATED", "Usuario creado"),
                    ("USER_UPDATED", "Usuario actualizado"),
                    ("USER_DISABLED", "Usuario deshabilitado"),
                    ("MOVEMENT_CREATED", "Movimiento creado"),
                    ("ADJUSTMENT_CREATED", "Ajuste creado"),
                    ("RETURN_CREATED", "Devolución registrada"),
                    ("REPORT_GENERATED", "Reporte generado"),
                    ("PERMISSION_CHANGED", "Permisos modificados"),
                    (
                        "STOCK_RECONSTRUCTED",
                        "Stock reconstruido desde ledger",
                    ),
                    ("PRODUCT_CREATED", "Producto creado"),
                    ("PRODUCT_UPDATED", "Producto actualizado"),
                    ("COMBO_CREATED", "Combo de productos creado"),
                    ("CATEGORY_CREATED", "Categoría de catálogo creada"),
                    (
                        "SUBCATEGORY_CREATED",
                        "Subcategoría de catálogo creada",
                    ),
                    ("MOVEMENT_CORRECTED", "Movimiento corregido (BR-06)"),
                    ("RETURN_APPROVED", "Devolución aprobada"),
                    ("RETURN_REJECTED", "Devolución rechazada"),
                    ("ALERT_ACKNOWLEDGED", "Alerta reconocida"),
                    (
                        "UNAUTHORIZED_ACCESS_ATTEMPT",
                        "Intento de acceso no autorizado",
                    ),
                    (
                        "MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD",
                        "Intento de modificación sobre registro inmutable",
                    ),
                ],
                max_length=64,
            ),
        ),
    ]