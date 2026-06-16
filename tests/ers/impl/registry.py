# WORKFLOW para añadir un nuevo escenario:
# 1. Añadir escenario al ERS (docs/requisitos/ERS_ICM_Requisitos.md)
# 2. python -m scripts.generate_docs  → actualiza gherkin_scenarios.json y docs/test/scenarios/
# 3. Si es backend automatable hoy:
#    a. Crear impl_<rf>_<s>() en el fichero de dominio correspondiente
#    b. Registrarla en IMPLEMENTATIONS del mismo fichero
# 4. Si es backend automatable pero aplazado:
#    Añadir entrada en docs/test/gherkin_pending.json
# 5. Si es sólo E2E/UI:
#    Añadir entrada en docs/test/gherkin_out_of_scope.json
# CI (gherkin_tests job) fallará si el escenario queda sin registrar en ningún lado.

from __future__ import annotations

from .alerts import IMPLEMENTATIONS as _ALERTS
from .audit import IMPLEMENTATIONS as _AUDIT
from .auth import IMPLEMENTATIONS as _AUTH
from .catalog import IMPLEMENTATIONS as _CATALOG
from .inventory import IMPLEMENTATIONS as _INVENTORY
from .movements import IMPLEMENTATIONS as _MOVEMENTS
from .nonfunctional import IMPLEMENTATIONS as _NF
from .pricing import IMPLEMENTATIONS as _PRICING
from .purchasing import IMPLEMENTATIONS as _PURCHASING
from .reports import IMPLEMENTATIONS as _REPORTS

IMPLEMENTATIONS: dict[str, object] = {
    **_AUTH,
    **_CATALOG,
    **_INVENTORY,
    **_MOVEMENTS,
    **_REPORTS,
    **_ALERTS,
    **_AUDIT,
    **_PRICING,
    **_PURCHASING,
    **_NF,
}
