#!/usr/bin/env python3
"""
ci_local.py — Pipeline CI local con Docker para Postgres.

Replica .github/workflows/ci.yml ejecutando cada job localmente.
Muestra la salida en tiempo real y genera un reporte final con conteos
de tests, duración por stage y estado del pipeline.

Requisitos:
  - Docker Desktop corriendo (para stages con Postgres)
  - Entorno virtual presente en .venv/ con requirements/development.txt instalado

Uso:
  python scripts/ci_local/ci_local.py                        # pipeline completo
  python scripts/ci_local/ci_local.py --no-load              # sin Locust (más rápido)
  python scripts/ci_local/ci_local.py --from scenarios        # desde un stage en adelante
  python scripts/ci_local/ci_local.py --only quality unit_tests  # solo esos stages
  python scripts/ci_local/ci_local.py --skip seed_db          # omite un stage concreto
  python scripts/ci_local/ci_local.py --keep-container        # no elimina el contenedor al terminar

Salidas (en ci-local-out/<stage>/):
  output.log      — salida completa del stage
  junit.xml       — resultados pytest (para IDE / parsing)
  coverage.xml    — cobertura (stages que miden)
  locust_*.csv    — estadísticas de carga (solo load_test)
"""

from __future__ import annotations

import argparse
import atexit
import signal
import os
import platform
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "ci-local-out"

IS_WIN = platform.system() == "Windows"
VENV_BIN = ROOT / ".venv" / ("Scripts" if IS_WIN else "bin")
PYTHON = VENV_BIN / ("python.exe" if IS_WIN else "python")
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

# ── Docker / Postgres ──────────────────────────────────────────────────────────
PG_CONTAINER = "icm_ci_local_pg"
PG_IMAGE = "postgres:18"
# Puerto 15432 para evitar colisión con Postgres de desarrollo local (5432)
PG_PORT = 15432
DB_URL = f"postgres://icm:icm_pass@localhost:{PG_PORT}/icm_test"

# ── ANSI colors ────────────────────────────────────────────────────────────────
if IS_WIN:
    os.system("")  # habilita VT100 en Windows Console / PowerShell

_USE_COLOR = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def green(t: str) -> str:
    return _c(t, "32")


def red(t: str) -> str:
    return _c(t, "31")


def yellow(t: str) -> str:
    return _c(t, "33")


def cyan(t: str) -> str:
    return _c(t, "36")


def bold(t: str) -> str:
    return _c(t, "1")


def dim(t: str) -> str:
    return _c(t, "2")


# ── Data classes ───────────────────────────────────────────────────────────────
@dataclass
class StageResult:
    name: str
    display: str
    status: str = "pending"  # pass | fail | warn | skip | error
    duration: float = 0.0
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    notes: str = ""


# ── Utilities ──────────────────────────────────────────────────────────────────
def venv_tool(name: str) -> str:
    """Devuelve la ruta a una herramienta instalada en el venv."""
    for suffix in [".exe", ".cmd"] if IS_WIN else [""]:
        p = VENV_BIN / f"{name}{suffix}"
        if p.exists():
            return str(p)
    return name  # fallback al PATH del sistema


