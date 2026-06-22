"""
Configuración de pruebas.

Por defecto usa SQLite :memory: para velocidad.
Cuando DATABASE_URL está en el entorno (CI con Postgres o scripts/ci_local/ci_local.py),
usa esa base de datos en su lugar, lo que permite ejecutar pruebas
transaccionales reales (SELECT FOR UPDATE, constraints, etc.).
"""

import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = True
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    DATABASES = {"default": dj_database_url.config(default=_db_url, conn_max_age=0)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = []

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": (),
}
