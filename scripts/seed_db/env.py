"""Variables de entorno usadas por el seed y el usuario inicial."""

from __future__ import annotations

from decouple import config

ALMACENISTA_USERNAME = config("ALMACENISTA_USERNAME", default="almacenista")
ALMACENISTA_EMAIL = config("ALMACENISTA_EMAIL", default="almacenista@icm.local")
ALMACENISTA_PASSWORD = config("ALMACENISTA_PASSWORD", default="")
