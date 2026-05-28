#!/usr/bin/env python3
"""Legacy entrypoint for the ERS Gherkin generator; kept as a thin wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_docs import main


if __name__ == "__main__":
    raise SystemExit(main(["--only", "gherkin"]))
