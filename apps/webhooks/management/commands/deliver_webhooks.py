"""Management command para entregar webhooks pendientes (NEW-03)."""

import time

from django.core.management.base import BaseCommand

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.webhooks.services import deliver_pending_webhooks


class Command(BaseCommand):
    help = "Entrega webhooks pendientes en la cola. Seguro para ejecutar en paralelo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Número máximo de webhooks a procesar por ejecución (default: 50).",
        )

    def handle(self, *args, **options):
        start_time = time.monotonic()
        batch_size = options["batch_size"]
        log_event(
            AuditEventType.BATCH_JOB_EXECUTED,
            detail={
                "job_name": "deliver_webhooks",
                "status": "STARTED",
                "batch_size": batch_size,
            },
        )
        try:
            delivered, failed = deliver_pending_webhooks(batch_size=batch_size)
            total = delivered + failed
            elapsed = time.monotonic() - start_time
            log_event(
                AuditEventType.BATCH_JOB_EXECUTED,
                detail={
                    "job_name": "deliver_webhooks",
                    "status": "COMPLETED",
                    "delivered": delivered,
                    "failed": failed,
                    "elapsed_seconds": round(elapsed, 2),
                },
            )
            if total == 0:
                self.stdout.write("No hay webhooks pendientes.")
                return
            self.stdout.write(
                self.style.SUCCESS(
                    f"Procesados: {total} | Entregados: {delivered} | Fallidos: {failed}"
                )
            )
        except Exception:
            elapsed = time.monotonic() - start_time
            log_event(
                AuditEventType.BATCH_JOB_EXECUTED,
                detail={
                    "job_name": "deliver_webhooks",
                    "status": "FAILED",
                    "elapsed_seconds": round(elapsed, 2),
                },
            )
            raise
