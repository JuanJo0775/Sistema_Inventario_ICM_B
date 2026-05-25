# Proyecto ICM — reglas Antigravity (GEMINI.md)

Este archivo tiene prioridad sobre `AGENTS.md` solo para **Antigravity**. No dupliques políticas: mantén una sola fuente de verdad.

## Debes seguir

1. Lee y respeta **`AGENTS.md`** en la raíz del repo (contexto ICM, capas, documentación).
2. Respeta las reglas de Cursor en **`.cursor/rules/`** (`icm-contexto-requisitos.mdc`, `icm-capas-django.mdc`, `icm-api-openapi.mdc`).
3. Para detalle de negocio y arquitectura, usa **`docs/README_ARQUITECTURA.md`** y **`docs/requisitos/ERS_ICM_Requisitos.md`**.

## Convención

- Implementación Django: negocio en `services.py`, lecturas en `selectors.py`, API versionada `/api/v1/`, trazabilidad RF/BR cuando cambies dominio.
