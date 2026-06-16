"""Ajustes para desarrollo local y contenedor Docker."""

from datetime import timedelta

from .base import *  # noqa: F401,F403

DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)  # noqa: F405
ALLOWED_HOSTS = [
    h.strip()
    for h in config("DJANGO_ALLOWED_HOSTS", default="*").split(",")  # noqa: F405
    if h.strip()
]

# DATABASES viene de base.py con el switch DB_PROVIDER (local/neon)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = []

SIMPLE_JWT.update(  # noqa: F405
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    }
)

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
