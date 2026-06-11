"""Alertas operativas (RF-011, BR-04, BR-11)."""

from django.conf import settings
from django.db import models


class AlertType(models.TextChoices):
    LOW_STOCK = "LOW_STOCK", "Stock bajo mínimo"
    EXPIRATION_30 = "EXPIRATION_30", "Vencimiento en 30 días"
    EXPIRATION_60 = "EXPIRATION_60", "Vencimiento en 60 días"
    LOT_EXPIRED = "LOT_EXPIRED", "Lote vencido"
    COLD_CHAIN_MISSING = "COLD_CHAIN_MISSING", "Cadena de frío irregular"
    LOCATION_BLOCKED_WITH_STOCK = (
        "LOCATION_BLOCKED_WITH_STOCK",
        "Ubicación bloqueada con stock",
    )
    STOCK_MISMATCH = "STOCK_MISMATCH", "Desincronización stock vs ledger"
    STOCK_ZERO = "STOCK_ZERO", "Producto sin stock"


class AlertSeverity(models.TextChoices):
    CRITICAL = "CRITICAL", "Crítico"
    HIGH = "HIGH", "Alto"
    MEDIUM = "MEDIUM", "Medio"
    LOW = "LOW", "Bajo"
    INFO = "INFO", "Informativo"


class AlertCategory(models.TextChoices):
    STOCK = "STOCK", "Stock"
    EXPIRATION = "EXPIRATION", "Vencimiento"
    LOCATION = "LOCATION", "Ubicación"
    INTEGRITY = "INTEGRITY", "Integridad"
    BUSINESS = "BUSINESS", "Negocio"


# Mapa canónico tipo → (severidad, categoría)
ALERT_TYPE_DEFAULTS: dict[str, tuple[str, str]] = {
    AlertType.LOW_STOCK: (AlertSeverity.HIGH, AlertCategory.STOCK),
    AlertType.EXPIRATION_30: (AlertSeverity.CRITICAL, AlertCategory.EXPIRATION),
    AlertType.EXPIRATION_60: (AlertSeverity.HIGH, AlertCategory.EXPIRATION),
    AlertType.LOT_EXPIRED: (AlertSeverity.CRITICAL, AlertCategory.EXPIRATION),
    AlertType.COLD_CHAIN_MISSING: (AlertSeverity.HIGH, AlertCategory.LOCATION),
    AlertType.LOCATION_BLOCKED_WITH_STOCK: (AlertSeverity.HIGH, AlertCategory.LOCATION),
    AlertType.STOCK_MISMATCH: (AlertSeverity.CRITICAL, AlertCategory.INTEGRITY),
    AlertType.STOCK_ZERO: (AlertSeverity.MEDIUM, AlertCategory.STOCK),
}


class Alert(models.Model):
    """
    Alerta generada por el sistema (RF-011).

    `location` null: alerta global al producto (p. ej. vencimiento).
    """

    alert_type = models.CharField(max_length=64, choices=AlertType.choices)
    severity = models.CharField(
        max_length=16,
        choices=AlertSeverity.choices,
        default=AlertSeverity.MEDIUM,
    )
    category = models.CharField(
        max_length=16,
        choices=AlertCategory.choices,
        default=AlertCategory.STOCK,
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    lot = models.ForeignKey(
        "catalog.Lot",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    location = models.ForeignKey(
        "inventory.Location",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alerts_resolved",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("is_resolved", "alert_type")),
            models.Index(fields=("severity", "is_resolved")),
            models.Index(fields=("category", "is_resolved")),
            models.Index(fields=("is_resolved", "created_at")),
        ]

    def __str__(self) -> str:
        return f"{self.alert_type} ({self.product_id})"
