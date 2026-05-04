# AGENTS.md — Sistema Inventario ICM (backend Django)

Instrucciones para asistentes de código (Antigravity, Cursor u otras herramientas que lean este archivo). Complementa las reglas en `.cursor/rules/*.mdc`.

## Documentación fuente (obligatoria como referencia)

| Documento | Uso |
|-----------|-----|
| `docs/README_ARQUITECTURA.md` | Arquitectura modular, ledger + stock derivado, BR-01…BR-13, SOLID, testing, Docker |
| `docs/ERS_ICM_Requisitos.md` | RF-001…RF-012, RNF-001…RNF-006, Gherkin, tabla de trazabilidad |
| `docs/README_API.md` | `/api/v1/`, JWT, tags OpenAPI, checklist de publicación de API |
| `docs/ICM_Informe_Elicitacion_v2_plus.docx.md` | Contexto de negocio ICM, entidades, reglas consolidadas |

## Dominio breve

- **ICM**: inventario insumos médicos; marca propia **Can** → SKU con prefijo **CAN-** (BR-12).
- **Ubicaciones**: Vitrina, Bodega 1, Bodega 2; stock total = suma por ubicación; traslados no cambian total global (BR-11).
- **Roles**: `almacenista` (24/7, credenciales, ajustes), `auxiliar_despacho` (movimientos; solo **07:00–12:00** y **14:00–17:00** en **America/Bogota**), `administrador` (reportes/KPI, sin escritura).
- **Crítico**: validación cruzada escaneado vs SKU de orden en despacho (BR-08); movimientos/auditoría **inmutables** (BR-10); serial obligatorio Electroterapia en entradas/salidas según catálogo (BR-04); datos personales cliente mayorista y Ley 1581 (RNF-006).

## Reglas de implementación backend

1. **Negocio solo en `services.py`**. `models.py` / `serializers.py` / `views.py` sin reglas de dominio.
2. **Consultas** complejas en `selectors.py` sin efectos secundarios.
3. **Stock**: ledger (`Movement`) como fuente de verdad; actualizar `StockByLocation` solo en la misma transacción que el movimiento; no stock negativo.
4. **API**: REST JSON bajo `/api/v1/`; errores `{ error, message, detail }`; permisos alineados al ERS; OpenAPI con tags oficiales.
5. **Tests**: casos críticos del README de arquitectura (horario auxiliar, inmutabilidad, validación cruzada, serial, devoluciones, ajustes, consistencia ledger).


### API / OpenAPI (icm-api-openapi.mdc)

- Prefijo API: `/api/v1/`. Cambios incompatibles -> nueva versión `/api/v2/`.
- Documentar endpoints con `@extend_schema`: `summary`, `description`, `tags`, `request`, `responses`, `parameters`.
- Usar únicamente los tags en `shared/openapi.py` para consistencia en Swagger.
- Rutas públicas deben declarar `auth=[]` cuando corresponda.
- Forma uniforme de errores:

```
{
	"error": "codigo_maquina",
	"message": "Mensaje legible",
	"detail": {}
}
```

### Capas Django (icm-capas-django.mdc)

- `models.py`: entidades y restricciones (sin lógica de negocio).
- `serializers.py`: validación/transformación I/O (sin reglas de dominio).
- `views.py`: validar entrada y delegar (sin lógica de negocio).
- `services.py`: toda la lógica de negocio y transacciones.
- `selectors.py`: lecturas complejas, sin efectos secundarios.
- `permissions.py`: RBAC y restricciones (p. ej. horario auxiliar).

Principios clave: operaciones que alteren stock deben usar `@transaction.atomic` y `select_for_update()` donde aplique; movimientos/auditoría inmutables.

### Contexto y trazabilidad (icm-contexto-requisitos.mdc)

- Antes de cambiar comportamiento o contratos, alinear con `docs/README_ARQUITECTURA.md`, `docs/ERS_ICM_Requisitos.md` y `docs/README_API.md`.
- En cambios de lógica de dominio, referenciar RF/BR/RNF impactados en docstrings/PRs.
- Recordar horario y roles del negocio (`auxiliar_despacho` en America/Bogota: 07:00–12:00 y 14:00–17:00).

## Propuesta: reglas mejoradas para `AGENTS` / `.cursor` (plantilla)

Para facilitar reglas más robustas y consistentes, propongo una plantilla y una serie de reglas mejoradas que pueden añadirse a `.cursor/rules/`:

- Plantilla mínima (`.mdc`):

```
---
description: Short description
globs:
	- "**/views.py"
	- "**/serializers.py"
alwaysApply: false
---

# Title

- Key points...
```

- Reglas sugeridas:
	- `icm-openapi-checks.mdc`: validar que nuevos endpoints tengan `@extend_schema` con `request` y `responses`.
	- `icm-service-logic.mdc`: advertir si hay lógica de dominio en `views.py` o `serializers.py` (sugerir mover a `services.py`).
	- `icm-stock-transactions.mdc`: detectar operaciones que escriben stock y asegurar `@transaction.atomic` y `select_for_update()` en `services.py`.
	- `icm-trazabilidad.mdc`: forzar mención de RF/BR/RNF en docstrings de funciones que alteran invariantes del dominio.

Estas reglas pueden implementarse como heurísticas sencillas en `.cursor` y luego pulirse con reglas más avanzadas (regex, AST checks) si el tooling lo permite.

---

Si quieres, aplico estas reglas como archivos `.cursor/rules/*.mdc` nuevos y los commiteo; también puedo crear PRs separados por regla para revisión.
