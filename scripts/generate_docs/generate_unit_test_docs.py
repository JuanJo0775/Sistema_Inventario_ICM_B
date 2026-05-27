#!/usr/bin/env python3
"""
Genera documentación para tests unitarios en `docs/test/unit/` usando las utilidades compartidas.

Uso: python scripts/generate_docs/generate_unit_test_docs.py
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
out_dir = ROOT / "docs" / "test" / "unit"
out_dir.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))

utils = import_module("scripts.generate_docs.utils")
iter_test_nodes = utils.iter_test_nodes
render_doc = utils.render_doc
classify_test = utils.classify_test


def main() -> None:
    nodes = iter_test_nodes()
    unit_nodes = [n for n in nodes if classify_test(n[1]) == "unit"]
    print(f"Encontrados {len(unit_nodes)} tests unitarios")
    utils.clear_markdown_dir(out_dir)
    codes = utils.assign_codes(unit_nodes, "unit")
    # escribir index
    utils.write_index(unit_nodes, codes, "unit", out_dir)
    for nodeid, rel, line in unit_nodes:
        code = codes.get(nodeid)
        md = render_doc(nodeid, rel, line, kind="unit")
        # añadir línea con código al inicio
        md = f"**Código:** {code}\n\n" + md
        (out_dir / f"{code}.md").write_text(md, encoding="utf-8")
    print("Documentación unitaria generada en docs/test/unit/ con index.md")


if __name__ == "__main__":
    main()
