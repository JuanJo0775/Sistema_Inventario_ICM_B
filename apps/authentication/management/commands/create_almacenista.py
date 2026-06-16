"""Management command: crea el usuario almacenista inicial del sistema."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from apps.authentication.models import RoleChoices, User
from scripts.seed_db.env import (
    ALMACENISTA_EMAIL,
    ALMACENISTA_PASSWORD,
    ALMACENISTA_USERNAME,
)


class Command(BaseCommand):
    help = (
        "Crea el usuario almacenista inicial para operación del sistema. "
        "Idempotente: si el usuario ya existe, no hace nada."
    )

    def handle(self, *args, **options):
        username = ALMACENISTA_USERNAME
        email = ALMACENISTA_EMAIL
        password = ALMACENISTA_PASSWORD

        if not password:
            raise CommandError(
                "La variable ALMACENISTA_PASSWORD está vacía. "
                "Configúrala en el archivo .env antes de ejecutar este comando."
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"El usuario '{username}' ya existe. No se realizaron cambios."
                )
            )
            return

        if User.objects.filter(email__iexact=email).exists():
            raise CommandError(
                f"El email '{email}' ya está registrado para otro usuario. "
                "Cambia ALMACENISTA_EMAIL en el .env."
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=RoleChoices.ALMACENISTA,
        )
        log_event(
            AuditEventType.USER_CREATED,
            description=f"Usuario almacenista inicial creado via comando: {username}",
            user=user,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario almacenista '{username}' ({email}) creado exitosamente."
            )
        )
