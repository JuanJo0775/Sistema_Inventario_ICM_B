"""Management command: importa el catálogo inicial de productos desde Excel."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.authentication.models import User
from scripts.import_catalog import config as import_config
from scripts.import_catalog import reporter

# Directorio donde se guardan los reportes JSON (scripts/import_catalog/)
_REPORTS_DIR = Path(import_config.__file__).resolve().parent / "reports"
from scripts.import_catalog.importer import import_rows
from scripts.import_catalog.reader import read_excel
from scripts.import_catalog.transformer import transform
from scripts.import_catalog.validator import validate


class Command(BaseCommand):
    help = (
        "Importa el catálogo inicial de productos desde el Excel del cliente. "
        "Es idempotente: productos y categorías ya existentes se omiten."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--excel-path",
            type=str,
            default=None,
            help="Ruta al archivo Excel. Por defecto: variable IMPORT_EXCEL_PATH del .env.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Ejecuta validación y transformación sin escribir en la BD.",
        )
        parser.add_argument(
            "--actor-username",
            type=str,
            default=None,
            help=(
                "Username del usuario almacenista que actúa como autor de la importación. "
                "Por defecto: variable ALMACENISTA_USERNAME del .env."
            ),
        )

    def handle(self, *args, **options):
        excel_path = options["excel_path"] or import_config.EXCEL_PATH
        dry_run = options["dry_run"] or import_config.DRY_RUN
        actor_username = options["actor_username"] or import_config.ALMACENISTA_USERNAME

        # Validar usuario actor
        try:
            user = User.objects.get(username=actor_username)
        except User.DoesNotExist:
            raise CommandError(
                f"Usuario '{actor_username}' no encontrado. "
                "Ejecuta primero: python manage.py create_almacenista"
            )
        if user.role != "almacenista":
            raise CommandError(
                f"El usuario '{actor_username}' tiene rol '{user.role}', "
                "se requiere rol 'almacenista'."
            )

        self.stdout.write(f"Excel:  {excel_path}")
        self.stdout.write(f"Actor:  {user.username} (rol: {user.role})")
        if dry_run:
            self.stdout.write(
                self.style.WARNING("Modo DRY-RUN activo — no se escribirá en la BD.")
            )

        # 1. Leer Excel
        self.stdout.write("\nLeyendo Excel...")
        raw_rows = read_excel(excel_path)
        self.stdout.write(f"  Filas leídas: {len(raw_rows)}")

        # 2. Validar
        val_report = validate(raw_rows)
        reporter.print_validation_report(val_report)

        # 3. Transformar
        import_rows_list, transform_errors = transform(val_report)
        if transform_errors:
            self.stdout.write(
                self.style.ERROR(
                    f"\nErrores de transformación ({len(transform_errors)}):"
                )
            )
            for row, msg in transform_errors:
                self.stdout.write(f"  {row.codigo!r}: {msg}")

        self.stdout.write(f"\nFilas a importar: {len(import_rows_list)}")

        # 4. Importar
        self.stdout.write("Importando...")
        result = import_rows(user, import_rows_list, dry_run=dry_run)
        reporter.print_import_result(result, dry_run=dry_run)

        # 5. Guardar reporte JSON
        report_path = reporter.save_report(
            result, output_dir=_REPORTS_DIR, dry_run=dry_run
        )
        self.stdout.write(f"\nReporte guardado en: {report_path}")

        # 6. Resultado final
        if result.errors:
            self.stdout.write(
                self.style.ERROR(
                    f"\nImportación completada con {len(result.errors)} error(es)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\nImportación completada exitosamente.")
            )
