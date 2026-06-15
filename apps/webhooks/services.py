"""Servicios de webhooks: encolar y entregar eventos (NEW-03)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.request
import warnings
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.webhooks.models import WebhookDelivery, WebhookEndpoint
from shared.utils.db import get_for_update_or_404

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
        ep
        for ep in WebhookEndpoint.objects.filter(is_active=True)
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

    # Reclamar deliveries en una transacción corta: leer IDs bajo lock y empujar
    # next_retry_at al futuro para que otro worker no los reencole mientras procesamos.
    with transaction.atomic():
        pending_ids = list(
            WebhookDelivery.objects.select_for_update(skip_locked=True)
            .filter(
                status=WebhookDelivery.Status.PENDING,
                next_retry_at__lte=now,
            )
            .values_list("id", flat=True)[:batch_size]
        )
        if pending_ids:
            WebhookDelivery.objects.filter(id__in=pending_ids).update(
                next_retry_at=now + timedelta(hours=1)
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


def test_webhook_endpoint(
    endpoint: WebhookEndpoint,
    event_type: str = "TEST",
    payload: dict | None = None,
) -> dict:
    """Sends a test delivery without persisting to the database (MEDIA-22)."""
    delivery = WebhookDelivery(
        endpoint=endpoint,
        event_type=event_type,
        payload=payload or {},
        status=WebhookDelivery.Status.PENDING,
        next_retry_at=timezone.now(),
    )
    _attempt_delivery(delivery, persist=False)
    return {"status": delivery.status, "response_code": delivery.response_code}


def _attempt_delivery(delivery: WebhookDelivery, *, persist: bool = True) -> None:
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
        scheme = urlparse(endpoint.url).scheme
        if scheme not in ("http", "https"):
            raise ValueError(f"Unsupported URL scheme: {scheme}")
        # nosemgrep
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 — scheme validated above
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
        if persist:
            delivery.save(
                update_fields=[
                    "status",
                    "attempts",
                    "last_attempt_at",
                    "next_retry_at",
                    "response_code",
                    "response_body",
                    "updated_at",
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


# =============================================================================
# Soft Delete / Disponibilidad — WebhookEndpoint
# =============================================================================


@transaction.atomic
def soft_delete_webhook_endpoint(
    executor: Any,
    endpoint_id: Any,
    *,
    request: Any = None,
) -> None:
    """Elimina lógicamente un endpoint de webhook (soft delete)."""
    endpoint = get_for_update_or_404(WebhookEndpoint.objects, pk=endpoint_id)
    endpoint.deleted_at = timezone.now()
    endpoint.is_active = False  # sync legado
    endpoint.save(update_fields=["deleted_at", "is_active", "updated_at"])
    log_event(
        AuditEventType.WEBHOOK_ENDPOINT_SOFT_DELETED,
        description=f"Endpoint webhook eliminado lógicamente: {endpoint.url}",
        user=executor,
        request=request,
        detail={"endpoint_id": str(endpoint.id), "url": endpoint.url},
    )


@transaction.atomic
def restore_webhook_endpoint(
    executor: Any,
    endpoint_id: Any,
    *,
    request: Any = None,
) -> WebhookEndpoint:
    """Restaura un endpoint de webhook previamente eliminado lógicamente."""
    endpoint = get_for_update_or_404(WebhookEndpoint.objects, pk=endpoint_id)
    endpoint.deleted_at = None
    endpoint.is_active = True  # sync legado
    endpoint.save(update_fields=["deleted_at", "is_active", "updated_at"])
    log_event(
        AuditEventType.WEBHOOK_ENDPOINT_RESTORED,
        description=f"Endpoint webhook restaurado: {endpoint.url}",
        user=executor,
        request=request,
        detail={"endpoint_id": str(endpoint.id), "url": endpoint.url},
    )
    return endpoint


@transaction.atomic
def disable_webhook_endpoint(
    executor: Any,
    endpoint_id: Any,
    *,
    request: Any = None,
) -> None:
    """Desactiva un endpoint para recepción de eventos (no borra, solo pausa)."""
    endpoint = get_for_update_or_404(WebhookEndpoint.objects, pk=endpoint_id)
    if endpoint.deleted_at is not None:
        raise ValueError(
            "No se puede desactivar un endpoint archivado; restáurelo primero."
        )
    endpoint.is_active = False
    endpoint.save(update_fields=["is_active", "updated_at"])
    log_event(
        AuditEventType.WEBHOOK_ENDPOINT_DISABLED,
        description=f"Endpoint webhook desactivado: {endpoint.url}",
        user=executor,
        request=request,
        detail={"endpoint_id": str(endpoint.id), "url": endpoint.url},
    )


@transaction.atomic
def enable_webhook_endpoint(
    executor: Any,
    endpoint_id: Any,
    *,
    request: Any = None,
) -> WebhookEndpoint:
    """Reactiva un endpoint para recepción de eventos."""
    endpoint = get_for_update_or_404(WebhookEndpoint.objects, pk=endpoint_id)
    if endpoint.deleted_at is not None:
        raise ValueError(
            "No se puede activar un endpoint archivado; restáurelo primero."
        )
    endpoint.is_active = True
    endpoint.save(update_fields=["is_active", "updated_at"])
    log_event(
        AuditEventType.WEBHOOK_ENDPOINT_ENABLED,
        description=f"Endpoint webhook reactivado: {endpoint.url}",
        user=executor,
        request=request,
        detail={"endpoint_id": str(endpoint.id), "url": endpoint.url},
    )
    return endpoint


# =============================================================================
# Wrappers legacy (deprecados)
# =============================================================================


@transaction.atomic
def deactivate_webhook_endpoint(
    executor: Any,
    endpoint_id: Any,
    *,
    request: Any = None,
) -> None:
    """Legacy wrapper: desactiva endpoint -> soft_delete_webhook_endpoint."""
    warnings.warn(
        "deactivate_webhook_endpoint is deprecated; use soft_delete_webhook_endpoint",
        DeprecationWarning,
        stacklevel=2,
    )
    soft_delete_webhook_endpoint(executor, endpoint_id, request=request)


@transaction.atomic
def activate_webhook_endpoint(
    executor: Any,
    endpoint_id: Any,
    *,
    request: Any = None,
) -> WebhookEndpoint:
    """Legacy wrapper: reactiva endpoint -> restore_webhook_endpoint."""
    warnings.warn(
        "activate_webhook_endpoint is deprecated; use restore_webhook_endpoint",
        DeprecationWarning,
        stacklevel=2,
    )
    return restore_webhook_endpoint(executor, endpoint_id, request=request)
