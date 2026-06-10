"""Re-exporta excepciones de dominio usadas por movimientos (README_ARQUITECTURA §7.5)."""

from shared.exceptions import (  # noqa: F401
    AdjustmentJustificationRequiredError,
    CrossValidationFailedError,
    DiscrepancyNoteRequiredError,
    ICMBaseException,
    ImmutableRecordError,
    InsufficientStockError,
    LotCodeRequiredError,
    LotExpirationDateRequiredError,
    LotMismatchError,
    PrivacyConsentRequiredError,
    ReturnNotAllowedError,
    SerialNumberRequiredError,
    StockMismatchError,
    UnauthorizedDomainActionError,
)


class ImmutableMovementError(ImmutableRecordError):
    """Compatibilidad: movimiento inmutable (BR-10)."""

    default_code = "immutable_movement"
