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

## Idioma

- Respuestas al equipo en **español** salvo que pidan otro idioma.
