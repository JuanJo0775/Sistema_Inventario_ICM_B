"""Modelos de webhooks (NEW-03): endpoints y cola de entregas."""

from django.conf import settings
from django.db import models

from shared.models import BaseModel, SoftDeleteModel


class WebhookEndpoint(BaseModel, SoftDeleteModel):
    """Destino externo suscrito a eventos del sistema."""

    url = models.URLField(max_length=500)
    secret = models.CharField(
        max_length=128,
        help_text="Clave compartida para firmar payloads con HMAC-SHA256.",
    )
    events = models.JSONField(
        default=list,
        help_text='Lista de event_types suscritos. Ej: ["STOCK_CRITICO"].',
    )
    is_active = models.BooleanField(default=True)
    max_retries = models.PositiveSmallIntegerField(default=3)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="webhook_endpoints",
    )

    class Meta:
        verbose_name = "Webhook Endpoint"
        verbose_name_plural = "Webhook Endpoints"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.url} ({len(self.events)} eventos)"


class WebhookDelivery(BaseModel):
    """Registro de un intento de entrega de un evento a un endpoint."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        DELIVERED = "DELIVERED", "Entregado"
        FAILED = "FAILED", "Fallido"

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    event_type = models.CharField(max_length=64)
    payload = models.JSONField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    response_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Webhook Delivery"
        verbose_name_plural = "Webhook Deliveries"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} → {self.endpoint.url} [{self.status}]"
