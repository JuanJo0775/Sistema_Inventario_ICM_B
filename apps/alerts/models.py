"""Alertas operativas (RF-011, BR-04, BR-11)."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class AlertType(models.TextChoices):
    LOW_STOCK = "LOW_STOCK", "Stock bajo mínimo"
    EXPIRATION_30 = "EXPIRATION_30", "Vencimiento en 30 días"
    EXPIRATION_60 = "EXPIRATION_60", "Vencimiento en 60 días"
    COLD_CHAIN_MISSING = "COLD_CHAIN_MISSING", "Cadena de frío irregular"
    STOCK_MISMATCH = "STOCK_MISMATCH", "Desincronización stock vs ledger"


class Alert(models.Model):
    """
    Alerta generada por el sistema (RF-011).

    `location` null: alerta global al producto (p. ej. vencimiento).
    """

    alert_type = models.CharField(max_length=64, choices=AlertType.choices)
    product = models.ForeignKey(
        "catalog.Product",
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
        ]

    def __str__(self) -> str:
        return f"{self.alert_type} ({self.product_id})"
