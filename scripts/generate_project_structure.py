#!/usr/bin/env python3
"""Compatibility shim for the project structure generator."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.project_structure.generate_project_structure import main

if __name__ == "__main__":
    raise SystemExit(main())
