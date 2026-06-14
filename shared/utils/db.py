"""Utilidades de base de datos compartidas entre servicios."""

from __future__ import annotations

from typing import Any

from shared.exceptions import ResourceNotFoundError


def get_for_update_or_404(
    queryset: Any,
    *,
    pk: object,
    detail: str | None = None,
) -> Any:
    """
    Obtiene un objeto con lock de fila o lanza 404.

    Uso típico dentro de servicios @transaction.atomic:
        product = get_for_update_or_404(Product.objects, pk=product_id)

    Args:
        queryset: QuerySet del modelo, normalmente ``Model.objects``.
        pk: Valor de clave primaria a buscar.
        detail: Mensaje opcional para ResourceNotFoundError.

    Returns:
        La instancia del modelo con lock adquirido.

    Raises:
        ResourceNotFoundError: Si el objeto no existe (HTTP 404).
    """
    try:
        return queryset.select_for_update().get(pk=pk)
    except queryset.model.DoesNotExist:
        model_name = queryset.model._meta.verbose_name or queryset.model.__name__
        msg = detail or f"{model_name} con ID {pk} no encontrado."
        raise ResourceNotFoundError(msg)
