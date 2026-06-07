# DEPRECATED — este módulo es un shim de compatibilidad.
# La implementación real está en tests/ers/impl/
# Este fichero se mantiene únicamente para no romper imports externos durante la transición.
import warnings

warnings.warn(
    "gherkin_impl.py está deprecado. Importar desde tests.ers.impl",
    DeprecationWarning,
    stacklevel=2,
)

from tests.ers.impl import IMPLEMENTATIONS, run_gherkin_scenario  # noqa: F401, E402
