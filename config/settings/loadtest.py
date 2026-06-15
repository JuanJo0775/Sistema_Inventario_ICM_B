"""Settings para load testing (Locust) — hereda de test pero usa Postgres.

El settings de test usa SQLite :memory:, que no persiste entre procesos.
Para el load test se necesita que migrate, manage.py shell y runserver
compartan la misma base de datos, lo que requiere un motor persistente.
"""

import os

import dj_database_url

from .test import *  # noqa: F401,F403

_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    DATABASES = {"default": dj_database_url.config(default=_db_url)}
else:
    # Fallback local para desarrollo
    from .base import DATABASES as _base_db  # noqa: F401

    DATABASES = _base_db
