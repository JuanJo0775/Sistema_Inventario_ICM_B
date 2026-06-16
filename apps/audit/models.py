"""Auditoría central (RF-012, BR-10)."""

import uuid

from django.conf import settings
from django.db import models


class AuditEventType(models.TextChoices):
    """Tipos de evento auditados (RF-012); valores adicionales para trazabilidad operativa."""

    LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login exitoso"
    LOGIN_FAILED = "LOGIN_FAILED", "Login fallido"
    LOGOUT = "LOGOUT", "Cierre de sesión"
    USER_CREATED = "USER_CREATED", "Usuario creado"
    USER_UPDATED = "USER_UPDATED", "Usuario actualizado"
    USER_DISABLED = "USER_DISABLED", "Usuario deshabilitado"
    USER_ENABLED = "USER_ENABLED", "Usuario rehabilitado"
    MOVEMENT_CREATED = "MOVEMENT_CREATED", "Movimiento creado"
    ADJUSTMENT_CREATED = "ADJUSTMENT_CREATED", "Ajuste creado"
    RETURN_CREATED = "RETURN_CREATED", "Devolución registrada"
    REPORT_GENERATED = "REPORT_GENERATED", "Reporte generado"
    PERMISSION_CHANGED = "PERMISSION_CHANGED", "Permisos modificados"
    STOCK_RECONSTRUCTED = "STOCK_RECONSTRUCTED", "Stock reconstruido desde ledger"
    # Extensiones usadas por servicios actuales (misma familia RF-012)
    PRODUCT_CREATED = "PRODUCT_CREATED", "Producto creado"
    PRODUCT_UPDATED = "PRODUCT_UPDATED", "Producto actualizado"
    PRODUCT_DEACTIVATED = "PRODUCT_DEACTIVATED", "Producto desactivado"
    PRODUCT_ACTIVATED = "PRODUCT_ACTIVATED", "Producto reactivado"
    PRODUCT_PRICE_UPDATED = "PRODUCT_PRICE_UPDATED", "Precios de producto actualizados"
    # Soft delete — existencia lógica
    PRODUCT_SOFT_DELETED = "PRODUCT_SOFT_DELETED", "Producto eliminado lógicamente"
    PRODUCT_RESTORED = "PRODUCT_RESTORED", "Producto restaurado"
    # Disponibilidad para asignación
    PRODUCT_DISABLED = "PRODUCT_DISABLED", "Producto desactivado para asignación"
    PRODUCT_ENABLED = "PRODUCT_ENABLED", "Producto reactivado para asignación"
    COMBO_CREATED = "COMBO_CREATED", "Combo de productos creado"
    COMBO_UPDATED = "COMBO_UPDATED", "Combo de productos actualizado"
    COMBO_DEACTIVATED = "COMBO_DEACTIVATED", "Combo de productos desactivado"
    COMBO_ACTIVATED = "COMBO_ACTIVATED", "Combo de productos reactivado"
    # Soft delete — existencia lógica
    COMBO_SOFT_DELETED = "COMBO_SOFT_DELETED", "Combo eliminado lógicamente"
    COMBO_RESTORED = "COMBO_RESTORED", "Combo restaurado"
    CATEGORY_CREATED = "CATEGORY_CREATED", "Categoría de catálogo creada"
    CATEGORY_UPDATED = "CATEGORY_UPDATED", "Categoría de catálogo actualizada"
    CATEGORY_DEACTIVATED = "CATEGORY_DEACTIVATED", "Categoría de catálogo desactivada"
    CATEGORY_ACTIVATED = "CATEGORY_ACTIVATED", "Categoría de catálogo reactivada"
    # Soft delete — existencia lógica
    CATEGORY_SOFT_DELETED = "CATEGORY_SOFT_DELETED", "Categoría eliminada lógicamente"
    CATEGORY_RESTORED = "CATEGORY_RESTORED", "Categoría restaurada"
    # Disponibilidad para asignación
    CATEGORY_DISABLED = (
        "CATEGORY_DISABLED",
        "Categoría desactivada para nuevas asignaciones",
    )
    CATEGORY_ENABLED = (
        "CATEGORY_ENABLED",
        "Categoría reactivada para nuevas asignaciones",
    )
    BRAND_CREATED = "BRAND_CREATED", "Marca de catálogo creada"
    BRAND_UPDATED = "BRAND_UPDATED", "Marca de catálogo actualizada"
    BRAND_DEACTIVATED = "BRAND_DEACTIVATED", "Marca de catálogo desactivada"
    BRAND_ACTIVATED = "BRAND_ACTIVATED", "Marca de catálogo reactivada"
    # Soft delete — existencia lógica
    BRAND_SOFT_DELETED = "BRAND_SOFT_DELETED", "Marca eliminada lógicamente"
    BRAND_RESTORED = "BRAND_RESTORED", "Marca restaurada"
    # Disponibilidad para asignación
    BRAND_DISABLED = "BRAND_DISABLED", "Marca desactivada para nuevas asignaciones"
    BRAND_ENABLED = "BRAND_ENABLED", "Marca reactivada para nuevas asignaciones"
    SUBCATEGORY_CREATED = "SUBCATEGORY_CREATED", "Subcategoría de catálogo creada"
    SUBCATEGORY_UPDATED = "SUBCATEGORY_UPDATED", "Subcategoría de catálogo actualizada"
    SUBCATEGORY_DEACTIVATED = (
        "SUBCATEGORY_DEACTIVATED",
        "Subcategoría de catálogo desactivada",
    )
    SUBCATEGORY_ACTIVATED = (
        "SUBCATEGORY_ACTIVATED",
        "Subcategoría de catálogo reactivada",
    )
    MOVEMENT_CORRECTED = "MOVEMENT_CORRECTED", "Movimiento corregido (BR-06)"
    RETURN_APPROVED = "RETURN_APPROVED", "Devolución aprobada"
    RETURN_REJECTED = "RETURN_REJECTED", "Devolución rechazada"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED", "Alerta reconocida"
    UNAUTHORIZED_ACCESS_ATTEMPT = (
        "UNAUTHORIZED_ACCESS_ATTEMPT",
        "Intento de acceso no autorizado",
    )
    MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD = (
        "MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD",
        "Intento de modificación sobre registro inmutable",
    )
    INVOICE_GENERATED = "INVOICE_GENERATED", "Factura generada"
    INVOICE_VOIDED = "INVOICE_VOIDED", "Factura anulada"
    COMPANY_INFO_UPDATED = "COMPANY_INFO_UPDATED", "Datos de empresa actualizados"
    DISPATCH_WITH_PRICE_COMPLETED = (
        "DISPATCH_WITH_PRICE_COMPLETED",
        "Despacho con precio completado",
    )
    # Módulo de compras (Proveedores, OC, Recepción)
    SUPPLIER_CREATED = "SUPPLIER_CREATED", "Proveedor creado"
    SUPPLIER_UPDATED = "SUPPLIER_UPDATED", "Proveedor actualizado"
    SUPPLIER_DEACTIVATED = "SUPPLIER_DEACTIVATED", "Proveedor desactivado"
    SUPPLIER_ACTIVATED = "SUPPLIER_ACTIVATED", "Proveedor reactivado"
    # Supplier — Soft delete
    SUPPLIER_SOFT_DELETED = "SUPPLIER_SOFT_DELETED", "Proveedor eliminado lógicamente"
    SUPPLIER_RESTORED = "SUPPLIER_RESTORED", "Proveedor restaurado"
    # Supplier — Disponibilidad
    SUPPLIER_DISABLED = "SUPPLIER_DISABLED", "Proveedor desactivado para nuevas OC"
    SUPPLIER_ENABLED = "SUPPLIER_ENABLED", "Proveedor reactivado para nuevas OC"
    # Webhooks — Soft delete
    WEBHOOK_ENDPOINT_SOFT_DELETED = (
        "WEBHOOK_ENDPOINT_SOFT_DELETED",
        "Endpoint webhook eliminado lógicamente",
    )
    WEBHOOK_ENDPOINT_RESTORED = (
        "WEBHOOK_ENDPOINT_RESTORED",
        "Endpoint webhook restaurado",
    )
    # Webhooks — Disponibilidad
    WEBHOOK_ENDPOINT_DISABLED = (
        "WEBHOOK_ENDPOINT_DISABLED",
        "Endpoint webhook desactivado para recepción",
    )
    WEBHOOK_ENDPOINT_ENABLED = (
        "WEBHOOK_ENDPOINT_ENABLED",
        "Endpoint webhook reactivado para recepción",
    )
    # Storage — Creación / edición
    STORAGE_TYPE_CREATED = "STORAGE_TYPE_CREATED", "Tipo de almacenamiento creado"
    STORAGE_TYPE_UPDATED = "STORAGE_TYPE_UPDATED", "Tipo de almacenamiento actualizado"
    STORAGE_TEMPLATE_CREATED = (
        "STORAGE_TEMPLATE_CREATED",
        "Plantilla de almacenamiento creada",
    )
    STORAGE_TEMPLATE_UPDATED = (
        "STORAGE_TEMPLATE_UPDATED",
        "Plantilla de almacenamiento actualizada",
    )
    # Storage — Soft delete
    STORAGE_TYPE_SOFT_DELETED = (
        "STORAGE_TYPE_SOFT_DELETED",
        "Tipo de almacenamiento eliminado lógicamente",
    )
    STORAGE_TYPE_RESTORED = "STORAGE_TYPE_RESTORED", "Tipo de almacenamiento restaurado"
    STORAGE_TEMPLATE_SOFT_DELETED = (
        "STORAGE_TEMPLATE_SOFT_DELETED",
        "Plantilla de almacenamiento eliminada lógicamente",
    )
    STORAGE_TEMPLATE_RESTORED = (
        "STORAGE_TEMPLATE_RESTORED",
        "Plantilla de almacenamiento restaurada",
    )
    # Storage — Disponibilidad
    STORAGE_TYPE_DISABLED = (
        "STORAGE_TYPE_DISABLED",
        "Tipo de almacenamiento desactivado para asignación",
    )
    STORAGE_TYPE_ENABLED = (
        "STORAGE_TYPE_ENABLED",
        "Tipo de almacenamiento reactivado para asignación",
    )
    STORAGE_TEMPLATE_DISABLED = (
        "STORAGE_TEMPLATE_DISABLED",
        "Plantilla de almacenamiento desactivada para asignación",
    )
    STORAGE_TEMPLATE_ENABLED = (
        "STORAGE_TEMPLATE_ENABLED",
        "Plantilla de almacenamiento reactivada para asignación",
    )
    PURCHASE_ORDER_CREATED = "PURCHASE_ORDER_CREATED", "Orden de compra creada"
    PURCHASE_ORDER_CONFIRMED = "PURCHASE_ORDER_CONFIRMED", "Orden de compra confirmada"
    PURCHASE_ORDER_CANCELLED = "PURCHASE_ORDER_CANCELLED", "Orden de compra cancelada"
    RECEPTION_CREATED = "RECEPTION_CREATED", "Recepción de mercancía creada"
    RECEPTION_CONFIRMED = "RECEPTION_CONFIRMED", "Recepción de mercancía confirmada"
    RECEPTION_CANCELLED = "RECEPTION_CANCELLED", "Recepción de mercancía cancelada"
    # Ubicaciones — entidad de negocio con operaciones protegidas
    LOCATION_CREATED = "LOCATION_CREATED", "Ubicación creada"
    LOCATION_MODIFIED = "LOCATION_MODIFIED", "Ubicación modificada"
    # Soft delete — existencia lógica
    LOCATION_SOFT_DELETED = "LOCATION_SOFT_DELETED", "Ubicación eliminada lógicamente"
    LOCATION_RESTORED = "LOCATION_RESTORED", "Ubicación restaurada"
    # Webhook endpoints — seguridad: vector de exfiltración
    WEBHOOK_ENDPOINT_CHANGED = "WEBHOOK_ENDPOINT_CHANGED", "Endpoint webhook modificado"
    # Umbrales de reorden — afecta comportamiento operativo
    STOCK_THRESHOLD_UPDATED = "STOCK_THRESHOLD_UPDATED", "Umbral de stock actualizado"
    # Alertas — accountability de resolución
    ALERT_RESOLVED = "ALERT_RESOLVED", "Alerta resuelta"
    # Órdenes de compra — documento financiero
    PURCHASE_ORDER_UPDATED = "PURCHASE_ORDER_UPDATED", "Orden de compra actualizada"
    # Procesos batch — accountability de jobs automáticos
    BATCH_JOB_EXECUTED = "BATCH_JOB_EXECUTED", "Job batch ejecutado"
    # Contraseñas — self-service y recuperación (RF-001)
    PASSWORD_CHANGED = "PASSWORD_CHANGED", "Contraseña cambiada por el usuario"
    PASSWORD_RESET_REQUESTED = (
        "PASSWORD_RESET_REQUESTED",
        "Recuperación de contraseña solicitada",
    )
    PASSWORD_RESET_COMPLETED = (
        "PASSWORD_RESET_COMPLETED",
        "Contraseña restablecida exitosamente",
    )


class AuditLog(models.Model):
    """
    Registro inmutable de auditoría (RF-012, BR-10).

    Sin `updated_at` por diseño inmutable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64, choices=AuditEventType.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    movement = models.ForeignKey(
        "movements.Movement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de auditoría"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("user", "created_at")),
            models.Index(fields=("event_type", "created_at")),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from shared.exceptions import ImmutableRecordError

            raise ImmutableRecordError("AuditLog records cannot be modified.")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at}"


class AuditLogArchive(models.Model):
    """Tabla de archivo histórico de AuditLog (M-02).

    Misma estructura que AuditLog + campo archived_at.
    Registros movidos por archive_old_audit_logs management command.
    """

    id = models.UUIDField(primary_key=True, editable=False)
    event_type = models.CharField(max_length=64)
    user_id = models.IntegerField(null=True, blank=True)
    movement_id = models.UUIDField(null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField()
    archived_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Auditoría (Archivo)"
        verbose_name_plural = "Logs de auditoría (Archivo)"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("created_at",)),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from shared.exceptions import ImmutableRecordError

            raise ImmutableRecordError("AuditLogArchive records cannot be modified.")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"[ARCHIVO] {self.event_type} @ {self.created_at}"
