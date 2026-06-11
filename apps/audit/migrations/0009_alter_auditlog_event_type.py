# Generated migration — adds PASSWORD_CHANGED, PASSWORD_RESET_REQUESTED, PASSWORD_RESET_COMPLETED (RF-001)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0008_alter_auditlog_event_type"),
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
                    ("USER_ENABLED", "Usuario rehabilitado"),
                    ("MOVEMENT_CREATED", "Movimiento creado"),
                    ("ADJUSTMENT_CREATED", "Ajuste creado"),
                    ("RETURN_CREATED", "Devolución registrada"),
                    ("REPORT_GENERATED", "Reporte generado"),
                    ("PERMISSION_CHANGED", "Permisos modificados"),
                    ("STOCK_RECONSTRUCTED", "Stock reconstruido desde ledger"),
                    ("PRODUCT_CREATED", "Producto creado"),
                    ("PRODUCT_UPDATED", "Producto actualizado"),
                    ("PRODUCT_DEACTIVATED", "Producto desactivado"),
                    ("PRODUCT_ACTIVATED", "Producto reactivado"),
                    ("PRODUCT_PRICE_UPDATED", "Precios de producto actualizados"),
                    ("COMBO_CREATED", "Combo de productos creado"),
                    ("COMBO_UPDATED", "Combo de productos actualizado"),
                    ("COMBO_DEACTIVATED", "Combo de productos desactivado"),
                    ("COMBO_ACTIVATED", "Combo de productos reactivado"),
                    ("CATEGORY_CREATED", "Categoría de catálogo creada"),
                    ("CATEGORY_UPDATED", "Categoría de catálogo actualizada"),
                    ("CATEGORY_DEACTIVATED", "Categoría de catálogo desactivada"),
                    ("CATEGORY_ACTIVATED", "Categoría de catálogo reactivada"),
                    ("SUBCATEGORY_CREATED", "Subcategoría de catálogo creada"),
                    ("SUBCATEGORY_UPDATED", "Subcategoría de catálogo actualizada"),
                    ("SUBCATEGORY_DEACTIVATED", "Subcategoría de catálogo desactivada"),
                    ("SUBCATEGORY_ACTIVATED", "Subcategoría de catálogo reactivada"),
                    ("MOVEMENT_CORRECTED", "Movimiento corregido (BR-06)"),
                    ("RETURN_APPROVED", "Devolución aprobada"),
                    ("RETURN_REJECTED", "Devolución rechazada"),
                    ("ALERT_ACKNOWLEDGED", "Alerta reconocida"),
                    ("UNAUTHORIZED_ACCESS_ATTEMPT", "Intento de acceso no autorizado"),
                    (
                        "MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD",
                        "Intento de modificación sobre registro inmutable",
                    ),
                    ("INVOICE_GENERATED", "Factura generada"),
                    ("DISPATCH_WITH_PRICE_COMPLETED", "Despacho con precio completado"),
                    ("SUPPLIER_CREATED", "Proveedor creado"),
                    ("SUPPLIER_UPDATED", "Proveedor actualizado"),
                    ("SUPPLIER_DEACTIVATED", "Proveedor desactivado"),
                    ("SUPPLIER_ACTIVATED", "Proveedor reactivado"),
                    ("PURCHASE_ORDER_CREATED", "Orden de compra creada"),
                    ("PURCHASE_ORDER_CONFIRMED", "Orden de compra confirmada"),
                    ("PURCHASE_ORDER_CANCELLED", "Orden de compra cancelada"),
                    ("RECEPTION_CREATED", "Recepción de mercancía creada"),
                    ("RECEPTION_CONFIRMED", "Recepción de mercancía confirmada"),
                    ("RECEPTION_CANCELLED", "Recepción de mercancía cancelada"),
                    ("LOCATION_CREATED", "Ubicación creada"),
                    ("LOCATION_MODIFIED", "Ubicación modificada"),
                    ("WEBHOOK_ENDPOINT_CHANGED", "Endpoint webhook modificado"),
                    ("STOCK_THRESHOLD_UPDATED", "Umbral de stock actualizado"),
                    ("ALERT_RESOLVED", "Alerta resuelta"),
                    ("PURCHASE_ORDER_UPDATED", "Orden de compra actualizada"),
                    ("BATCH_JOB_EXECUTED", "Job batch ejecutado"),
                    ("PASSWORD_CHANGED", "Contraseña cambiada por el usuario"),
                    ("PASSWORD_RESET_REQUESTED", "Recuperación de contraseña solicitada"),
                    ("PASSWORD_RESET_COMPLETED", "Contraseña restablecida exitosamente"),
                ],
                max_length=64,
            ),
        ),
    ]
