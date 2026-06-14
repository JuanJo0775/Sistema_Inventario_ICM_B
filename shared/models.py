"""Modelos abstractos transversales (RNF-005).

Regla arquitectónica:
- `deleted_at` = existencia lógica del registro (soft delete / archivado).
- `is_active`  = disponibilidad para reglas de negocio (asignación, uso).
Nunca mezclar ambas responsabilidades en nuevas entidades.
"""

import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Base para entidades mutables con identificador UUID (RNF-005).

    Los timestamps se almacenan en UTC (USE_TZ=True); America/Bogota en presentación.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación (UTC).",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de última modificación (UTC).",
    )

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class SoftDeleteModel(models.Model):
    """
    Abstracto para entidades con eliminación lógica (soft delete).

    Responsabilidad exclusiva: existencia lógica del registro.
    NO usar `deleted_at` para controlar reglas de negocio (asignación, disponibilidad).

    - deleted_at = NULL   → registro activo (no eliminado)
    - deleted_at = ahora  → registro eliminado lógicamente (archivado)
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Soft delete timestamp. NULL = activo; not-NULL = eliminado lógicamente.",
    )

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """Marca el registro como eliminado lógicamente."""
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self) -> None:
        """Restaura un registro previamente eliminado lógicamente."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self) -> bool:
        """True si el registro fue eliminado lógicamente."""
        return self.deleted_at is not None
