"""Alertas proactivas (RF-011)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.alerts.models import Alert, AlertType
from apps.authentication.models import RoleChoices
from apps.catalog.models import Lot, Product
from apps.inventory.models import Location, StockByLocation
from shared.exceptions import UnauthorizedDomainActionError

if TYPE_CHECKING:
    from apps.authentication.models import User


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
            Alert.objects.create(
                product_id=product_id,
                alert_type=AlertType.LOW_STOCK,
                location=None,
                message=f"Stock total {total_qty} en o por debajo del umbral {threshold}.",
            )
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
    alert, created = Alert.objects.get_or_create(
        product_id=lot.product_id,
        lot_id=lot.id,
        alert_type=alert_type,
        location=None,
        defaults={"message": message, "is_resolved": False},
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
            Alert.objects.create(
                product_id=product_id,
                lot=None,
                alert_type=AlertType.EXPIRATION_60,
                location=None,
                message=f"El producto vence en {days_left} días (ventana 60).",
            )
    if days_left <= 30:
        alert, _created = Alert.objects.get_or_create(
            product_id=product_id,
            lot=None,
            alert_type=AlertType.EXPIRATION_30,
            location=None,
            defaults={
                "message": f"El producto vence en {days_left} días (ventana 30).",
                "is_resolved": False,
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

    Usa `reorder_point` del producto como umbral mínimo.
    """
    threshold = int(getattr(product, "reorder_point", 0) or 0)
    row = StockByLocation.objects.filter(
        product_id=product.id, location_id=location.id
    ).first()
    qty = int(row.current_stock) if row else 0
    if qty > threshold:
        return None
    if Alert.objects.filter(
        product_id=product.id,
        location_id=location.id,
        alert_type=AlertType.LOW_STOCK,
        is_resolved=False,
    ).exists():
        return None
    return Alert.objects.create(
        product_id=product.id,
        location_id=location.id,
        alert_type=AlertType.LOW_STOCK,
        message=f"Stock en {location.code} ({qty}) en o por debajo del umbral {threshold}.",
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
    return alert
