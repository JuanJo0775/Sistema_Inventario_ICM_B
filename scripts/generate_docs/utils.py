#!/usr/bin/env python3
"""
Utilidades para generación de documentación de tests.

Provee: iter_test_nodes(), render_doc(), classify_test(), assign_codes()
e índices por carpeta.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
GHERKIN_SCOPE_FILE = ROOT / "docs" / "test" / "gherkin_out_of_scope.json"


def clear_markdown_dir(dir_path: Path) -> None:
    """Elimina archivos Markdown existentes dentro de una carpeta."""
    if not dir_path.exists():
        return
    for file_path in dir_path.glob("*.md"):
        file_path.unlink()


def iter_test_nodes() -> List[Tuple[str, str, int]]:
    """Recorre `tests/` y `apps/*/tests/` buscando test_*.py y devuelve
    una lista de tuplas (nodeid, rel_path, line_no).
    """
    out: list[tuple[str, str, int]] = []
    paths: list[Path] = []
    root_tests = ROOT / "tests"
    if root_tests.is_dir():
        paths.extend(root_tests.glob("test_*.py"))
        # Also include nested test files under tests/**/ if any
        paths.extend(root_tests.rglob("test_*.py"))
    apps_dir = ROOT / "apps"
    if apps_dir.is_dir():
        for app in apps_dir.iterdir():
            tdir = app / "tests"
            if tdir.is_dir():
                paths.extend(tdir.glob("test_*.py"))
                paths.extend(tdir.rglob("test_*.py"))
    seen = set()
    for path in paths:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        if path.name == "__init__.py":
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


def render_doc(nodeid: str, rel: str, line: int, kind: str = "unit") -> str:
    short = nodeid.split("::")[-1]
    if kind == "integration":
        purpose = "Prueba de integración HTTP (API) — validar flujos y contratos entre capas."
    elif kind == "gherkin":
        purpose = "Escenario Gherkin derivado del ERS; ver `docs/ERS_ICM_Requisitos.md`."
    else:
        purpose = "Prueba unitaria del backend ICM."
    return f"""# {short}

## Nombre del test

`{nodeid}`

## Propósito

{purpose}

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


def classify_test(rel: str) -> str:
    """Clasifica por ruta relativa en 'gherkin'|'integration'|'unit'.

    Reglas:
    - Cualquier test bajo `tests/ers/` => 'gherkin'
    - Archivos con 'integration' en el nombre, o bajo `tests/integration/`, o
      el archivo `tests/test_api_integration.py`, o `apps/*/tests/integration_*.py` => 'integration'
    - Resto => 'unit'
    """
    if rel.startswith("tests/ers/"):
        return "gherkin"
    name = Path(rel).name.lower()
    if "integration" in name:
        return "integration"
    if rel.startswith("tests/integration/"):
        return "integration"
    if rel == "tests/test_api_integration.py":
        return "integration"
    # apps/*/tests/integration_*.py
    if re.match(r"apps/[^/]+/tests/integration_.*\.py", rel):
        return "integration"
    return "unit"


def assign_codes(nodes: list[tuple[str, str, int]], kind: str) -> dict:
    """Asigna códigos de documentación secuenciales por tipo.

    Devuelve un dict nodeid -> code.
    Formato: UNIT-0001, INT-0001
    """
    prefix = "UNIT" if kind == "unit" else "INT" if kind == "integration" else "GEN"
    out: dict[str, str] = {}
    i = 1
    for nodeid, rel, line in sorted(nodes, key=lambda x: x[0]):
        code = f"{prefix}-{i:04d}"
        out[nodeid] = code
        i += 1
    return out


def write_index(
    nodes: list[tuple[str, str, int]],
    codes: dict,
    kind: str,
    out_dir: Path | None = None,
) -> None:
    """Escribe un índice `index.md` dentro de la carpeta de documentación del tipo.

    El índice queda junto a los archivos individuales para que sea el primer
    elemento visible al abrir la carpeta en el explorador.
    """
    root = ROOT
    target_dir = out_dir or (root / "docs" / "test" / kind)
    target_dir.mkdir(parents=True, exist_ok=True)
    clear_markdown_dir(target_dir)
    fname = target_dir / "index.md"
    title = {
        "unit": "unitarios",
        "integration": "integración",
        "gherkin": "escenarios Gherkin",
    }.get(kind, kind)
    lines = [f"# Índice de tests ({title})\n", "| Código | Test | Archivo |\n", "|---|---|---|\n"]
    for nodeid, rel, line in sorted(nodes, key=lambda x: codes.get(x[0], "")):
        code = codes.get(nodeid, "")
        short = nodeid.split("::")[-1]
        link = f"./{code}.md" if code else "#"
        lines.append(f"| {code} | {short} | [{code}.md]({link}) |\n")
    fname.write_text("".join(lines), encoding="utf-8")


def write_gherkin_docs(scenarios: list[dict]) -> None:
    """Escribe JSON y Markdown para escenarios Gherkin en `docs/test/scenarios/`.

    Este helper preserva el formato actual de `scripts/parse_ers_gherkin.py`.
    """
    root = ROOT
    out_json = root / "docs" / "test" / "gherkin_scenarios.json"
    out_dir = root / "docs" / "test" / "scenarios"

    out_of_scope: dict[str, dict[str, str]] = {}
    if GHERKIN_SCOPE_FILE.exists():
        raw = json.loads(GHERKIN_SCOPE_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            out_of_scope = {
                str(key): {
                    "reason": str(value.get("reason", "")),
                    "scope": str(value.get("scope", "backend")),
                }
                for key, value in raw.items()
                if isinstance(value, dict)
            }

    out_dir.mkdir(parents=True, exist_ok=True)
    clear_markdown_dir(out_dir)
    for sc in scenarios:
        scope_note = out_of_scope.get(sc["id"])
        if scope_note:
            sc["automation_scope"] = scope_note
        else:
            sc["automation_scope"] = {"reason": "", "scope": "backend"}

    out_json.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")
    index_lines = [
        "# Índice de escenarios Gherkin\n",
        "| Código | Escenario | Estado | Archivo |\n",
        "|---|---|---|---|\n",
    ]

    # escribir por escenario usando el contenido ya parseado
    for sc in scenarios:
        sid = sc["id"]
        pytest_node = f"tests/ers/test_gherkin_dynamic.py::test_{sid.replace('-', '_')}"
        scope_note = sc.get("automation_scope", {})
        is_out_of_scope = bool(scope_note.get("reason"))
        auto_txt = (
            "Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. "
            f"Motivo: {scope_note.get('reason')}"
            if is_out_of_scope
            else "Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS)."
        )
        md = f"""# {sc['title']}

## Nombre del test

`{pytest_node}`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **{sc['rf']}** — escenario {sc['scenario_number']}.\n
## Requisito o caso de negocio asociado

- **Requisito:** `{sc['rf']}` (ver `docs/ERS_ICM_Requisitos.md`).\n
## Inputs (Given / When — extracto ERS)

{sc['given_when_then'][:4000]}{"…" if len(sc['given_when_then']) > 4000 else ""}

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest {pytest_node} -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatización backend

{auto_txt}
"""
        (out_dir / f"{sid}.md").write_text(md, encoding="utf-8")
    state = "Fuera de alcance" if is_out_of_scope else "Implementado"
    index_lines.append(f"| {sid} | {sc['title']} | {state} | [{sid}.md](./{sid}.md) |\n")

    (out_dir / "index.md").write_text("".join(index_lines), encoding="utf-8")
