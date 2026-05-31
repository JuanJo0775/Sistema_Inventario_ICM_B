"""Management command para entregar webhooks pendientes (NEW-03)."""

from django.core.management.base import BaseCommand

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
        batch_size = options["batch_size"]
        delivered, failed = deliver_pending_webhooks(batch_size=batch_size)
        total = delivered + failed
        if total == 0:
            self.stdout.write("No hay webhooks pendientes.")
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"Procesados: {total} | Entregados: {delivered} | Fallidos: {failed}"
            )
        )
