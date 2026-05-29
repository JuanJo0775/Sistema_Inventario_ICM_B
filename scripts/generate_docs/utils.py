#!/usr/bin/env python3
"""Canonical helpers for test documentation generation."""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
TEST_DOC_ROOT = ROOT / "docs" / "test"
GHERKIN_SCOPE_FILE = TEST_DOC_ROOT / "gherkin_out_of_scope.json"

KIND_ORDER = ("unit", "integration", "gherkin")
KIND_PREFIXES = {"unit": "UNIT", "integration": "INT", "gherkin": "GEN"}
KIND_TITLES = {
    "unit": "tests unitarios",
    "integration": "tests de integración",
    "gherkin": "escenarios Gherkin",
}
KIND_OUTPUT_DIRS = {
    "unit": TEST_DOC_ROOT / "unit",
    "integration": TEST_DOC_ROOT / "integration",
    "gherkin": TEST_DOC_ROOT / "scenarios",
}
KIND_AGGREGATES = {
    "unit": TEST_DOC_ROOT / "all_unit.md",
    "integration": TEST_DOC_ROOT / "all_integration.md",
    "gherkin": TEST_DOC_ROOT / "all_scenarios.md",
}


@dataclass(frozen=True)
class TestNode:
    nodeid: str
    rel_path: str
    line_no: int
    kind: str

    @property
    def short_name(self) -> str:
        return self.nodeid.split("::")[-1]


@dataclass
class GenerationSummary:
    kind: str
    changed: bool = False
    written: list[Path] = field(default_factory=list)
    unchanged: list[Path] = field(default_factory=list)
    removed: list[Path] = field(default_factory=list)

    def absorb(self, other: "GenerationSummary") -> None:
        self.changed = self.changed or other.changed
        self.written.extend(other.written)
        self.unchanged.extend(other.unchanged)
        self.removed.extend(other.removed)


def _read_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _write_text_if_needed(
    path: Path, content: str, *, force: bool = False, check: bool = False
) -> bool:
    existing = _read_text(path)
    same = existing == content
    if check:
        return not same
    if same and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _remove_stale_markdown(
    dir_path: Path, expected_names: set[str], *, check: bool = False
) -> list[Path]:
    removed: list[Path] = []
    if not dir_path.exists():
        return removed
    for path in sorted(dir_path.glob("*.md")):
        if path.name in expected_names:
            continue
        removed.append(path)
        if not check:
            path.unlink()
    return removed


def _discover_test_files() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()

    roots: list[Path] = []
    tests_root = ROOT / "tests"
    if tests_root.is_dir():
        roots.append(tests_root)

    apps_root = ROOT / "apps"
    if apps_root.is_dir():
        for app_dir in sorted(apps_root.iterdir()):
            tests_dir = app_dir / "tests"
            if tests_dir.is_dir():
                roots.append(tests_dir)

    for root in roots:
        for path in root.rglob("test_*.py"):
            rel_path = path.relative_to(ROOT).as_posix()
            if rel_path in seen:
                continue
            seen.add(rel_path)
            candidates.append(path)

    return sorted(candidates, key=lambda path: path.relative_to(ROOT).as_posix())


def classify_test(rel_path: str) -> str:
    if rel_path.startswith("tests/ers/"):
        return "gherkin"
    name = Path(rel_path).name.lower()
    if (
        "integration" in name
        or rel_path.startswith("tests/integration/")
        or rel_path.startswith("tests/concurrency/")
        or rel_path == "tests/test_api_integration.py"
    ):
        return "integration"
    if re.match(r"apps/[^/]+/tests/integration_.*\.py", rel_path):
        return "integration"
    return "unit"


def discover_test_nodes() -> list[TestNode]:
    nodes: list[TestNode] = []
    for path in _discover_test_files():
        rel_path = path.relative_to(ROOT).as_posix()
        if path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            raise SyntaxError(f"Failed to parse {rel_path}: {exc.msg}") from exc

        kind = classify_test(rel_path)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                nodes.append(
                    TestNode(f"{rel_path}::{node.name}", rel_path, node.lineno, kind)
                )
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith(
                        "test_"
                    ):
                        nodes.append(
                            TestNode(
                                f"{rel_path}::{node.name}::{item.name}",
                                rel_path,
                                item.lineno,
                                kind,
                            )
                        )

    return sorted(nodes, key=lambda node: node.nodeid)


def iter_test_nodes() -> list[tuple[str, str, int]]:
    return [
        (node.nodeid, node.rel_path, node.line_no) for node in discover_test_nodes()
    ]


def slug_from_nodeid(nodeid: str) -> str:
    value = nodeid.replace("/", "__").replace("::", "__")
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)
    return value[:180]


