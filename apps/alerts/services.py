"""Alertas proactivas (RF-011)."""

from __future__ import annotations

from uuid import UUID

from django.db.models import Sum
from django.utils import timezone

from apps.alerts.models import Alert, AlertType
from apps.catalog.models import Product
from apps.inventory.models import StockByLocation


def sync_stock_alerts_for_product(product_id: UUID, *, user=None) -> None:
    """
    RF-011 — Alerta de stock bajo según `Product.reorder_point`.

    Debe ejecutarse tras movimientos que alteren stock consolidado.
    """
    agg = StockByLocation.objects.filter(product_id=product_id).aggregate(s=Sum("current_stock"))
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
        rb = user if user is not None and getattr(user, "is_authenticated", False) else None
        open_alerts.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=rb)


def sync_expiry_alerts_for_product(product_id: UUID, *, user=None) -> None:
    """RF-011 — Alertas de vencimiento a 60 y 30 días según `Product.expiration_date`."""
    product = Product.objects.filter(pk=product_id).first()
    if not product or not product.expiration_date:
        return
    today = timezone.now().date()
    days_left = (product.expiration_date - today).days
    if days_left > 60:
        return
    if 30 < days_left <= 60:
        if not Alert.objects.filter(
            product_id=product_id,
            alert_type=AlertType.EXPIRATION_60,
            location__isnull=True,
            is_resolved=False,
        ).exists():
            Alert.objects.create(
                product_id=product_id,
                alert_type=AlertType.EXPIRATION_60,
                location=None,
                message=f"El producto vence en {days_left} días (ventana 60).",
            )
    if days_left <= 30:
        alert, _created = Alert.objects.get_or_create(
            product_id=product_id,
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
            alert.save(update_fields=["message", "is_resolved", "resolved_at", "resolved_by"])
