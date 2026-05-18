#!/usr/bin/env python3
"""
Regenera la documentación de tests completa:

- Escenarios ERS/Gherkin (`scripts/parse_ers_gherkin.py`)
- Tests unitarios / de integración fuera de ERS (`scripts/generate_docs/generate_unit_test_docs.py` y `scripts/generate_docs/generate_integration_test_docs.py`)

Uso: python scripts/generate_all_test_docs.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = [
    ROOT / "scripts" / "generate_docs" / "generate_gherkin_test_docs.py",
    ROOT / "scripts" / "generate_docs" / "generate_integration_test_docs.py",
    ROOT / "scripts" / "generate_docs" / "generate_unit_test_docs.py",
]


def run_script(path: Path) -> int:
    print(f"Ejecutando: {path.name}")
    return subprocess.run([sys.executable, str(path)], cwd=str(ROOT)).returncode


def main() -> None:
    any_failed = False
    for s in SCRIPTS:
        if not s.exists():
            print(f"Script no encontrado: {s}")
            any_failed = True
            continue
        code = run_script(s)
        if code != 0:
            print(f"Fallo al ejecutar {s.name} (código {code})")
            any_failed = True
    if any_failed:
        print("Al menos un script falló. Revisa la salida anterior.")
        sys.exit(1)
    print("Documentación regenerada correctamente: Gherkin + unitarias/integración.")


if __name__ == "__main__":
    main()