def _nodeid(entry: TestNode | tuple[str, str, int]) -> str:
    return entry.nodeid if isinstance(entry, TestNode) else entry[0]


def assign_codes(
    nodes: Sequence[TestNode | tuple[str, str, int]], kind: str
) -> dict[str, str]:
    prefix = KIND_PREFIXES.get(kind, "GEN")
    out: dict[str, str] = {}
    for index, entry in enumerate(sorted(nodes, key=_nodeid), start=1):
        out[_nodeid(entry)] = f"{prefix}-{index:04d}"
    return out


def render_doc(
    nodeid: str, rel: str, line: int, kind: str = "unit", code: str | None = None
) -> str:
    short = nodeid.split("::")[-1]
    if kind == "integration":
        purpose = (
            "Prueba de integración HTTP para validar flujos y contratos entre capas."
        )
    elif kind == "gherkin":
        purpose = "Escenario Gherkin derivado del ERS; ver docs/requisitos/ERS_ICM_Requisitos.md."
    else:
        purpose = "Prueba unitaria del backend ICM."

    code_block = f"**Código:** {code}\n\n" if code else ""
    return (
        f"{code_block}# {short}\n\n"
        f"## Nombre del test\n\n"
        f"`{nodeid}`\n\n"
        f"## Propósito\n\n"
        f"{purpose}\n\n"
        f"## Requisito o caso de negocio asociado\n\n"
        f"Ver docstring del test y módulo; trazabilidad RF/BR en docs/test/TRAZABILIDAD_ERS_GHERKIN.md cuando aplique.\n\n"
        f"## Inputs\n\n"
        f"Fixtures pytest (conftest.py, tests/factories.py) y datos creados en el propio test. Ver implementación.\n\n"
        f"## Resultado esperado\n\n"
        f"Aserciones del test (assert); ver código en la línea indicada abajo.\n\n"
        f"## Link directo al test\n\n"
        f"```bash\npytest {nodeid} -v\n```\n\n"
        f"Código fuente: [{rel}](../../{rel}) (aprox. línea {line})\n"
    )


def _render_index(
    nodes: Sequence[TestNode | tuple[str, str, int]], codes: dict[str, str], kind: str
) -> str:
    title = KIND_TITLES.get(kind, kind)
    lines = [
        f"# Índice de {title}\n",
        "| Código | Test | Archivo |\n",
        "|---|---|---|\n",
    ]
    for entry in sorted(nodes, key=_nodeid):
        nodeid = _nodeid(entry)
        code = codes.get(nodeid, "")
        short = nodeid.split("::")[-1]
        lines.append(f"| {code} | {short} | [{code}.md](./{code}.md) |\n")
    return "".join(lines)


def write_index(
    nodes: Sequence[TestNode | tuple[str, str, int]],
    codes: dict[str, str],
    kind: str,
    out_dir: Path | None = None,
    *,
    force: bool = False,
    check: bool = False,
) -> bool:
    target_dir = out_dir or KIND_OUTPUT_DIRS[kind]
    target_dir.mkdir(parents=True, exist_ok=True)
    return _write_text_if_needed(
        target_dir / "index.md",
        _render_index(nodes, codes, kind),
        force=force,
        check=check,
    )


