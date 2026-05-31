"""Stock derivado por ubicación (RF-004, BR-11, BR-14, BR-15).

El ledger en `movements` es la única fuente de verdad; este modelo es caché
consistente actualizada solo desde `apps.movements.services`.
"""

from __future__ import annotations

# Determinar el nombre de argumento correcto para CheckConstraint
from inspect import signature as _inspect_signature

from django.db import models
from django.db.models import Q

from shared.models import BaseModel

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


class StorageType(BaseModel):
    """
    Tipo configurable de almacenamiento para clasificar ubicaciones (BR-15).

    Se modela aparte para permitir extensibilidad (bodega, vitrina, nevera, etc.)
    sin romper la entidad única de `Location`.
    BR-15: solo tipos activos pueden asignarse a nuevas ubicaciones o reasignarse a las existentes.
    """

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, default="general")
    description = models.TextField(blank=True)
    capabilities = models.JSONField(default=dict, blank=True)
    default_is_retail = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tipo de almacenamiento"
        verbose_name_plural = "Tipos de almacenamiento"
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class StorageTemplate(BaseModel):
    """
    Plantilla reutilizable de configuración para crear ubicaciones rápidamente.

    Desacoplada de stock y ledger: solo define metadatos/defaults operativos.
    """

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120, unique=True)
    storage_type = models.ForeignKey(
        StorageType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="templates",
    )
    description = models.TextField(blank=True)
    defaults = models.JSONField(default=dict, blank=True)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Plantilla de almacenamiento"
        verbose_name_plural = "Plantillas de almacenamiento"
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class Location(BaseModel):
    """
    Ubicación física de almacenamiento (RF-004, BR-11, BR-14).

    `code`: identificador corto auto-generado con slugify del nombre (único).
    `is_retail`: se detecta automáticamente si el nombre contiene palabras clave de vitrina.
    `max_capacity`: capacidad máxima de productos (útil para vitrinas o espacios limitados).
    BR-14: `operational_status` determina qué operaciones de stock son elegibles para esta ubicación.
    """

    class OperationalStatus(models.TextChoices):
        ACTIVE = "active", "Activa"
        MAINTENANCE = "maintenance", "Mantenimiento"
        RESTRICTED = "restricted", "Restringida"
        BLOCKED = "blocked", "Bloqueada"
        ARCHIVED = "archived", "Archivada"

    class CapacityMode(models.TextChoices):
        NONE = "none", "Sin capacidad"
        RELATIVE_SCALE = "relative_scale", "Escala relativa"
        ABSOLUTE_LEGACY = "absolute_legacy", "Capacidad absoluta (legacy)"

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
    storage_type = models.ForeignKey(
        StorageType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="locations",
    )
    storage_template = models.ForeignKey(
        StorageTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locations",
    )
    operational_status = models.CharField(
        max_length=20,
        choices=OperationalStatus.choices,
        default=OperationalStatus.ACTIVE,
        db_index=True,
        help_text="Estado operativo de la ubicación para reglas de movimientos.",
    )
    capacity_mode = models.CharField(
        max_length=20,
        choices=CapacityMode.choices,
        default=CapacityMode.NONE,
        db_index=True,
        help_text="Modo de capacidad para cálculo de ocupación informativa.",
    )
    capacity_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Escala relativa (1-5) cuando capacity_mode=relative_scale.",
    )
    capacity_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Puntaje de capacidad relativo (unidad abstracta, no bloqueante).",
    )
    occupancy_estimate_pct = models.FloatField(
        null=True,
        blank=True,
        help_text="Estimación informativa de ocupación calculada o ajustada.",
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
    location_reorder_point = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override local de umbral de reorden. Si null, usa reorder_point del producto.",
    )
    last_movement_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Último movimiento que alteró este registro (auditoría rápida).",
    )

    @property
    def effective_reorder_point(self) -> int:
        """Umbral efectivo: local si está definido, global del producto como fallback."""
        if self.location_reorder_point is not None:
            return self.location_reorder_point
        return int(self.product.reorder_point or 0)

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
