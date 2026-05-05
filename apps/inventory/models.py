"""Stock derivado por ubicación (RF-004, BR-11).

El ledger en `movements` es la única fuente de verdad; este modelo es caché
consistente actualizada solo desde `apps.movements.services`.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from shared.models import BaseModel


class LocationChoices(models.TextChoices):
    """Códigos de ubicación física ICM."""

    VITRINA = "VITRINA", "Vitrina"
    BODEGA_1 = "BODEGA_1", "Bodega 1"
    BODEGA_2 = "BODEGA_2", "Bodega 2"


class Location(BaseModel):
    """
    Ubicación física de almacenamiento (RF-004, BR-11).

    `is_retail`: True solo en Vitrina (venta minorista).
    """

    code = models.CharField(max_length=50, unique=True, choices=LocationChoices.choices)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_retail = models.BooleanField(
        default=False,
        help_text="BR-11: True solo para Vitrina (punto minorista).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ("code",)

    def __str__(self) -> str:
        return self.name


class StockByLocation(BaseModel):
    """
    Caché de stock actual por producto y ubicación (RF-004, BR-11).

    NO es fuente de verdad: el ledger (`Movement`) lo es.
    """

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="stock_by_location",
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    current_stock = models.PositiveIntegerField(
        default=0,
        help_text="BR-11: stock derivado; debe reconstruirse desde el ledger.",
    )
    last_movement_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Último movimiento que alteró este registro (auditoría rápida).",
    )

    class Meta:
        verbose_name = "Stock por Ubicación"
        verbose_name_plural = "Stock por ubicación"
        constraints = [
            models.UniqueConstraint(
                fields=("product", "location"), name="uniq_product_location_stock"
            ),
            models.CheckConstraint(
                check=Q(current_stock__gte=0),
                name="stock_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=("product", "location")),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} @ {self.location_id}: {self.current_stock}"