def _load_gherkin_scope() -> dict[str, dict[str, str]]:
    if not GHERKIN_SCOPE_FILE.exists():
        return {}
    raw = json.loads(GHERKIN_SCOPE_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            out[str(key)] = {
                "reason": str(value.get("reason", "")),
                "scope": str(value.get("scope", "backend")),
            }
    return out


def parse_ers() -> list[dict]:
    text = (ROOT / "docs" / "requisitos" / "ERS_ICM_Requisitos.md").read_text(
        encoding="utf-8"
    )
    lines = text.splitlines()
    current_rf: str | None = None
    scenarios: list[dict] = []

    def slug_id(rf: str, num: int) -> str:
        return f"{rf.upper()}-S{num:02d}"

    index = 0
    while index < len(lines):
        line = lines[index]
        rf_match = re.match(r"^## \*\*(RF|RNF)-(\d+)", line)
        if rf_match:
            kind, num = rf_match.group(1), rf_match.group(2)
            current_rf = f"{kind}{int(num):03d}"
            index += 1
            continue

        scenario_match = re.match(r"^### Scenario (\d+):\s*(.+)\s*$", line)
        if scenario_match and current_rf:
            scenario_number = int(scenario_match.group(1))
            title = scenario_match.group(2).strip()
            scenario_id = slug_id(current_rf, scenario_number)
            body_lines: list[str] = []
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if re.match(r"^### Scenario \d+:", next_line) or re.match(
                    r"^## \*\*", next_line
                ):
                    break
                body_lines.append(next_line)
                index += 1
            scenarios.append(
                {
                    "id": scenario_id,
                    "rf": current_rf,
                    "scenario_number": scenario_number,
                    "title": title,
                    "given_when_then": "\n".join(body_lines).strip(),
                    "source": "docs/requisitos/ERS_ICM_Requisitos.md",
                }
            )
            continue

        index += 1

    return scenarios


def _render_gherkin_doc(scenario: dict, automation_scope: dict[str, str]) -> str:
    scenario_id = scenario["id"]
    pytest_node = (
        f"tests/ers/test_gherkin_dynamic.py::test_{scenario_id.replace('-', '_')}"
    )
    reason = automation_scope.get("reason", "")
    automation_text = (
        "Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. "
        f"Motivo: {reason}"
        if reason
        else "Implementada en tests/ers/gherkin_impl.py (comprueba API/servicios equivalentes al Then del ERS)."
    )
    excerpt = scenario.get("given_when_then", "")
    excerpt = excerpt[:4000] + ("…" if len(excerpt) > 4000 else "")
    return (
        f"# {scenario['title']}\n\n"
        f"## Nombre del test\n\n"
        f"`{pytest_node}`\n\n"
        f"## Propósito\n\n"
        f"Validar el criterio de aceptación Gherkin del ERS ICM para {scenario['rf']} — escenario {scenario['scenario_number']}.\n\n"
        f"## Requisito o caso de negocio asociado\n\n"
        f"- **Requisito:** `{scenario['rf']}` (ver docs/requisitos/ERS_ICM_Requisitos.md).\n\n"
        f"## Inputs (Given / When — extracto ERS)\n\n"
        f"{excerpt}\n\n"
        f"## Resultado esperado (Then)\n\n"
        f"Ver la sección Then en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.\n\n"
        f"## Link directo al test\n\n"
        f"Ejecutar:\n\n"
        f"```bash\npytest {pytest_node} -v\n```\n\n"
        f"Archivo de definición dinámica: [tests/ers/test_gherkin_dynamic.py](../../tests/ers/test_gherkin_dynamic.py)\n\n"
        f"---\n\n"
        f"## Estado de automatización backend\n\n"
        f"{automation_text}\n"
    )


def write_gherkin_docs(
    scenarios: Sequence[dict], *, force: bool = False, check: bool = False
) -> GenerationSummary:
    summary = GenerationSummary("gherkin")
    out_dir = KIND_OUTPUT_DIRS["gherkin"]
    out_dir.mkdir(parents=True, exist_ok=True)

    scope = _load_gherkin_scope()
    docs = [
        {
            "data": dict(scenario),
            "automation_scope": scope.get(
                str(scenario["id"]), {"reason": "", "scope": "backend"}
            ),
        }
        for scenario in scenarios
    ]

    json_path = TEST_DOC_ROOT / "gherkin_scenarios.json"
    json_payload = [
        dict(doc["data"], automation_scope=doc["automation_scope"]) for doc in docs
    ]
    if _write_text_if_needed(
        json_path,
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        force=force,
        check=check,
    ):
        summary.changed = True
        summary.written.append(json_path)
    else:
        summary.unchanged.append(json_path)

    expected_names = {"index.md"} | {f"{doc['data']['id']}.md" for doc in docs}
    removed = _remove_stale_markdown(out_dir, expected_names, check=check)
    if removed:
        summary.changed = True
        summary.removed.extend(removed)

    index_lines = [
        "# Índice de escenarios Gherkin\n",
        "| Código | Escenario | Estado | Archivo |\n",
        "|---|---|---|---|\n",
    ]
    for doc in sorted(docs, key=lambda item: item["data"]["id"]):
        state = (
            "Fuera de alcance"
            if doc["automation_scope"].get("reason")
            else "Implementado"
        )
        sid = doc["data"]["id"]
        index_lines.append(
            f"| {sid} | {doc['data']['title']} | {state} | [{sid}.md](./{sid}.md) |\n"
        )
    index_path = out_dir / "index.md"
    if _write_text_if_needed(
        index_path, "".join(index_lines), force=force, check=check
    ):
        summary.changed = True
        summary.written.append(index_path)
    else:
        summary.unchanged.append(index_path)

    for doc in docs:
        sid = doc["data"]["id"]
        doc_path = out_dir / f"{sid}.md"
        if _write_text_if_needed(
            doc_path,
            _render_gherkin_doc(doc["data"], doc["automation_scope"]),
            force=force,
            check=check,
        ):
            summary.changed = True
            summary.written.append(doc_path)
        else:
            summary.unchanged.append(doc_path)

    aggregate_path = KIND_AGGREGATES["gherkin"]
    if concat_markdown(out_dir, aggregate_path, force=force, check=check):
        summary.changed = True
        summary.written.append(aggregate_path)
    else:
        summary.unchanged.append(aggregate_path)

    return summary


def write_test_docs(
    nodes: Sequence[TestNode | tuple[str, str, int]],
    kind: str,
    *,
    force: bool = False,
    check: bool = False,
) -> GenerationSummary:
    summary = GenerationSummary(kind)
    out_dir = KIND_OUTPUT_DIRS[kind]
    out_dir.mkdir(parents=True, exist_ok=True)

    node_objects = [
        (
            node
            if isinstance(node, TestNode)
            else TestNode(node[0], node[1], node[2], kind)
        )
        for node in nodes
    ]
    codes = assign_codes(node_objects, kind)
    expected_names = {"index.md"} | {
        f"{codes[node.nodeid]}.md" for node in node_objects
    }

    removed = _remove_stale_markdown(out_dir, expected_names, check=check)
    if removed:
        summary.changed = True
        summary.removed.extend(removed)

    if write_index(node_objects, codes, kind, out_dir, force=force, check=check):
        summary.changed = True
        summary.written.append(out_dir / "index.md")
    else:
        summary.unchanged.append(out_dir / "index.md")

    for node in sorted(node_objects, key=lambda item: item.nodeid):
        code = codes[node.nodeid]
        doc_path = out_dir / f"{code}.md"
        content = render_doc(
            node.nodeid, node.rel_path, node.line_no, kind=kind, code=code
        )
        if _write_text_if_needed(doc_path, content, force=force, check=check):
            summary.changed = True
            summary.written.append(doc_path)
        else:
            summary.unchanged.append(doc_path)

    aggregate_path = KIND_AGGREGATES[kind]
    if concat_markdown(out_dir, aggregate_path, force=force, check=check):
        summary.changed = True
        summary.written.append(aggregate_path)
    else:
        summary.unchanged.append(aggregate_path)

    return summary


def concat_markdown(
    src_dir: Path, out_file: Path, *, force: bool = False, check: bool = False
) -> bool:
    markdown_files = [
        path
        for path in sorted(src_dir.glob("*.md"), key=lambda candidate: candidate.name)
        if path.name != "index.md" and not path.name.startswith("all_")
    ]
    if not markdown_files:
        if check:
            return out_file.exists()
        if out_file.exists():
            out_file.unlink()
            return True
        return False

    parts: list[str] = []
    for path in markdown_files:
        parts.append(f"<!-- file: {path.name} -->\n")
        parts.append(path.read_text(encoding="utf-8"))
        parts.append("\n\n---\n\n")
    return _write_text_if_needed(out_file, "".join(parts), force=force, check=check)


def generate_kind_docs(
    kind: str, *, force: bool = False, check: bool = False
) -> GenerationSummary:
    if kind not in KIND_ORDER:
        raise ValueError(f"Unsupported kind: {kind}")
    if kind == "gherkin":
        return write_gherkin_docs(parse_ers(), force=force, check=check)
    nodes = [node for node in discover_test_nodes() if node.kind == kind]
    return write_test_docs(nodes, kind, force=force, check=check)


def generate_docs(
    kinds: Sequence[str], *, force: bool = False, check: bool = False
) -> GenerationSummary:
    summary = GenerationSummary("all")
    for kind in kinds:
        summary.absorb(generate_kind_docs(kind, force=force, check=check))
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate test documentation for the repository."
    )
    parser.add_argument(
        "--only", choices=KIND_ORDER, help="Generate only one documentation family."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite outputs even when the content is unchanged.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report whether regeneration is needed without writing.",
    )
    return parser


def _print_summary(summary: GenerationSummary) -> None:
    print("Documentación de tests generada.")
    print(f"Cambios detectados: {'sí' if summary.changed else 'no'}")
    if summary.written:
        print("Archivos escritos:")
        for path in summary.written:
            print(f"  + {path.relative_to(ROOT).as_posix()}")
    if summary.removed:
        print("Archivos eliminados:")
        for path in summary.removed:
            print(f"  - {path.relative_to(ROOT).as_posix()}")
    if summary.unchanged:
        print(f"Archivos sin cambios: {len(summary.unchanged)}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.check and args.force:
        parser.error("--check and --force cannot be used together")

    kinds = [args.only] if args.only else list(KIND_ORDER)
    summary = generate_docs(kinds, force=args.force, check=args.check)
    _print_summary(summary)
    return 1 if args.check and summary.changed else 0


def clear_markdown_dir(dir_path: Path) -> None:
    if not dir_path.exists():
        return
    for file_path in dir_path.glob("*.md"):
        file_path.unlink()


def write_gherkin_docs_compat(scenarios: list[dict]) -> None:
    write_gherkin_docs(scenarios)
