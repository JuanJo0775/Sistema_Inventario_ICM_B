#!/usr/bin/env python3
"""
Genera un .md por cada test pytest fuera de tests/ers/test_gherkin_dynamic.py
en docs/test/unit/ con el formato estándar ICM.

Uso: python scripts/generate_non_gherkin_test_docs.py
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "test" / "unit"
SKIP_PARTS = ("tests/ers/test_gherkin_dynamic.py",)


def iter_test_nodes() -> list[tuple[str, str, int]]:
    """(nodeid, rel_path, line_no)"""
    out: list[tuple[str, str, int]] = []
    paths: list[Path] = []
    root_tests = ROOT / "tests"
    if root_tests.is_dir():
        paths.extend(root_tests.glob("test_*.py"))
    apps_dir = ROOT / "apps"
    if apps_dir.is_dir():
        for app in apps_dir.iterdir():
            tdir = app / "tests"
            if tdir.is_dir():
                paths.extend(tdir.glob("test_*.py"))
    for path in paths:
        if path.name == "__init__.py" or "tests/ers/" in path.as_posix():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(s in rel for s in SKIP_PARTS):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                nodeid = f"{rel}::{node.name}"
                out.append((nodeid, rel, node.lineno))
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                        nodeid = f"{rel}::{node.name}::{item.name}"
                        out.append((nodeid, rel, item.lineno))
    return sorted(out, key=lambda x: x[0])


def slug_from_nodeid(nodeid: str) -> str:
    s = nodeid.replace("/", "__").replace("::", "__")
    s = re.sub(r"[^a-zA-Z0-9_.-]+", "_", s)
    return s[:180]


def write_doc(nodeid: str, rel: str, line: int) -> None:
    slug = slug_from_nodeid(nodeid)
    short = nodeid.split("::")[-1]
    md = f"""# {short}

## Nombre del test

`{nodeid}`

## Propósito

Prueba unitaria o de integración del backend ICM (fuera del mapeo 1:1 ERS Gherkin en `tests/ers/test_gherkin_dynamic.py`). Consultar docstring en el código fuente para el detalle del caso.

## Requisito o caso de negocio asociado

Ver docstring del test y módulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementación.

## Resultado esperado

Aserciones del test (`assert`); ver código en la línea indicada abajo.

## Link directo al test

```bash
pytest {nodeid} -v
```

Código: [`{rel}`](../../{rel}) (aprox. línea {line})
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{slug}.md").write_text(md, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for nodeid, rel, line in iter_test_nodes():
        write_doc(nodeid, rel, line)
    print(f"Generados {len(list(OUT.glob('*.md')))} archivos en {OUT}")


if __name__ == "__main__":
    main()
