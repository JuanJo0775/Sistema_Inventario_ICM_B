"""Variables de entorno usadas por el seed y el usuario inicial."""

from __future__ import annotations

import os
from pathlib import Path

from decouple import Config, RepositoryEnv

# Detectar qué .env cargar según DJANGO_SETTINGS_MODULE
_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
_base_dir = Path(__file__).resolve().parent.parent.parent
if "production" in _settings_module:
    _env_file = _base_dir / ".env.production"
elif "development" in _settings_module:
    _env_file = _base_dir / ".env.development"
else:
    _env_file = _base_dir / ".env"
if not _env_file.exists():
    _env_file = _base_dir / ".env"

config = Config(RepositoryEnv(str(_env_file)))

ALMACENISTA_USERNAME = config("ALMACENISTA_USERNAME", default="almacenista")
ALMACENISTA_EMAIL = config("ALMACENISTA_EMAIL", default="almacenista@icm.local")
ALMACENISTA_PASSWORD = config("ALMACENISTA_PASSWORD", default="")
