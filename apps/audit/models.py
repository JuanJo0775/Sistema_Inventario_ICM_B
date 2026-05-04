"""Auditoría central (RF-012, BR-10)."""

from __future__ import annotations

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
    MOVEMENT_CREATED = "MOVEMENT_CREATED", "Movimiento creado"
    ADJUSTMENT_CREATED = "ADJUSTMENT_CREATED", "Ajuste creado"
    RETURN_CREATED = "RETURN_CREATED", "Devolución registrada"
    REPORT_GENERATED = "REPORT_GENERATED", "Reporte generado"
    PERMISSION_CHANGED = "PERMISSION_CHANGED", "Permisos modificados"
    STOCK_RECONSTRUCTED = "STOCK_RECONSTRUCTED", "Stock reconstruido desde ledger"
    # Extensiones usadas por servicios actuales (misma familia RF-012)
    PRODUCT_CREATED = "PRODUCT_CREATED", "Producto creado"
    MOVEMENT_CORRECTED = "MOVEMENT_CORRECTED", "Movimiento corregido (BR-06)"
    RETURN_APPROVED = "RETURN_APPROVED", "Devolución aprobada"
    RETURN_REJECTED = "RETURN_REJECTED", "Devolución rechazada"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED", "Alerta reconocida"
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT", "Intento de acceso no autorizado"
    MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD = (
        "MODIFICATION_ATTEMPT_ON_IMMUTABLE_RECORD",
        "Intento de modificación sobre registro inmutable",
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

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at}"
