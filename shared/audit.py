"""Decorador @auditable para servicios que generan AuditLog (I-02).

Convención: aplicar en todo servicio nuevo que cree o modifique entidades
de negocio. Los servicios existentes mantienen sus llamadas manuales a
log_event() para evitar riesgo de regresión.

Uso:
    @auditable(
        AuditEventType.WEBHOOK_ENDPOINT_CREATED,
        get_user=lambda user, *a, **kw: user,
    )
    def create_webhook_endpoint(user, data): ...
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def auditable(
    event_type: str,
    *,
    get_user: Callable[..., Any] | None = None,
    get_extra: Callable[..., dict] | None = None,
) -> Callable:
    """
    Decorador que emite un AuditLog tras la ejecución exitosa del servicio.

    El bloque try/except garantiza que un fallo en la auditoría nunca
    bloquea el flujo principal del servicio decorado.

    Args:
        event_type: Valor de AuditEventType a registrar.
        get_user: Callable que extrae el usuario de los args/kwargs del servicio.
        get_extra: Callable que extrae campos extra del resultado y args/kwargs.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            try:
                from apps.audit.services import log_event

                user = get_user(*args, **kwargs) if get_user else None
                extra = get_extra(result, *args, **kwargs) if get_extra else {}
                log_event(event_type, user=user, **extra)
            except Exception:
                logger.exception(
                    "auditable: fallo al emitir AuditLog para event_type=%s en %s",
                    event_type,
                    func.__qualname__,
                )
            return result

        return wrapper

    return decorator
