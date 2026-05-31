"""Management command para archivar AuditLogs antiguos (M-02)."""

from __future__ import annotations

import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog, AuditLogArchive


class Command(BaseCommand):
    help = (
        "Mueve AuditLogs más antiguos que --older-than-days días a la tabla de archivo. "
        "Ejecutar con --dry-run antes de producción."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-days",
            type=int,
            default=365,
            help="Archivar logs más antiguos que N días (default: 365).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula sin modificar la base de datos.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Registros por batch atómico (default: 1000).",
        )

    def handle(self, *args, **options):
        older_than = timezone.now() - timedelta(days=options["older_than_days"])
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        total_qs = AuditLog.objects.filter(created_at__lt=older_than)
        total_count = total_qs.count()

        if total_count == 0:
            self.stdout.write("No hay logs para archivar.")
            return

        self.stdout.write(
            f"{'[DRY-RUN] ' if dry_run else ''}"
            f"Logs candidatos para archivar: {total_count} "
            f"(anteriores a {older_than.date()})"
        )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("--dry-run: ningún cambio realizado."))
            return

        start_time = time.monotonic()
        archived_total = 0

        while True:
            batch = list(
                AuditLog.objects.filter(created_at__lt=older_than)
                .order_by("created_at")[:batch_size]
            )
            if not batch:
                break

            with transaction.atomic():
                archive_records = [
                    AuditLogArchive(
                        id=log.id,
                        event_type=log.event_type,
                        user_id=log.user_id,
                        movement_id=log.movement_id,
                        description=log.description,
                        metadata=log.metadata,
                        ip_address=log.ip_address,
                        created_at=log.created_at,
                    )
                    for log in batch
                ]
                AuditLogArchive.objects.bulk_create(archive_records, ignore_conflicts=True)
                batch_ids = [log.id for log in batch]
                AuditLog.objects.filter(id__in=batch_ids).delete()

            archived_total += len(batch)
            self.stdout.write(f"  Archivados: {archived_total}/{total_count}...")

        elapsed = time.monotonic() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Archivado completo: {archived_total} registros en {elapsed:.1f}s."
            )
        )
