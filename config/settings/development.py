"""Ajustes para desarrollo local y contenedor Docker."""

from datetime import timedelta

from decouple import config

from .base import *  # noqa: F401,F403

DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = [h.strip() for h in config("DJANGO_ALLOWED_HOSTS", default="*").split(",") if h.strip()]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="icm_db"),
        "USER": config("DB_USER", default="icm_user"),
        "PASSWORD": config("DB_PASSWORD", default="icm_password"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,
    }
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = []

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    }
)

LOGGING["root"]["level"] = "DEBUG"
