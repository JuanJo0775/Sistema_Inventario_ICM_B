"""Dispatcher Gherkin con lógica de 3 estados: Implementado / Pendiente / Fuera de alcance / Faltante."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from .registry import IMPLEMENTATIONS

_ROOT = Path(__file__).resolve().parents[3]
_OUT_OF_SCOPE: dict = json.loads(
    (_ROOT / "docs" / "test" / "gherkin_out_of_scope.json").read_text(encoding="utf-8")
)
_pending_path = _ROOT / "docs" / "test" / "gherkin_pending.json"
_PENDING: dict = (
    json.loads(_pending_path.read_text(encoding="utf-8"))
    if _pending_path.exists()
    else {}
)


def run_gherkin_scenario(sid: str, request: pytest.FixtureRequest) -> None:
    fn = IMPLEMENTATIONS.get(sid)

    if fn is not None:
        sig = inspect.signature(fn)
        kwargs = {name: request.getfixturevalue(name) for name in sig.parameters}
        fn(**kwargs)
        return

    if sid in _OUT_OF_SCOPE:
        reason = _OUT_OF_SCOPE[sid].get("reason", "")
        pytest.skip(f"[SCOPE] {sid} — {reason}")

    if sid in _PENDING:
        reason = _PENDING[sid].get("reason", "")
        pytest.skip(f"[PENDING] {sid} — {reason}")

    pytest.fail(
        f"[MISSING] {sid} no tiene implementación ni está declarado en "
        f"gherkin_pending.json ni gherkin_out_of_scope.json.\n"
        f"Para añadir la implementación: crear impl_<sid_snake>() en "
        f"tests/ers/impl/<dominio>.py y registrarla en IMPLEMENTATIONS del mismo fichero.\n"
        f"Para aplazarla: añadir entrada en docs/test/gherkin_pending.json."
    )
