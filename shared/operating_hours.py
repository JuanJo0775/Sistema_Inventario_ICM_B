"""
BR-03 — Franja horaria operativa para auxiliares de despacho.

Única fuente de verdad para la regla de horario. Importar desde aquí
en lugar de duplicar la lógica en authentication/services, serializers o permissions.
"""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

BOGOTA = ZoneInfo("America/Bogota")

_MORNING_START = time(7, 0)
_MORNING_END = time(12, 0)
_AFTERNOON_START = time(14, 0)
_AFTERNOON_END = time(17, 0)


def is_within_operating_hours(*, now: datetime | None = None) -> bool:
    """
    BR-03 — True si la hora actual (o `now`) está en franja operativa de auxiliares.

    Franjas (hora local America/Bogota): 07:00–12:00 y 14:00–17:00 (inclusive).
    """
    now = now or timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, BOGOTA)
    t = now.astimezone(BOGOTA).time()
    return (_MORNING_START <= t <= _MORNING_END) or (
        _AFTERNOON_START <= t <= _AFTERNOON_END
    )
