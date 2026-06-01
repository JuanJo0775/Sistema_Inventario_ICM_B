"""Configuración centralizada del proceso de importación."""

from __future__ import annotations

from pathlib import Path

from decouple import config

# Raíz del repositorio (3 niveles arriba de este archivo)
_BASE_DIR = Path(__file__).resolve().parent.parent.parent

EXCEL_PATH: str = config(
    "IMPORT_EXCEL_PATH",
    default=str(_BASE_DIR / "docs" / "guias" / "Clasificacion_Productos.xlsx"),
)

DRY_RUN: bool = config("IMPORT_DRY_RUN", default=False, cast=bool)

ALMACENISTA_USERNAME: str = config("ALMACENISTA_USERNAME", default="almacenista")
ALMACENISTA_EMAIL: str = config("ALMACENISTA_EMAIL", default="almacenista@icm.local")
ALMACENISTA_PASSWORD: str = config("ALMACENISTA_PASSWORD", default="")
