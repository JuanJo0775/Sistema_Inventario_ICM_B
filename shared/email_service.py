"""Servicio de email desacoplado — porta-adaptador sobre el backend Django configurado.

Permite sustituir el proveedor (Mailtrap → Mailgun → SES) cambiando únicamente
la configuración de settings; los servicios de dominio no dependen del proveedor concreto.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str, html_body: str | None = None) -> None:
    """Envía un email con contenido texto plano y opcionalmente HTML."""
    send_mail(
        subject=subject,
        message=body,
        html_message=html_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to],
        fail_silently=False,
    )


def send_password_reset_email(to_email: str, username: str, reset_url: str) -> None:
    """Envía el correo de recuperación de contraseña al usuario (RF-001)."""
    subject = "Recuperación de contraseña — ICM LogiStock"
    expiry = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 10)

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f7f8;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;">
          <tr>
            <td style="padding:32px 32px 8px;text-align:center;">
              <span style="font-size:24px;font-weight:700;color:#1a6b72;">ICM LogiStock</span>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;text-align:center;font-size:14px;color:#8a9ea2;">
              Recuperaci&oacute;n de contrase&ntilde;a
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;font-size:14px;color:#2d3e41;line-height:1.6;">
              Hola {username},<br><br>
              Has solicitado recuperar tu contrase&ntilde;a en el sistema ICM.
              Haz clic en el bot&oacute;n para restablecerla
              (v&aacute;lido por {expiry} minutos).
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 32px 24px;">
              <a href="{reset_url}"
                 style="display:inline-block;padding:14px 32px;background:#1a6b72;color:#ffffff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;">
                Restablecer contrase&ntilde;a
              </a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 32px 24px;font-size:13px;color:#8a9ea2;">
              Si el bot&oacute;n no funciona,
              <a href="{reset_url}" style="color:#e07b39;text-decoration:underline;">
                haz clic aqu&iacute;
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px;background:#f4f7f8;font-size:12px;color:#8a9ea2;text-align:center;">
              Si no realizaste esta solicitud, ignora este mensaje. Tu contrase&ntilde;a no ser&aacute; modificada.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_body = (
        f"Hola {username},\n\n"
        "Has solicitado recuperar tu contraseña en el sistema ICM.\n\n"
        f"Usa el siguiente enlace para restablecer tu contraseña (válido por {expiry} minutos):\n"
        f"{reset_url}\n\n"
        "Si no realizaste esta solicitud, ignora este mensaje. "
        "Tu contraseña no será modificada.\n\n"
        "Equipo ICM LogiStock"
    )
    send_email(to_email, subject, text_body, html_body=html_body)
