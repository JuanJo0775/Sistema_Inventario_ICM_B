#!/usr/bin/env python3
"""
Menu para generación de documentación de tests.

Uso:
  python scripts/generate_docs/menu.py --type unit|integration|gherkin|all

Por defecto concatena los MD generados y escribe `docs/test/all_<type>.md`.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts" / "generate_docs"

GEN_MAP = {
    "unit": SCRIPTS_DIR / "generate_unit_test_docs.py",
    "integration": SCRIPTS_DIR / "generate_integration_test_docs.py",
    "gherkin": SCRIPTS_DIR / "generate_gherkin_test_docs.py",
}

OUT_DIR_MAP = {
    "unit": ROOT / "docs" / "test" / "unit",
    "integration": ROOT / "docs" / "test" / "integration",
    "gherkin": ROOT / "docs" / "test" / "scenarios",
}


def hash_file(p: Path) -> str:
    h = hashlib.sha1()
    data = p.read_bytes()
    h.update(data)
    return h.hexdigest()


def snapshot(dirp: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not dirp.exists():
        return out
    for f in sorted(dirp.glob("*.md")):
        try:
            out[f.as_posix()] = hash_file(f)
        except Exception:
            out[f.as_posix()] = ""
    return out


def run_generator(script: Path) -> int:
    print(f"Ejecutando generador: {script.name}")
    env = os.environ.copy()
    # ensure generators can import scripts package
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run([sys.executable, str(script)], cwd=str(ROOT), env=env).returncode


def run_powershell_concat() -> int:
    ps = ROOT / "scripts" / "concat_md.ps1"
    if not ps.exists():
        print("PowerShell concat script not found:", ps)
        return 1
    print("Ejecutando concat_md.ps1 para generar all_*.md")
    # Use pwsh if available on PATH
    cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps)]
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def compare_snapshots(before: Dict[str, str], after: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    created = [p for p in after.keys() if p not in before]
    removed = [p for p in before.keys() if p not in after]
    updated = [p for p in after.keys() if p in before and before[p] != after[p]]
    unchanged = [p for p in after.keys() if p in before and before[p] == after[p]]
    return created, updated, unchanged


def concat_md(src_dir: Path, out_file: Path) -> None:
    md_files = sorted(
        [p for p in src_dir.glob("*.md") if p.name != "index.md" and not p.name.startswith("all_") and not p.name.endswith("_index.md")]
    )
    if not md_files:
        if out_file.exists():
            out_file.unlink()
        return
    parts: List[str] = []
    for p in md_files:
        parts.append(f"<!-- {p.name} -->\n")
        parts.append(p.read_text(encoding="utf-8"))
        parts.append("\n\n---\n\n")
    out_file.write_text("".join(parts), encoding="utf-8")


def main() -> None:
    import argparse

    # If no CLI args provided, present simple terminal menu
    if len(sys.argv) == 1:
        while True:
            print("\n=== Generador de documentación de tests ===")
            print("1) Unitarias")
            print("2) Integración")
            print("3) Escenarios (Gherkin)")
            print("4) Todo (unit/integration/gherkin)")
            print("5) Salir")
            choice = input("Elige una opción [1-5]: ").strip()
            if choice == "5":
                print("Saliendo.")
                return
            map_choice = {"1": ["unit"], "2": ["integration"], "3": ["gherkin"], "4": ["unit", "integration", "gherkin"]}
            kinds = map_choice.get(choice)
            if not kinds:
                print("Opción no válida, intenta de nuevo.")
                continue
            no_concat = False
            # run selected kinds
            for kind in kinds:
                out_dir = OUT_DIR_MAP[kind]
                before = snapshot(out_dir)
                script = GEN_MAP[kind]
                if not script.exists():
                    print(f"Generador no encontrado para {kind}: {script}")
                    continue
                rc = run_generator(script)
                if rc != 0:
                    print(f"El generador {script.name} salió con código {rc}")
                after = snapshot(out_dir)
                created, updated, unchanged = compare_snapshots(before, after)
                print(f"{kind}: creados={len(created)} actualizados={len(updated)} iguales={len(unchanged)}")
            # run PowerShell concat to produce all_*.md
            rc2 = run_powershell_concat()
            if rc2 != 0:
                print("Warning: concat_md.ps1 salió con código", rc2)
            else:
                print("Concatenación completa: docs/test/all_*.md y tests/all_scenarios.md actualizados.")
            # loop back to menu
        # end interactive menu

    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["unit", "integration", "gherkin", "all"], default="all")
    parser.add_argument("--no-concat", action="store_true", help="No concatenar después de generar")
    args = parser.parse_args()

    kinds = [args.type] if args.type != "all" else ["unit", "integration", "gherkin"]

    overall_created: Dict[str, List[str]] = {}
    overall_updated: Dict[str, List[str]] = {}
    overall_unchanged: Dict[str, List[str]] = {}

    for kind in kinds:
        out_dir = OUT_DIR_MAP[kind]
        before = snapshot(out_dir)
        script = GEN_MAP[kind]
        if not script.exists():
            print(f"Generador no encontrado para {kind}: {script}")
            continue
        rc = run_generator(script)
        if rc != 0:
            print(f"El generador {script.name} salió con código {rc}")
        after = snapshot(out_dir)
        created, updated, unchanged = compare_snapshots(before, after)  # removed ignored
        overall_created[kind] = created
        overall_updated[kind] = updated
        overall_unchanged[kind] = unchanged
        print(f"{kind}: creados={len(created)} actualizados={len(updated)} iguales={len(unchanged)}")
        # concatenar si corresponde
        if not args.no_concat:
            if kind == "gherkin":
                out_file = ROOT / "docs" / "test" / "all_scenarios.md"
                src_dir = out_dir
            else:
                out_file = ROOT / "docs" / "test" / f"all_{kind}.md"
                src_dir = out_dir
            concat_md(src_dir, out_file)
            print(f"Concatenado {src_dir} -> {out_file}")

    # resumen final
    print("\nResumen por tipo:")
    for kind in kinds:
        print(f"\n== {kind} ==")
        print("Creados:")
        for p in overall_created.get(kind, []):
            print(f"  + {p}")
        print("Actualizados:")
        for p in overall_updated.get(kind, []):
            print(f"  * {p}")
        print("Sin cambios:")
        for p in overall_unchanged.get(kind, []):
            print(f"    {p}")


if __name__ == "__main__":
    main()
