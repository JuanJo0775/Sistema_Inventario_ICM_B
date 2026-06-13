"""SQLite para pruebas automatizadas sin PostgreSQL."""

from .base import *  # noqa: F401,F403

DEBUG = True
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

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
