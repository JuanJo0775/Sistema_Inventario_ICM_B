"""Settings para load testing (Locust) — hereda de test pero usa Postgres.

El settings de test usa SQLite :memory:, que no persiste entre procesos.
Para el load test se necesita que migrate, manage.py shell y runserver
compartan la misma base de datos, lo que requiere un motor persistente.
"""

import urllib.parse
import os

from .test import *  # noqa: F401,F403

_db = urllib.parse.urlparse(os.environ.get("DATABASE_URL", ""))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db.path.lstrip("/") or "icm_test",
        "USER": _db.username or "icm",
        "PASSWORD": _db.password or "icm_pass",
        "HOST": _db.hostname or "localhost",
        "PORT": str(_db.port or 5432),
    }
}
