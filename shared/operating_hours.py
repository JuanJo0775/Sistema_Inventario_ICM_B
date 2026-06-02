"""
BR-03 — Franja horaria operativa para auxiliares de despacho.

Única fuente de verdad para la regla de horario. Importar desde aquí
en lugar de duplicar la lógica en authentication/services, serializers o permissions.
"""

from __future__ import annotations

from datetime import datetime, time

from django.utils import timezone

_MORNING_START = time(7, 0)
_MORNING_END = time(12, 0)
_AFTERNOON_START = time(14, 0)
_AFTERNOON_END = time(17, 0)


def is_time_in_ranges(
    t: time,
    m_start: time | None,
    m_end: time | None,
    a_start: time | None,
    a_end: time | None,
) -> bool:
    """
    Checks if a given time `t` falls within the morning range (m_start to m_end)
    or the afternoon range (a_start to a_end).
    """
    in_morning = False
    if m_start is not None and m_end is not None:
        in_morning = m_start <= t <= m_end

    in_afternoon = False
    if a_start is not None and a_end is not None:
        in_afternoon = a_start <= t <= a_end

    return in_morning or in_afternoon


def is_within_operating_hours(*, now: datetime | None = None) -> bool:
    """
    BR-03 — True si la hora actual (o `now`) está en franja operativa de auxiliares.

    Franjas (hora local): 07:00–12:00 y 14:00–17:00 (inclusive).
    """
    tz = timezone.get_current_timezone()
    now = now or timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, tz)
    t = now.astimezone(tz).time()
    return is_time_in_ranges(
        t,
        _MORNING_START,
        _MORNING_END,
        _AFTERNOON_START,
        _AFTERNOON_END,
    )
