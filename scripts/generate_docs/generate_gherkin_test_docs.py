#!/usr/bin/env python3
"""
Wrapper para regenerar la documentación de escenarios Gherkin.

Uso: python scripts/generate_docs/generate_gherkin_test_docs.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "parse_ers_gherkin.py"


def main() -> None:
    if not SCRIPT.exists():
        print(f"No encontrado: {SCRIPT}")
        raise SystemExit(1)
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT)
    rc = subprocess.run([sys.executable, str(SCRIPT)], cwd=str(ROOT), env=env).returncode
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
