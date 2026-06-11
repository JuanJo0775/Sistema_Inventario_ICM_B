"""Servicio de email desacoplado — porta-adaptador sobre el backend Django configurado.

Permite sustituir el proveedor (Mailtrap → Mailgun → SES) cambiando únicamente
la configuración de settings; los servicios de dominio no dependen del proveedor concreto.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Envía un email de texto plano usando el backend configurado en Django."""
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to],
        fail_silently=False,
    )


def send_password_reset_email(to_email: str, username: str, reset_url: str) -> None:
    """Envía el correo de recuperación de contraseña al usuario (RF-001)."""
    subject = "Recuperación de contraseña — ICM"
    from django.conf import settings as _s

    expiry = getattr(_s, "PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 10)
    body = (
        f"Hola {username},\n\n"
        "Has solicitado recuperar tu contraseña en el sistema ICM.\n\n"
        f"Usa el siguiente enlace para restablecer tu contraseña (válido por {expiry} minutos):\n"
        f"{reset_url}\n\n"
        "Si no realizaste esta solicitud, ignora este mensaje. "
        "Tu contraseña no será modificada.\n\n"
        "Equipo ICM"
    )
    send_email(to_email, subject, body)
