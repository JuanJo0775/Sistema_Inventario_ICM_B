"""Management command para escaneo periódico de alertas (RF-011).

Uso:
    python manage.py scan_alerts
    python manage.py scan_alerts --types expiry,stock,location
    python manage.py scan_alerts --dry-run

Diseñado para ejecutarse desde un cron externo o CI/CD al menos una vez al día.
Idempotente: ejecutarlo múltiples veces no duplica alertas.
Siempre retorna exit code 0 para no interrumpir procesos automatizados.
"""

from __future__ import annotations

import logging

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

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
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

        try:
            if "expiry" in active_types:
                n = scan_all_expiry_alerts(dry_run=dry_run)
                self.stdout.write(f"  expiry  -> {n} productos procesados")

            if "stock" in active_types:
                n = scan_all_stock_alerts(dry_run=dry_run)
                self.stdout.write(f"  stock   -> {n} productos procesados")

            if "location" in active_types:
                n = scan_all_location_alerts(dry_run=dry_run)
                self.stdout.write(f"  location-> {n} ubicaciones procesadas")

            self.stdout.write(self.style.SUCCESS(f"{mode}scan_alerts completado."))
        except Exception as exc:
            logger.exception("scan_alerts falló inesperadamente")
            self.stderr.write(self.style.ERROR(f"scan_alerts falló: {exc}"))