def run_cmd(
    cmd: list,
    env: Optional[dict] = None,
    log_path: Optional[Path] = None,
    stdin_path: Optional[Path] = None,
) -> int:
    """Ejecuta un comando transmitiendo salida a consola y al archivo de log."""
    full_env = {**os.environ, **(env or {})}
    log_fh = (
        open(log_path, "w", encoding="utf-8", errors="replace") if log_path else None
    )
    stdin_fh = open(stdin_path, "r", encoding="utf-8") if stdin_path else None
    try:
        proc = subprocess.Popen(
            [str(c) for c in cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=stdin_fh,
            env=full_env,
            cwd=str(ROOT),
            text=True,
            bufsize=1,
            errors="replace",
        )
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if log_fh:
                log_fh.write(line)
        proc.wait()
        return proc.returncode
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise
    finally:
        if log_fh:
            log_fh.close()
        if stdin_fh:
            stdin_fh.close()


def parse_junit(xml_path: Path) -> dict:
    """Extrae conteos de un archivo JUnit XML."""
    if not xml_path.exists():
        return {}
    try:
        root = ET.parse(xml_path).getroot()
        suites = root.findall("testsuite") if root.tag == "testsuites" else [root]
        total = errors = failures = skipped = 0
        for s in suites:
            total += int(s.get("tests", 0) or 0)
            errors += int(s.get("errors", 0) or 0)
            failures += int(s.get("failures", 0) or 0)
            skipped += int(s.get("skipped", 0) or 0)
        return {
            "total": total,
            "passed": total - errors - failures - skipped,
            "failed": failures + errors,
            "skipped": skipped,
        }
    except Exception:
        return {}


def _apply_junit(sr: StageResult, junit_path: Path) -> None:
    c = parse_junit(junit_path)
    sr.tests_total = c.get("total", 0)
    sr.tests_passed = c.get("passed", 0)
    sr.tests_failed = c.get("failed", 0)
    sr.tests_skipped = c.get("skipped", 0)


def banner(title: str) -> None:
    w = 66
    print()
    print(bold(cyan("─" * w)))
    print(bold(cyan(f"  {title}")))
    print(bold(cyan("─" * w)))


def step_label(name: str) -> None:
    print(dim(f"  ▶ {name}"))


# ── Docker helpers ─────────────────────────────────────────────────────────────
def _docker(*args: str) -> int:
    return subprocess.run(["docker"] + list(args), capture_output=True).returncode


def start_postgres() -> None:
    print(cyan(f"  Iniciando contenedor Postgres {PG_IMAGE} en puerto {PG_PORT}…"))
    _docker("rm", "-f", PG_CONTAINER)
    rc = _docker(
        "run",
        "-d",
        "--name",
        PG_CONTAINER,
        "-e",
        "POSTGRES_DB=icm_test",
        "-e",
        "POSTGRES_USER=icm",
        "-e",
        "POSTGRES_PASSWORD=icm_pass",
        "-p",
        f"{PG_PORT}:5432",
        PG_IMAGE,
    )
    if rc != 0:
        print(
            red("  ✗ No se pudo iniciar el contenedor. ¿Está Docker Desktop corriendo?")
        )
        sys.exit(1)

    print("  Esperando a Postgres", end="", flush=True)
    for i in range(40):
        r = subprocess.run(
            ["docker", "exec", PG_CONTAINER, "pg_isready", "-U", "icm"],
            capture_output=True,
        )
        if r.returncode == 0:
            print(green(f" listo ({i + 1}s)"))
            return
        time.sleep(1)
        print(".", end="", flush=True)

    print(red("\n  ✗ Postgres no quedó listo a tiempo"))
    sys.exit(1)


def stop_postgres() -> None:
    _docker("rm", "-f", PG_CONTAINER)
    print(dim("  Contenedor Postgres eliminado."))


def _cleanup_on_interrupt(signum, frame):
    """Handler SIGINT/SIGTERM: elimina contenedor Docker y sale."""
    print(red("\n  CTRL+C detectado — limpiando contenedor Postgres…"))
    stop_postgres()
    sys.exit(130)


# ── Entornos por stage ─────────────────────────────────────────────────────────
def _env(settings: str, db_url: str = "", extra: Optional[dict] = None) -> dict:
    e: dict = {"DJANGO_SETTINGS_MODULE": settings}
    if db_url:
        e["DATABASE_URL"] = db_url
    if extra:
        e.update(extra)
    return e


def _test_env() -> dict:
    return _env("config.settings.test")


def _pg_env() -> dict:
    return _env("config.settings.test", DB_URL)


def _load_env() -> dict:
    return _env("config.settings.loadtest", DB_URL)


# ── Función auxiliar: migraciones ──────────────────────────────────────────────
def _migrate(out: Path, env: dict, tag: str = "") -> bool:
    label = f"migrate" + (f" ({tag})" if tag else "")
    step_label(label)
    rc = run_cmd(
        [str(PYTHON), "manage.py", "migrate", "--noinput"],
        env=env,
        log_path=out / "migrate.log",
    )
    if rc != 0:
        print(red("  ✗ Migración falló"))
    return rc == 0


# ── Stage: quality ─────────────────────────────────────────────────────────────
def stage_quality(sr: StageResult, out: Path) -> None:
    env = _test_env()
    steps: list[tuple[str, list, bool]] = [
        ("ruff check", [venv_tool("ruff"), "check", "apps/", "shared/"], True),
        (
            "ruff format --check",
            [venv_tool("ruff"), "format", "--check", "apps/", "shared/"],
            True,
        ),
        (
            "semgrep / security scan",
            [
                str(PYTHON),
                "scripts/security/run_security_scan.py",
                "--ci",
                "--skip",
                "pip-audit",
            ],
            True,
        ),
        ("bandit", [venv_tool("bandit"), "-r", "apps", "shared", "-ll"], True),
        (
            "pip-audit",
            [venv_tool("pip-audit"), "--progress=off"],
            False,
        ),  # informativo — no bloquea
        (
            "migrations check",
            [str(PYTHON), "manage.py", "makemigrations", "--check", "--dry-run"],
            True,
        ),
        ("docs check", [str(PYTHON), "-m", "scripts.generate_docs", "--check"], True),
        (
            "mypy",
            [
                venv_tool("mypy"),
                "apps/",
                "shared/",
                "--ignore-missing-imports",
                "--no-error-summary",
            ],
            True,
        ),
    ]

    warned = False
    for name, cmd, fatal in steps:
        step_label(name)
        rc = run_cmd(
            cmd,
            env=env,
            log_path=out / f"{name.replace(' ', '_').replace('/', '_')}.log",
        )
        if rc != 0:
            if fatal:
                sr.status = "fail"
                sr.notes = f"falló en: {name}"
                return
            warned = True
            print(yellow(f"  ⚠ {name} falló (no bloqueante)"))

    sr.status = "warn" if warned else "pass"


# ── Stage: unit_tests ──────────────────────────────────────────────────────────
def stage_unit_tests(sr: StageResult, out: Path) -> None:
    junit = out / "junit.xml"
    rc = run_cmd(
        [
            venv_tool("pytest"),
            "apps/",
            "-q",
            "--ignore=tests",
            f"--junitxml={junit}",
            "--cov=apps",
            f"--cov-report=xml:{out / 'coverage.xml'}",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
        ],
        env=_test_env(),
        log_path=out / "output.log",
    )
    _apply_junit(sr, junit)
    sr.status = "pass" if rc == 0 else "fail"


# ── Stage: integration_tests ───────────────────────────────────────────────────
def stage_integration_tests(sr: StageResult, out: Path) -> None:
    junit = out / "junit.xml"
    rc = run_cmd(
        [
            venv_tool("pytest"),
            "tests/integration",
            "tests/scripts",
            "tests/shared",
            "tests/test_service_sla.py",
            "-q",
            "--ignore=tests/scripts/test_perf_locustfile.py",
            f"--junitxml={junit}",
            "--cov=apps",
            f"--cov-report=xml:{out / 'coverage.xml'}",
        ],
        env=_test_env(),
        log_path=out / "output.log",
    )
    _apply_junit(sr, junit)
    sr.status = "pass" if rc == 0 else "fail"


# ── Stage: scenarios ───────────────────────────────────────────────────────────
def stage_scenarios(sr: StageResult, out: Path) -> None:
    env = _pg_env()
    if not _migrate(out, env, "scenarios"):
        sr.status = "fail"
        return
    junit = out / "junit.xml"
    rc = run_cmd(
        [
            venv_tool("pytest"),
            "tests/ers",
            "-q",
            f"--junitxml={junit}",
            "--cov=apps",
            f"--cov-report=xml:{out / 'coverage.xml'}",
        ],
        env=env,
        log_path=out / "output.log",
    )
    _apply_junit(sr, junit)
    sr.status = "pass" if rc == 0 else "fail"


# ── Stage: seed_db ─────────────────────────────────────────────────────────────
def stage_seed_db(sr: StageResult, out: Path) -> None:
    env = _pg_env()
    if not _migrate(out, env, "seed_db"):
        sr.status = "fail"
        return
    junit = out / "junit.xml"
    rc = run_cmd(
        [
            venv_tool("pytest"),
            "tests/scripts/test_seed_db.py",
            "-q",
            f"--junitxml={junit}",
        ],
        env=env,
        log_path=out / "output.log",
    )
    _apply_junit(sr, junit)
    sr.status = "pass" if rc == 0 else "fail"


# ── Stage: security_tests ──────────────────────────────────────────────────────
def stage_security_tests(sr: StageResult, out: Path) -> None:
    env = _pg_env()
    if not _migrate(out, env, "security"):
        sr.status = "fail"
        return
    junit = out / "junit.xml"
    rc = run_cmd(
        [
            venv_tool("pytest"),
            "tests/security/",
            "-v",
            f"--junitxml={junit}",
            "--cov=apps",
            f"--cov-report=xml:{out / 'coverage.xml'}",
        ],
        env=env,
        log_path=out / "output.log",
    )
    _apply_junit(sr, junit)
    sr.status = "pass" if rc == 0 else "fail"


# ── Stage: concurrency_tests ───────────────────────────────────────────────────
def stage_concurrency_tests(sr: StageResult, out: Path) -> None:
    env = _pg_env() | {"RUN_CONCURRENCY_TESTS": "1"}
    if not _migrate(out, env, "concurrency"):
        sr.status = "fail"
        return
    junit = out / "junit.xml"
    rc = run_cmd(
        [
            venv_tool("pytest"),
            "tests/concurrency",
            "-v",
            f"--junitxml={junit}",
        ],
        env=env,
        log_path=out / "output.log",
    )
    _apply_junit(sr, junit)
    sr.status = "pass" if rc == 0 else "fail"


# ── Stage: load_test ───────────────────────────────────────────────────────────
_SEED_SCRIPT = """\
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.authentication.models import UserRole, TemporaryAccessPermit

User = get_user_model()
for username, role, email in [
    ("almacenista",   UserRole.ALMACENISTA,        "almacenista@icm.local"),
    ("auxiliar",      UserRole.AUXILIAR_DESPACHO,   "auxiliar@icm.local"),
    ("administrador", UserRole.ADMINISTRADOR,        "administrador@icm.local"),
]:
    u, _ = User.objects.get_or_create(
        username=username, defaults={"email": email, "role": role}
    )
    if not u.has_usable_password():
        u.set_password("testpass123")
        u.save()

almacenista = User.objects.get(username="almacenista")
auxiliar    = User.objects.get(username="auxiliar")
now = timezone.now()
if not TemporaryAccessPermit.objects.filter(
    user=auxiliar, allow_24_7=True, is_active=True
).exists():
    TemporaryAccessPermit.objects.create(
        user=auxiliar,
        start_datetime=now - timedelta(hours=1),
        end_datetime=now + timedelta(hours=2),
        allow_24_7=True,
        reason="ci_local load test",
        granted_by=almacenista,
    )
print("Usuarios listos para el load test.")
"""


def _wait_for_port(
    host: str = "localhost", port: int = 8000, timeout: int = 30
) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _sla_check(out: Path, sr: StageResult) -> None:
    import csv as _csv

    stats = next(out.glob("locust_stats.csv"), None)
    if not stats:
        print(dim("  No se encontró CSV de Locust — SLA check omitido"))
        return
    violations: list[str] = []
    with open(stats) as f:
        for row in _csv.DictReader(f):
            name = row.get("Name", "")
            if name in ("Aggregated", ""):
                continue
            total = float(row.get("Request Count", 1) or 1)
            fail = float(row.get("Failure Count", 0) or 0)
            p95 = float(row.get("95%", 0) or 0)
            if total > 0 and fail / total * 100 > 1.0:
                violations.append(f"fail_ratio > 1%   ← {name}")
            if p95 > 500:
                violations.append(f"p95 = {p95:.0f}ms > 500ms ← {name}")
    if violations:
        print(yellow(f"  ⚠ {len(violations)} SLA violation(s) (informativo):"))
        for v in violations:
            print(yellow(f"    {v}"))
        sr.notes = f"{len(violations)} SLA violations"
        if sr.status == "pass":
            sr.status = "warn"
    else:
        print(green("  Todos los SLAs OK"))


def stage_load_test(sr: StageResult, out: Path) -> None:
    env = _load_env()

    if not _migrate(out, env, "load"):
        sr.status = "fail"
        return

    # Seed usuarios de prueba
    step_label("seed usuarios (almacenista / auxiliar / administrador)")
    seed_file = out / "_seed_users.py"
    seed_file.write_text(_SEED_SCRIPT, encoding="utf-8")
    # manage.py shell -c "exec(open(...))" — cross-platform, no escaping issues
    rc = run_cmd(
        [
            str(PYTHON),
            "manage.py",
            "shell",
            "-c",
            f"exec(open(r'{seed_file}', encoding='utf-8').read())",
        ],
        env=env,
        log_path=out / "seed.log",
    )
    if rc != 0:
        sr.status = "fail"
        sr.notes = "seed de usuarios falló"
        return

    # Iniciar servidor Django en background
    step_label("iniciar Django runserver :8000")
    server_log_path = out / "server.log"
    server_log = open(server_log_path, "w", encoding="utf-8")
    server_env = {**os.environ, **env}
    server_proc = subprocess.Popen(
        [
            str(PYTHON),
            "manage.py",
            "runserver",
            "0.0.0.0:8000",
            "--noreload",
            "--settings=config.settings.loadtest",
        ],
        stdout=server_log,
        stderr=server_log,
        env=server_env,
        cwd=str(ROOT),
    )

    try:
        print("  Esperando Django", end="", flush=True)
        if not _wait_for_port(timeout=30):
            print(red(" timeout"))
            sr.status = "fail"
            sr.notes = "el servidor Django no arrancó a tiempo"
            return
        print(green(" listo"))

        # Locust
        step_label("locust — 12 usuarios, 45s, 3 roles")
        csv_prefix = str(out / "locust")
        rc = run_cmd(
            [
                venv_tool("locust"),
                "-f",
                "tests/performance/locustfile.py",
                "--headless",
                "-H",
                "http://localhost:8000",
                "-u",
                "12",
                "-r",
                "3",
                "--run-time",
                "45s",
                "--only-summary",
                f"--csv={csv_prefix}",
            ],
            env={**os.environ, **env},
            log_path=out / "locust.log",
        )

        sr.status = "pass" if rc == 0 else "fail"

        # SLA check (informativo)
        step_label("SLA check")
        _sla_check(out, sr)

    finally:
        server_proc.terminate()
        server_proc.wait()
        server_log.close()


# ── Definición del pipeline ────────────────────────────────────────────────────
#  (name, display, needs_postgres, fn)
PIPELINE: list[tuple[str, str, bool, Callable]] = [
    ("quality", "Quality — lint · format · SAST · docs", False, stage_quality),
    ("unit_tests", "Unit tests (SQLite)", False, stage_unit_tests),
    (
        "integration_tests",
        "Integration tests (scripts + root)",
        False,
        stage_integration_tests,
    ),
    ("scenarios", "Scenarios / Gherkin (Postgres)", True, stage_scenarios),
    ("seed_db", "Seed DB tests (Postgres)", True, stage_seed_db),
    ("security_tests", "Security tests — OWASP (Postgres)", True, stage_security_tests),
    (
        "concurrency_tests",
        "Concurrency tests (Postgres)",
        True,
        stage_concurrency_tests,
    ),
    ("load_test", "Load test — Locust (Postgres)", True, stage_load_test),
]
STAGE_NAMES = [s[0] for s in PIPELINE]
STAGE_MAP = {s[0]: s for s in PIPELINE}


# ── main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ci_local",
        description="CI local — replica .github/workflows/ci.yml con Docker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
stages disponibles (en orden):
  quality  unit_tests  integration_tests  scenarios
  seed_db  security_tests  concurrency_tests  load_test

ejemplos:
  python scripts/ci_local/ci_local.py
  python scripts/ci_local/ci_local.py --no-load
  python scripts/ci_local/ci_local.py --from scenarios
  python scripts/ci_local/ci_local.py --only quality unit_tests integration_tests
  python scripts/ci_local/ci_local.py --skip seed_db --no-load
        """,
    )
    parser.add_argument(
        "--no-load", action="store_true", help="Omitir load test (Locust) — más rápido"
    )
    parser.add_argument(
        "--from",
        dest="from_stage",
        metavar="STAGE",
        choices=STAGE_NAMES,
        help="Empezar desde este stage",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="STAGE",
        choices=STAGE_NAMES,
        help="Ejecutar solo estos stages",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        default=[],
        metavar="STAGE",
        choices=STAGE_NAMES,
        help="Omitir estos stages",
    )
    parser.add_argument(
        "--keep-container",
        action="store_true",
        help="No eliminar el contenedor Postgres al terminar",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Desactivar colores ANSI"
    )
    args = parser.parse_args()

    global _USE_COLOR
    if args.no_color:
        _USE_COLOR = False

    # Calcular stages activos
    active = STAGE_NAMES[:]
    if args.only:
        active = [s for s in STAGE_NAMES if s in args.only]
    elif args.from_stage:
        active = STAGE_NAMES[STAGE_NAMES.index(args.from_stage) :]
    skip_set = set(args.skip)
    if args.no_load:
        skip_set.add("load_test")
    active = [s for s in active if s not in skip_set]

    if not active:
        print(yellow("No hay stages que ejecutar. Revisa --only / --skip."))
        sys.exit(0)

    # Verificar venv
    if not PYTHON.exists():
        print(red(f"  Python no encontrado: {PYTHON}"))
        print("  Crea el entorno virtual primero:")
        print("    python -m venv .venv")
        print("    .venv\\Scripts\\pip install -r requirements/development.txt")
        sys.exit(1)

    # Verificar Docker si hay stages con Postgres
    needs_pg = any(STAGE_MAP[n][2] for n in active)
    if needs_pg:
        try:
            rc = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=10
            ).returncode
        except (subprocess.TimeoutExpired, FileNotFoundError):
            rc = 1
        if rc != 0:
            print(
                red(
                    "  Docker no está corriendo. Inicia Docker Desktop y vuelve a intentarlo."
                )
            )
            sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)

    w = 66
    print()
    print(bold("═" * w))
    print(bold("  CI LOCAL — Sistema Inventario ICM"))
    print(bold(f"  Python : {PYTHON}"))
    print(bold(f"  Stages : {' → '.join(active)}"))
    if needs_pg:
        print(bold(f"  Postgres: localhost:{PG_PORT} (contenedor {PG_CONTAINER})"))
    print(bold("═" * w))

    # Iniciar Postgres
    if needs_pg:
        start_postgres()
        if not args.keep_container:
            atexit.register(stop_postgres)
            signal.signal(signal.SIGINT, _cleanup_on_interrupt)
            signal.signal(signal.SIGTERM, _cleanup_on_interrupt)

    # Ejecutar stages
    results: list[StageResult] = []
    pipeline_ok = True
    t_pipeline_start = time.time()
    n_total = len(active)

    for idx, stage_name in enumerate(active, 1):
        _, display, _, fn = STAGE_MAP[stage_name]
        sr = StageResult(name=stage_name, display=display)
        results.append(sr)

        stage_out = OUT_DIR / stage_name
        stage_out.mkdir(exist_ok=True)

        elapsed = time.time() - t_pipeline_start
        pct = idx * 100 // n_total
        progress = f"[{idx}/{n_total}] {pct}%"
        print()
        print(dim(f"  ── Progreso: {green(progress)} ──"))
        banner(f"[{stage_name.upper()}]  {display}")

        t0 = time.time()
        try:
            fn(sr, stage_out)
        except KeyboardInterrupt:
            sr.status = "fail"
            sr.notes = "interrumpido"
            pipeline_ok = False
            print(red("\n  Interrumpido — se detiene el pipeline"))
            break
        except Exception as exc:
            sr.status = "fail"
            sr.notes = str(exc)[:80]
            print(red(f"  Excepción inesperada: {exc}"))
        sr.duration = time.time() - t0

        icon = {"pass": green("✓"), "fail": red("✗"), "warn": yellow("⚠")}.get(
            sr.status, dim("–")
        )
        print(f"\n  {icon} {sr.display}  ({sr.duration:.1f}s)")

        if sr.status == "fail":
            pipeline_ok = False

    total_dur = time.time() - t_pipeline_start

    # ── Reporte final ──────────────────────────────────────────────────────────
    n_pass = sum(1 for r in results if r.status == "pass")
    n_warn = sum(1 for r in results if r.status == "warn")
    n_fail = sum(1 for r in results if r.status == "fail")
    t_total = sum(r.tests_total for r in results)
    t_passed = sum(r.tests_passed for r in results)
    t_failed = sum(r.tests_failed for r in results)
    t_skipped = sum(r.tests_skipped for r in results)

    print()
    print(bold("═" * w))
    print(bold("  REPORTE FINAL — CI LOCAL"))
    print(bold("═" * w))

    for r in results:
        icon = {"pass": green("✓"), "fail": red("✗"), "warn": yellow("⚠")}.get(
            r.status, dim("–")
        )
        dur = f"{r.duration:6.1f}s"
        tc = (
            (
                f"  [{green(str(r.tests_passed))}✓ "
                f"{(red if r.tests_failed else dim)(str(r.tests_failed))}✗ "
                f"{dim(str(r.tests_skipped))}–]"
            )
            if r.tests_total
            else ""
        )
        note = f"  {dim(r.notes)}" if r.notes else ""
        print(f"  {icon}  {r.display:<46}{dur}{tc}{note}")

    print(bold("─" * w))

    if n_fail == 0 and n_warn == 0:
        overall = green("✓ TODOS LOS STAGES PASARON")
    elif n_fail == 0:
        overall = yellow(f"✓ PASÓ — {n_warn} aviso(s) no bloqueantes")
    else:
        overall = red(f"✗ {n_fail} STAGE(S) FALLARON")

    run_label = f"{n_pass + n_warn}/{len(results)} stages OK"
    print(f"  {overall}   {run_label}   {total_dur:.0f}s total")

    if t_total:
        print(
            f"  Pruebas: {t_total} total · "
            f"{green(str(t_passed))} pasaron · "
            f"{(red if t_failed else dim)(str(t_failed))} fallaron · "
            f"{dim(str(t_skipped))} saltadas"
        )

    print(f"  Logs detallados: {OUT_DIR}")
    print(bold("═" * w))
    print()

    sys.exit(0 if pipeline_ok else 1)


if __name__ == "__main__":
    main()
