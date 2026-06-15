"""Configuración de producción (RNF-002, RNF-003)."""

from datetime import timedelta

from decouple import config

from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = [
    h.strip()
    for h in config("DJANGO_ALLOWED_HOSTS", default="").split(",")
    if h.strip()
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True

# DATABASES viene de base.py con el switch DB_PROVIDER (local/neon)
# Solo se fuerza connect_timeout para producción:
if config("DB_PROVIDER", default="local") == "local":
    DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 10

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [config("FRONTEND_URL", default="https://example.com").strip()]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

SIMPLE_JWT.update(  # noqa: F405
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    }
)

LOGGING["root"]["level"] = "INFO"  # noqa: F405

# M-06: Restringir acceso a documentación OpenAPI solo a staff en producción.
RESTRICT_API_SCHEMA = True
