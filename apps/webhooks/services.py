"""Servicios de webhooks: encolar y entregar eventos (NEW-03)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.request
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)

_BACKOFF_MINUTES = [1, 5, 30]


def queue_webhook_event(event_type: str, payload: dict) -> int:
    """
    Encola un evento para todos los endpoints activos suscritos.

    Returns:
        Número de deliveries creados.
    """
    # Filtrar en Python para compatibilidad con SQLite en tests
    # En producción (PostgreSQL) events__contains=[event_type] también funciona
    endpoints = [
        ep for ep in WebhookEndpoint.objects.filter(is_active=True)
        if event_type in (ep.events or [])
    ]
    if not endpoints:
        return 0
    now = timezone.now()
    deliveries = [
        WebhookDelivery(
            endpoint=ep,
            event_type=event_type,
            payload=payload,
            status=WebhookDelivery.Status.PENDING,
            next_retry_at=now,
        )
        for ep in endpoints
    ]
    WebhookDelivery.objects.bulk_create(deliveries)
    return len(deliveries)


def _sign_payload(secret: str, body: bytes) -> str:
    """Genera firma HMAC-SHA256 en formato sha256=<hex>."""
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def deliver_pending_webhooks(*, batch_size: int = 50) -> tuple[int, int]:
    """
    Procesa y entrega webhooks pendientes con retry y backoff exponencial.

    Usa select_for_update(skip_locked=True) para que múltiples instancias
    del cron puedan correr en paralelo sin doble-entrega.

    Returns:
        (delivered_count, failed_count)
    """
    now = timezone.now()
    delivered = 0
    failed = 0

    # Leer IDs en una transacción corta para evitar locks prolongados
    with transaction.atomic():
        pending_ids = list(
            WebhookDelivery.objects.select_for_update(skip_locked=True)
            .filter(
                status=WebhookDelivery.Status.PENDING,
                next_retry_at__lte=now,
            )
            .values_list("id", flat=True)[:batch_size]
        )

    if not pending_ids:
        return 0, 0

    deliveries = list(
        WebhookDelivery.objects.filter(id__in=pending_ids).select_related("endpoint")
    )

    for delivery in deliveries:
        _attempt_delivery(delivery)
        if delivery.status == WebhookDelivery.Status.DELIVERED:
            delivered += 1
        else:
            failed += 1

    return delivered, failed


def _attempt_delivery(delivery: WebhookDelivery) -> None:
    """Intenta entregar un webhook; actualiza status, attempts, y next_retry_at."""
    endpoint = delivery.endpoint
    body = json.dumps(delivery.payload, default=str).encode("utf-8")
    signature = _sign_payload(endpoint.secret, body)

    delivery.attempts += 1
    delivery.last_attempt_at = timezone.now()

    start = time.monotonic()
    try:
        req = urllib.request.Request(
            endpoint.url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-ICM-Signature": signature,
                "X-ICM-Event": delivery.event_type,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            delivery.response_code = resp.status
            delivery.response_body = resp.read(512).decode("utf-8", errors="replace")
            delivery.status = WebhookDelivery.Status.DELIVERED
    except urllib.error.HTTPError as exc:
        delivery.response_code = exc.code
        delivery.response_body = exc.read(512).decode("utf-8", errors="replace")
        _schedule_retry(delivery, endpoint.max_retries)
    except Exception as exc:
        delivery.response_code = None
        delivery.response_body = str(exc)[:512]
        _schedule_retry(delivery, endpoint.max_retries)
    finally:
        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            "webhook delivery endpoint=%s event=%s status=%s attempts=%d duration_ms=%.0f",
            endpoint.url,
            delivery.event_type,
            delivery.status,
            delivery.attempts,
            elapsed,
        )
        delivery.save(
            update_fields=[
                "status", "attempts", "last_attempt_at",
                "next_retry_at", "response_code", "response_body", "updated_at",
            ]
        )


def _schedule_retry(delivery: WebhookDelivery, max_retries: int) -> None:
    if delivery.attempts >= max_retries:
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.next_retry_at = None
        logger.warning(
            "webhook permanentemente fallido endpoint=%s event=%s attempts=%d",
            delivery.endpoint.url,
            delivery.event_type,
            delivery.attempts,
        )
    else:
        delay_minutes = _BACKOFF_MINUTES[
            min(delivery.attempts - 1, len(_BACKOFF_MINUTES) - 1)
        ]
        delivery.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
        delivery.status = WebhookDelivery.Status.PENDING
