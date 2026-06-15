#!/usr/bin/env python3
"""
Escaneo integral de calidad y seguridad para Sistema Inventario ICM.

Ejecuta herramientas de calidad de forma selectiva o completa.
Genera un reporte consolidado en texto plano.

Uso:
    python scripts/security/run_security_scan.py              # todas las herramientas
    python scripts/security/run_security_scan.py --only ruff  # solo ruff
    python scripts/security/run_security_scan.py --skip mypy  # todas menos mypy
    python scripts/security/run_security_scan.py --list       # listar herramientas
    python scripts/security/run_security_scan.py --ci         # modo CI
    python scripts/security/run_security_scan.py --dry-run    # modo simulación
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPORTS_DIR = Path(__file__).resolve().parent / "reports"

TOOLS: list[dict] = [
    {
        "name": "ruff lint",
        "cmd": ["ruff", "check", "apps/", "shared/", "config/"],
        "desc": "Linting Python (ruff)",
    },
    {
        "name": "ruff format",
        "cmd": ["ruff", "format", "--check", "apps/", "shared/", "config/"],
        "desc": "Formato Python (ruff format)",
    },
    {
        "name": "semgrep",
        "cmd": [
            "semgrep",
            "scan",
            "--config",
            "auto",
            "--include=*.py",
            "apps/",
            "shared/",
        ],
        "ci_flags": ["--quiet", "--error"],
        "desc": "SAST (Semgrep Registry)",
    },
    {
        "name": "bandit",
        "cmd": ["bandit", "-r", "apps", "shared", "-ll"],
        "desc": "SAST (Bandit)",
    },
    {
        "name": "pip-audit",
        "cmd": ["pip-audit", "--progress=off"],
        "desc": "Supply-chain (pip-audit)",
    },
    {
        "name": "mypy",
        "cmd": [
            "mypy",
            "apps/",
            "shared/",
            "--ignore-missing-imports",
            "--no-error-summary",
            "--show-error-codes",
        ],
        "desc": "Tipado estático (mypy)",
    },
]

_TOOL_NAMES = {t["name"] for t in TOOLS}


def _sanitize(text: str) -> str:
    """Strip Unicode box-drawing and checkmark characters for plain-text reports."""
    import re

    text = re.sub(r"[\u2500-\u257f]", "", text)
    text = re.sub(r"[\u2705\u274c]", "", text)
    return text


def _resolve_tools(only: str, skip: str) -> list[dict]:
    only_set = {s.strip() for s in only.split(",") if s.strip()}
    skip_set = {s.strip() for s in skip.split(",") if s.strip()}

    if only_set:
        unknown = only_set - _TOOL_NAMES
        if unknown:
            print(f"[ERROR] Herramientas desconocidas: {', '.join(sorted(unknown))}")
            print(f"        Disponibles: {', '.join(sorted(_TOOL_NAMES))}")
            raise SystemExit(2)
        return [t for t in TOOLS if t["name"] in only_set]

    if skip_set:
        unknown = skip_set - _TOOL_NAMES
        if unknown:
            print(f"[ERROR] Herramientas desconocidas: {', '.join(sorted(unknown))}")
            print(f"        Disponibles: {', '.join(sorted(_TOOL_NAMES))}")
            raise SystemExit(2)
        return [t for t in TOOLS if t["name"] not in skip_set]

    return list(TOOLS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Escaneo integral de calidad y seguridad -- Sistema Inventario ICM",
    )
    parser.add_argument(
        "--output",
        default=str(_REPORTS_DIR / "reporte_calidad.txt"),
        help=f"Ruta del archivo de reporte (default: {_REPORTS_DIR / 'reporte_calidad.txt'})",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Ejecutar solo estas herramientas separadas por coma (ej: ruff,bandit)",
    )
    parser.add_argument(
        "--skip",
        default="",
        help="Saltar estas herramientas separadas por coma (ej: pip-audit,mypy)",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Modo CI: salida compacta, exit code 0 si todas pasan",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra los comandos sin ejecutarlos",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista las herramientas disponibles y sale",
    )
    return parser


def _run_tool(
    name: str,
    cmd: list[str],
    desc: str,
    dry_run: bool,
    ci: bool = False,
    ci_flags: list[str] | None = None,
) -> tuple[bool, str]:
    effective_cmd = list(cmd)
    if ci and ci_flags:
        effective_cmd.extend(ci_flags)

    label = f"  [RUN]  {desc} ..."

    if dry_run:
        return True, f"{label}\n         {' '.join(effective_cmd)}"

    try:
        result = subprocess.run(
            effective_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        ok = result.returncode == 0
        if ok:
            raw = result.stdout or result.stderr or "(sin salida)"
            return True, f"{label}  OK\n{raw.strip()}"
        else:
            stdout = result.stdout.strip() if result.stdout.strip() else ""
            stderr = result.stderr.strip() if result.stderr.strip() else ""
            combined = "\n".join(filter(None, [stdout, stderr]))
            msg = combined or f"exit code {result.returncode}"
            return False, f"{label}  FAIL (code {result.returncode})\n{msg}"
    except FileNotFoundError:
        return False, f"{label}  NOT FOUND - {desc}. Comando: {' '.join(cmd)}"


def run_scan(args: argparse.Namespace) -> int:
    if args.list:
        print("Herramientas disponibles:")
        for t in TOOLS:
            print(f"  {t['name']:20s}  {t['desc']}")
        return 0

    if args.only and args.skip:
        print("[ERROR] No puedes usar --only y --skip al mismo tiempo.")
        return 2

    tools_to_run = _resolve_tools(args.only, args.skip)
    output_path = Path(args.output)

    report_lines: list[str] = []
    report_lines.append("=" * 72)
    report_lines.append("  Escaneo Integral de Calidad y Seguridad")
    report_lines.append("  Sistema Inventario ICM")
    report_lines.append("=" * 72)
    report_lines.append(f"  Inicio:    {datetime.now():%Y-%m-%d %H:%M:%S}")
    report_lines.append(f"  Modo:      {'CI' if args.ci else 'local'}")
    if args.only:
        report_lines.append(f"  Solo:      {args.only}")
    if args.skip:
        report_lines.append(f"  Skip:      {args.skip}")
    report_lines.append(f"  Reporte:   {output_path}")
    report_lines.append("")

    header = "\n".join(report_lines)
    print(header)

    all_ok = True
    results: list[tuple[str, bool, str]] = []

    for tool in tools_to_run:
        ok, output = _run_tool(
            tool["name"],
            tool["cmd"],
            tool["desc"],
            args.dry_run,
            args.ci,
            tool.get("ci_flags"),
        )
        if not ok:
            all_ok = False
        results.append((tool["name"], ok, output))
        print(output)
        print()

    summary_parts: list[str] = []
    summary_parts.append("")
    summary_parts.append("  Resumen por herramienta:")
    summary_parts.append(f"  {'HERRAMIENTA':20s} {'ESTADO':10s}")
    summary_parts.append(f"  {'-' * 20} {'-' * 10}")
    for tool_name, ok, _ in results:
        status = "[OK]" if ok else "[FAIL]"
        summary_parts.append(f"  {tool_name:20s} {status:10s}")
    summary_parts.append("")
    summary_text = "\n".join(summary_parts)

    summary_line = f"  {'[OK]' if all_ok else '[FAIL]'}  Resultado: {'TODAS PASARON' if all_ok else 'ALGUNAS FALLARON'}"
    print(summary_text)
    print(summary_line)
    print(f"  Finalizado: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 72)

    for _, _, output in results:
        report_lines.append(output)
    report_lines.append(summary_text)
    report_lines.append(summary_line)
    report_lines.append(f"  Finalizado: {datetime.now():%Y-%m-%d %H:%M:%S}")
    report_lines.append("=" * 72)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n  Reporte guardado: {output_path.resolve()}")

    return 0 if all_ok else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run_scan(args)


if __name__ == "__main__":
    raise SystemExit(main())
