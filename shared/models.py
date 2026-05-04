"""Modelos abstractos transversales (RNF-005)."""

from __future__ import annotations

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
