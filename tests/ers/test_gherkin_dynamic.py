"""
Tests dinámicos 1:1 con escenarios Gherkin del ERS.

Cada función `test_RFxxx_Sxx` corresponde al archivo `docs/test/scenarios/RFxxx-Sxx.md`.
Metadatos: `docs/test/gherkin_scenarios.json` (generado por `scripts/parse_ers_gherkin.py`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.ers.gherkin_impl import run_gherkin_scenario

_ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS_PATH = _ROOT / "docs" / "test" / "gherkin_scenarios.json"
SCENARIOS: list[dict] = json.loads(_SCENARIOS_PATH.read_text(encoding="utf-8"))


def _make_test(sid: str, title: str):
    @pytest.mark.django_db
    def _scenario_test(request: pytest.FixtureRequest) -> None:
        run_gherkin_scenario(sid, request)

    _scenario_test.__name__ = f"test_{sid.replace('-', '_')}"
    _scenario_test.__doc__ = f"ERS {sid} — {title}"
    return _scenario_test


for _sc in SCENARIOS:
    _sid = _sc["id"]
    _fname = f"test_{_sid.replace('-', '_')}"
    globals()[_fname] = _make_test(_sid, _sc["title"])
