"""
Management command para detectar (y opcionalmente reparar) divergencias entre
el caché StockByLocation y el ledger de movimientos.

Uso:
    python manage.py verify_stock_integrity          # solo reporta
    python manage.py verify_stock_integrity --fix    # reporta y repara
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from apps.inventory.models import StockByLocation
from apps.movements.services import _ledger_net_qty

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Verifica la integridad entre StockByLocation (caché) y el ledger de movimientos. "
        "Con --fix repara las divergencias encontradas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Corrige las divergencias actualizando el caché desde el ledger.",
        )

    def handle(self, *args, **options):
        rows = StockByLocation.objects.select_related("product", "location").all()
        divergences: list[tuple[StockByLocation, int]] = []

        for row in rows:
            expected = _ledger_net_qty(
                product_id=row.product_id, location_id=row.location_id
            )
            if expected != row.current_stock:
                divergences.append((row, expected))
                self.stderr.write(
                    self.style.WARNING(
                        f"DIVERGENCIA  {row.product.sku:20s}  "
                        f"@{row.location.code:15s}  "
                        f"caché={row.current_stock:6d}  ledger={expected:6d}"
                    )
                )

        if not divergences:
            self.stdout.write(
                self.style.SUCCESS("OK: todos los stocks coinciden con el ledger.")
            )
            return

        self.stderr.write(
            self.style.WARNING(f"\nTotal divergencias: {len(divergences)}")
        )

        try:
            from apps.webhooks.services import queue_webhook_event
            queue_webhook_event(
                "STOCK_INTEGRITY_DIVERGENCE",
                {"divergences": len(divergences)},
            )
        except Exception:
            pass

        if options["fix"]:
            for row, expected in divergences:
                row.current_stock = expected
                row.save(update_fields=["current_stock"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"REPARADO: {len(divergences)} divergencias corregidas desde el ledger."
                )
            )
        else:
            self.stdout.write(
                "Ejecuta con --fix para reparar automáticamente las divergencias."
            )
