# Proyecto ICM — reglas Antigravity (GEMINI.md)

Este archivo tiene prioridad sobre `AGENTS.md` solo para **Antigravity**. No dupliques políticas: mantén una sola fuente de verdad.

## Debes seguir

1. Lee y respeta **`AGENTS.md`** en la raíz del repo (contexto ICM, capas, documentación).
2. Las reglas operativas están consolidadas en **`AGENTS.md`** y en **`.github/instructions/Agents.instructions.md`** (canonical). Las antiguas "cursor rules" ya no se usan.
3. Para detalle de negocio y arquitectura, usa **`docs/README_ARQUITECTURA.md`** y **`docs/requisitos/ERS_ICM_Requisitos.md`**.
4. Consulta también **`docs/api/README_API.md`**, **`docs/api/README_MATRIZ_PERMISOS.md`** y **`docs/api/REFERENCIA_ENDPOINTS.md`** para contratos de API.

## Convención

- Implementación Django: negocio en `services.py`, lecturas en `selectors.py`, API versionada `/api/v1/`, trazabilidad RF/BR cuando cambies dominio.
