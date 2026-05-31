"""Management command para escaneo periódico de alertas (RF-011).

Uso:
    python manage.py scan_alerts
    python manage.py scan_alerts --types expiry,stock,location
    python manage.py scan_alerts --dry-run
    python manage.py scan_alerts --strict   # exit 1 si algún escaneo falla

Diseñado para ejecutarse desde un cron externo o CI/CD al menos una vez al día.
Idempotente: ejecutarlo múltiples veces no duplica alertas.
Por defecto retorna exit code 0 para no interrumpir procesos automatizados.
Usa --strict para propagar fallos al scheduler.
"""

from __future__ import annotations

import logging
import sys

from django.core.management.base import BaseCommand

from apps.alerts.services import (
    scan_all_expiry_alerts,
    scan_all_location_alerts,
    scan_all_stock_alerts,
)

logger = logging.getLogger(__name__)

VALID_TYPES = {"expiry", "stock", "location"}


class Command(BaseCommand):
    help = "Escanea alertas de inventario (vencimiento, stock, ubicaciones bloqueadas)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--types",
            type=str,
            default="expiry,stock,location",
            help="Tipos a escanear separados por coma: expiry,stock,location (default: todos)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Simula el escaneo sin crear ni resolver alertas",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            default=False,
            help="Retorna exit code 1 si algún escaneo falla (default: siempre exit 0)",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        strict: bool = options["strict"]
        requested = {
            t.strip().lower() for t in options["types"].split(",") if t.strip()
        }
        unknown = requested - VALID_TYPES
        if unknown:
            self.stderr.write(
                self.style.WARNING(
                    f"Tipos desconocidos ignorados: {', '.join(sorted(unknown))}"
                )
            )
        active_types = requested & VALID_TYPES

        mode = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            f"{mode}Iniciando scan_alerts — tipos: {', '.join(sorted(active_types))}"
        )

        scan_errors: list[str] = []

        def _run(label: str, fn, **kwargs):
            try:
                n = fn(**kwargs)
                self.stdout.write(f"  {label:<10} -> {n} procesados")
            except Exception as exc:
                logger.exception("scan_alerts[%s] falló", label)
                self.stderr.write(self.style.ERROR(f"  {label:<10} -> ERROR: {exc}"))
                scan_errors.append(label)

        if "expiry" in active_types:
            _run("expiry", scan_all_expiry_alerts, dry_run=dry_run)
        if "stock" in active_types:
            _run("stock", scan_all_stock_alerts, dry_run=dry_run)
        if "location" in active_types:
            _run("location", scan_all_location_alerts, dry_run=dry_run)

        if scan_errors:
            self.stderr.write(
                self.style.ERROR(
                    f"{mode}scan_alerts completado con errores: {', '.join(scan_errors)}"
                )
            )
            if strict:
                sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS(f"{mode}scan_alerts completado."))
