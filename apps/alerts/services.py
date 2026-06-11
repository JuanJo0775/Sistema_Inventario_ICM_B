"""Alertas proactivas (RF-011)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.alerts.models import (
    ALERT_TYPE_DEFAULTS,
    Alert,
    AlertCategory,
    AlertSeverity,
    AlertType,
)
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.authentication.models import RoleChoices
from apps.catalog.models import Lot, Product
from apps.inventory.models import Location, StockByLocation
from shared.exceptions import UnauthorizedDomainActionError

if TYPE_CHECKING:
    from apps.authentication.models import User


def _severity_and_category(
    alert_type: str,
    *,
    per_location: bool = False,
) -> tuple[str, str]:
    """Devuelve (severity, category) canónicos para un AlertType."""
    severity, category = ALERT_TYPE_DEFAULTS.get(
        alert_type, (AlertSeverity.MEDIUM, AlertCategory.STOCK)
    )
    if alert_type == AlertType.LOW_STOCK and per_location:
        severity = AlertSeverity.MEDIUM
    return severity, category


def sync_stock_alerts_for_product(product_id: UUID, *, user=None) -> None:
    """
    RF-011 — Alerta de stock bajo según `Product.reorder_point`.

    Debe ejecutarse tras movimientos que alteren stock consolidado.
    """
    agg = StockByLocation.objects.filter(product_id=product_id).aggregate(
        s=Sum("current_stock")
    )
    total_qty = int(agg["s"] or 0)
    product = Product.objects.get(pk=product_id)
    threshold = int(product.reorder_point)

    open_alerts = Alert.objects.filter(
        product_id=product_id,
        alert_type=AlertType.LOW_STOCK,
        location__isnull=True,
        is_resolved=False,
    )
    if total_qty <= threshold:
        if not open_alerts.exists():
            severity, category = _severity_and_category(AlertType.LOW_STOCK)
            Alert.objects.create(
                product_id=product_id,
                alert_type=AlertType.LOW_STOCK,
                severity=severity,
                category=category,
                location=None,
                message=f"Stock total {total_qty} en o por debajo del umbral {threshold}.",
            )
            try:
                from apps.webhooks.services import queue_webhook_event

                queue_webhook_event(
                    AlertType.LOW_STOCK,
                    {
                        "product_id": str(product_id),
                        "total_qty": total_qty,
                        "threshold": threshold,
                    },
                )
            except Exception:
                pass
    else:
        rb = (
            user
            if user is not None and getattr(user, "is_authenticated", False)
            else None
        )
        open_alerts.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=rb)


def _sync_lot_expiry_alert(lot: Lot, *, user=None) -> None:
    today = timezone.now().date()
    days_left = (lot.expiration_date - today).days
    resolved_by = (
        user if user is not None and getattr(user, "is_authenticated", False) else None
    )

    if days_left > 60:
        Alert.objects.filter(
            product_id=lot.product_id,
            lot_id=lot.id,
            alert_type__in=(AlertType.EXPIRATION_30, AlertType.EXPIRATION_60),
            is_resolved=False,
        ).update(is_resolved=True, resolved_at=timezone.now(), resolved_by=resolved_by)
        return

    alert_type = AlertType.EXPIRATION_60 if days_left > 30 else AlertType.EXPIRATION_30
    message = (
        f"El lote {lot.code} vence en {days_left} días (ventana 60)."
        if alert_type == AlertType.EXPIRATION_60
        else f"El lote {lot.code} vence en {days_left} días (ventana 30)."
    )
    severity, category = _severity_and_category(alert_type)
    alert, created = Alert.objects.get_or_create(
        product_id=lot.product_id,
        lot_id=lot.id,
        alert_type=alert_type,
        location=None,
        defaults={
            "message": message,
            "is_resolved": False,
            "severity": severity,
            "category": category,
        },
    )
    if not created:
        alert.message = message
        alert.is_resolved = False
        alert.resolved_at = None
        alert.resolved_by = None
        alert.save(
            update_fields=["message", "is_resolved", "resolved_at", "resolved_by"]
        )


def sync_expiry_alerts_for_product(product_id: UUID, *, user=None) -> None:
    """RF-011 — Alertas de vencimiento a 60 y 30 días según lotes o `Product.expiration_date`."""
    product = Product.objects.filter(pk=product_id).first()
    if not product:
        return

    lots = list(product.lots.all())
    if lots:
        for lot in lots:
            _sync_lot_expiry_alert(lot, user=user)
        return

    if not product.expiration_date:
        return

    today = timezone.now().date()
    days_left = (product.expiration_date - today).days
    if days_left > 60:
        return
    if 30 < days_left <= 60:
        if not Alert.objects.filter(
            product_id=product_id,
            lot__isnull=True,
            alert_type=AlertType.EXPIRATION_60,
            location__isnull=True,
            is_resolved=False,
        ).exists():
            severity, category = _severity_and_category(AlertType.EXPIRATION_60)
            Alert.objects.create(
                product_id=product_id,
                lot=None,
                alert_type=AlertType.EXPIRATION_60,
                severity=severity,
                category=category,
                location=None,
                message=f"El producto vence en {days_left} días (ventana 60).",
            )
    if days_left <= 30:
        # Cerrar EXPIRATION_60 si quedó abierta al cruzar la ventana de 30 días
        Alert.objects.filter(
            product_id=product_id,
            lot__isnull=True,
            alert_type=AlertType.EXPIRATION_60,
            location__isnull=True,
            is_resolved=False,
        ).update(is_resolved=True, resolved_at=timezone.now())
        severity, category = _severity_and_category(AlertType.EXPIRATION_30)
        alert, _created = Alert.objects.get_or_create(
            product_id=product_id,
            lot=None,
            alert_type=AlertType.EXPIRATION_30,
            location=None,
            defaults={
                "message": f"El producto vence en {days_left} días (ventana 30).",
                "is_resolved": False,
                "severity": severity,
                "category": category,
            },
        )
        if not _created:
            alert.message = f"El producto vence en {days_left} días (ventana 30)."
            alert.is_resolved = False
            alert.resolved_at = None
            alert.resolved_by = None
            alert.save(
                update_fields=["message", "is_resolved", "resolved_at", "resolved_by"]
            )


def check_and_create_minimum_stock_alert(
    product: Product, location: Location
) -> Alert | None:
    """
    RF-011, BR-11 — Alerta de stock bajo por producto y ubicación (sin duplicados activos).

    Usa `location_reorder_point` si está definido; si no, `reorder_point` del producto.
    """
    row = (
        StockByLocation.objects.filter(product_id=product.id, location_id=location.id)
        .select_related("product")
        .first()
    )
    qty = int(row.current_stock) if row else 0
    # NEW-02: umbral local si está definido, global del producto como fallback
    threshold = (
        row.effective_reorder_point
        if row
        else int(getattr(product, "reorder_point", 0) or 0)
    )
    if qty > threshold:
        return None
    if Alert.objects.filter(
        product_id=product.id,
        location_id=location.id,
        alert_type=AlertType.LOW_STOCK,
        is_resolved=False,
    ).exists():
        return None
    severity, category = _severity_and_category(AlertType.LOW_STOCK, per_location=True)
    return Alert.objects.create(
        product_id=product.id,
        location_id=location.id,
        alert_type=AlertType.LOW_STOCK,
        severity=severity,
        category=category,
        message=f"Stock en {location.code} ({qty}) en o por debajo del umbral {threshold}.",
    )


def sync_lot_expired_alerts(product_id: UUID) -> None:
    """Alerta CRITICAL por cada lote del producto cuya expiration_date ya pasó."""
    today = timezone.now().date()
    expired_lots = Lot.objects.filter(product_id=product_id, expiration_date__lt=today)
    severity, category = _severity_and_category(AlertType.LOT_EXPIRED)
    for lot in expired_lots:
        alert, created = Alert.objects.get_or_create(
            product_id=product_id,
            lot_id=lot.id,
            alert_type=AlertType.LOT_EXPIRED,
            location=None,
            defaults={
                "message": f"El lote {lot.code} venció el {lot.expiration_date}.",
                "is_resolved": False,
                "severity": severity,
                "category": category,
            },
        )
        if not created and alert.is_resolved:
            alert.is_resolved = False
            alert.resolved_at = None
            alert.resolved_by = None
            alert.save(update_fields=["is_resolved", "resolved_at", "resolved_by"])

    # Resolver alertas LOT_EXPIRED de lotes que ya no están vencidos (edge case)
    Alert.objects.filter(
        product_id=product_id,
        alert_type=AlertType.LOT_EXPIRED,
        is_resolved=False,
    ).exclude(lot_id__in=expired_lots.values_list("id", flat=True)).update(
        is_resolved=True, resolved_at=timezone.now()
    )


def sync_cold_chain_alerts(product: Product, location: Location) -> None:
    """Alerta si un producto con cadena de frío se almacena en ubicación no acondicionada."""
    if not product.requires_cold_chain:
        return

    storage_type = location.storage_type
    has_cold_chain = storage_type is not None and storage_type.category == "cold_chain"

    open_alert = Alert.objects.filter(
        product_id=product.id,
        location_id=location.id,
        alert_type=AlertType.COLD_CHAIN_MISSING,
        is_resolved=False,
    )
    if has_cold_chain:
        open_alert.update(is_resolved=True, resolved_at=timezone.now())
        return

    if not open_alert.exists():
        severity, category = _severity_and_category(AlertType.COLD_CHAIN_MISSING)
        Alert.objects.create(
            product_id=product.id,
            location_id=location.id,
            alert_type=AlertType.COLD_CHAIN_MISSING,
            severity=severity,
            category=category,
            message=(
                f"Producto {product.sku} requiere cadena de frío "
                f"pero la ubicación '{location.code}' no es un almacenamiento refrigerado."
            ),
        )


def sync_stock_zero_alerts(product_id: UUID) -> None:
    """Alerta cuando un producto activo no tiene stock en ninguna ubicación."""
    product = Product.objects.filter(pk=product_id, is_active=True).first()
    if not product:
        return

    agg = StockByLocation.objects.filter(product_id=product_id).aggregate(
        s=Sum("current_stock")
    )
    total_qty = int(agg["s"] or 0)

    open_alerts = Alert.objects.filter(
        product_id=product_id,
        alert_type=AlertType.STOCK_ZERO,
        is_resolved=False,
    )
    if total_qty == 0:
        if not open_alerts.exists():
            severity, category = _severity_and_category(AlertType.STOCK_ZERO)
            Alert.objects.create(
                product_id=product_id,
                alert_type=AlertType.STOCK_ZERO,
                severity=severity,
                category=category,
                location=None,
                message=f"El producto {product.sku} no tiene stock en ninguna ubicación.",
            )
    else:
        open_alerts.update(is_resolved=True, resolved_at=timezone.now())


def sync_location_blocked_alerts_for_location(location: Location) -> None:
    """Alerta por cada producto con stock en una ubicación BLOCKED o ARCHIVED."""
    blocked_statuses = (
        Location.OperationalStatus.BLOCKED,
        Location.OperationalStatus.ARCHIVED,
    )
    severity, category = _severity_and_category(AlertType.LOCATION_BLOCKED_WITH_STOCK)

    if location.operational_status not in blocked_statuses:
        # Ubicación ya no está bloqueada: resolver alertas pendientes de esta ubicación
        Alert.objects.filter(
            location_id=location.id,
            alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
            is_resolved=False,
        ).update(is_resolved=True, resolved_at=timezone.now())
        return

    products_with_stock = StockByLocation.objects.filter(
        location_id=location.id, current_stock__gt=0
    ).values_list("product_id", flat=True)

    for product_id in products_with_stock:
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            continue
        already_open = Alert.objects.filter(
            product_id=product_id,
            location_id=location.id,
            alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
            is_resolved=False,
        ).exists()
        if not already_open:
            Alert.objects.create(
                product_id=product_id,
                location_id=location.id,
                alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
                severity=severity,
                category=category,
                message=(
                    f"La ubicación '{location.code}' está {location.operational_status} "
                    f"y contiene stock del producto {product.sku}."
                ),
            )

    # Resolver alertas de productos que ya no tienen stock en esta ubicación
    Alert.objects.filter(
        location_id=location.id,
        alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
        is_resolved=False,
    ).exclude(product_id__in=products_with_stock).update(
        is_resolved=True, resolved_at=timezone.now()
    )


def check_and_create_expiration_alerts() -> list[Alert]:
    """
    RF-011 — Recorre productos con fecha de vencimiento y genera alertas 30/60 días.

    Returns:
        Lista vacía reservada para extensiones que retornen instancias creadas.
    """
    for pid in Product.objects.filter(is_active=True).values_list("id", flat=True):
        sync_expiry_alerts_for_product(pid)
    return []


def scan_all_expiry_alerts(*, dry_run: bool = False) -> int:
    """Escanea todos los productos activos y sincroniza alertas de vencimiento y lotes vencidos."""
    count = 0
    for pid in Product.objects.filter(is_active=True).values_list("id", flat=True):
        if not dry_run:
            sync_expiry_alerts_for_product(pid)
            sync_lot_expired_alerts(pid)
        count += 1
    return count


def scan_all_stock_alerts(*, dry_run: bool = False) -> int:
    """Escanea todos los productos activos y sincroniza alertas de stock bajo y stock cero."""
    count = 0
    for pid in Product.objects.filter(is_active=True).values_list("id", flat=True):
        if not dry_run:
            sync_stock_alerts_for_product(pid)
            sync_stock_zero_alerts(pid)
        count += 1
    return count


def scan_all_location_alerts(*, dry_run: bool = False) -> int:
    """Escanea ubicaciones BLOCKED/ARCHIVED con stock y genera alertas correspondientes.

    También procesa ubicaciones con alertas LOCATION_BLOCKED_WITH_STOCK abiertas que
    ya no están bloqueadas, garantizando que el cron resuelva estados stale.
    """
    blocked_statuses = (
        Location.OperationalStatus.BLOCKED,
        Location.OperationalStatus.ARCHIVED,
    )
    blocked_locations = Location.objects.filter(operational_status__in=blocked_statuses)
    blocked_ids = set(blocked_locations.values_list("id", flat=True))

    # Ubicaciones con alertas abiertas que ya NO están bloqueadas (stale)
    stale_ids = (
        Alert.objects.filter(
            alert_type=AlertType.LOCATION_BLOCKED_WITH_STOCK,
            is_resolved=False,
        )
        .exclude(location_id__in=blocked_ids)
        .values_list("location_id", flat=True)
        .distinct()
    )
    stale_locations = Location.objects.filter(pk__in=stale_ids)

    all_locations = list(blocked_locations) + [
        loc for loc in stale_locations if loc.id not in blocked_ids
    ]

    count = 0
    for location in all_locations:
        if not dry_run:
            sync_location_blocked_alerts_for_location(location)
        count += 1
    return count


@transaction.atomic
def resolve_alert(executor: User, alert_id: UUID) -> Alert:
    """
    RF-011 — Marca alerta como resuelta (solo almacenista).

    Raises:
        UnauthorizedDomainActionError: Rol distinto de almacenista.
    """
    if getattr(executor, "role", None) != RoleChoices.ALMACENISTA:
        raise UnauthorizedDomainActionError(
            "Solo el almacenista puede resolver alertas."
        )
    alert = Alert.objects.select_for_update().get(pk=alert_id)
    alert.is_resolved = True
    alert.resolved_at = timezone.now()
    alert.resolved_by = executor
    alert.save(update_fields=["is_resolved", "resolved_at", "resolved_by"])
    log_event(
        AuditEventType.ALERT_RESOLVED,
        user=executor,
        detail={
            "alert_id": str(alert.id),
            "alert_type": alert.alert_type,
            "product_id": str(alert.product_id) if alert.product_id else None,
            "location_id": str(alert.location_id) if alert.location_id else None,
            "_entity_type": "Alert",
            "_entity_id": str(alert.id),
            "_origin": "API",
        },
    )
    return alert
