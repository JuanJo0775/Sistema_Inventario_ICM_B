#!/usr/bin/env python3
"""
Genera documentación para tests de integración en `docs/test/integration/` usando utilidades compartidas.

Uso: python scripts/generate_docs/generate_integration_test_docs.py
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
out_dir = ROOT / "docs" / "test" / "integration"
out_dir.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))

utils = import_module("scripts.generate_docs.utils")
iter_test_nodes = utils.iter_test_nodes
render_doc = utils.render_doc
classify_test = utils.classify_test


def main() -> None:
    nodes = iter_test_nodes()
    integration_nodes = [n for n in nodes if classify_test(n[1]) == "integration"]
    print(f"Encontrados {len(integration_nodes)} tests de integración")
    utils.clear_markdown_dir(out_dir)
    codes = utils.assign_codes(integration_nodes, "integration")
    utils.write_index(integration_nodes, codes, "integration", out_dir)
    for nodeid, rel, line in integration_nodes:
        code = codes.get(nodeid)
        md = render_doc(nodeid, rel, line, kind="integration")
        md = f"**Código:** {code}\n\n" + md
        (out_dir / f"{code}.md").write_text(md, encoding="utf-8")
    print("Documentación de integración generada en docs/test/integration/ con index.md")


if __name__ == "__main__":
    main()
