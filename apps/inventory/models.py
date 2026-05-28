"""Stock derivado por ubicación (RF-004, BR-11).

El ledger en `movements` es la única fuente de verdad; este modelo es caché
consistente actualizada solo desde `apps.movements.services`.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from shared.models import BaseModel

# Determinar el nombre de argumento correcto para CheckConstraint
from inspect import signature as _inspect_signature

_cc_params = _inspect_signature(models.CheckConstraint.__init__).parameters
if "condition" in _cc_params:
    _cc_kw = {"condition": Q(current_stock__gte=0)}
else:
    _cc_kw = {"check": Q(current_stock__gte=0)}

# Constraint reutilizable para Meta
_STOCK_NON_NEGATIVE_CC = models.CheckConstraint(name="stock_non_negative", **_cc_kw)

# Palabras clave para detectar automáticamente si una ubicación es de tipo vitrina (minorista)
_VITRINA_KEYWORDS = {
    "vitrina",
    "mostrador",
    "exhibición",
    "exhibicion",
    "display",
    "tienda",
    "punto de venta",
}


def _is_retail_by_name(name: str) -> bool:
    """Detecta si una ubicación es minorista según palabras clave en el nombre."""
    normalized = (name or "").lower().strip()
    return any(kw in normalized for kw in _VITRINA_KEYWORDS)


class Location(BaseModel):
    """
    Ubicación física de almacenamiento (RF-004, BR-11).

    `code`: identificador corto auto-generado con slugify del nombre (único).
    `is_retail`: se detecta automáticamente si el nombre contiene palabras clave de vitrina.
    `max_capacity`: capacidad máxima de productos (útil para vitrinas o espacios limitados).
    """

    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_retail = models.BooleanField(
        default=False,
        help_text="True si la ubicación es un punto de venta minorista (vitrina, mostrador, etc.).",
    )
    max_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Capacidad máxima de productos. Aplica principalmente a vitrinas.",
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
            _STOCK_NON_NEGATIVE_CC,
        ]
        indexes = [
            models.Index(fields=("product", "location")),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} @ {self.location_id}: {self.current_stock}"
