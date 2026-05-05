"""Re-exporta excepciones de dominio usadas por movimientos (README_ARQUITECTURA §7.5)."""

from shared.exceptions import (AdjustmentJustificationRequiredError,
                               CrossValidationFailedError,
                               DiscrepancyNoteRequiredError, ICMBaseException,
                               ImmutableRecordError, InsufficientStockError,
                               PrivacyConsentRequiredError,
                               ReturnNotAllowedError,
                               SerialNumberRequiredError, StockMismatchError,
                               UnauthorizedDomainActionError)


class ImmutableMovementError(ImmutableRecordError):
    """Compatibilidad: movimiento inmutable (BR-10)."""

    default_code = "immutable_movement"
