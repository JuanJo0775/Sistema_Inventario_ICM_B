# Trazabilidad tests ↔ ERS (Gherkin) e informe de elicitación

Este documento enlaza pruebas automatizadas con **requisitos** y **criterios de aceptación en estilo Gherkin** del `docs/requisitos/ERS_ICM_Requisitos.md`, complementados con el contexto de negocio del `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (BR, roles, ubicaciones).

**Cobertura 1:1 ERS:** la suite `tests/ers/test_gherkin_dynamic.py` (95 nodos) y `tests/ers/gherkin_impl.py` son la fuente principal; cada escenario tiene su ficha en `docs/test/scenarios/<ID>.md`.

**Fuentes de verdad (orden):** ERS + informe de elicitación → código → tests.

---

## RF-001 — Inicio de sesión (Feature Gherkin en ERS)

| Escenario ERS (resumen) | Comportamiento esperado (Then) | Cobertura en tests |
|-------------------------|--------------------------------|--------------------|
| Scenario 1 — Almacenista | Autenticación exitosa, evento auditable | `tests/test_api_integration.py::test_auth_login_with_username_returns_jwt_and_profile` |
| Scenario 1 / login por email | JWT + perfil | `tests/test_api_integration.py::test_auth_login_with_email_returns_jwt` |
| Scenario 3 — Auxiliar **fuera** de horario | Bloqueo, sin sesión | `apps/authentication/tests/test_services.py::test_auxiliar_blocked_outside_hours` (servicio); API login sigue patrón ValidationError en serializer |
| Scenario 5 — Administrador fuera horario «laboral» | Sin restricción BR-03 | Cubierto por rol `administrador` en permisos; login sin patch horario en integración |
| **Extensión BR-03 (sesión)** | Renovar `access` no debe eludir franja auxiliar | `tests/test_api_integration.py::test_auth_token_refresh_auxiliar_outside_hours_forbidden` |
| Contraste roles | Almacenista renueva fuera de ventana auxiliar | `tests/test_api_integration.py::test_auth_token_refresh_almacenista_allowed_outside_auxiliar_window` |
| BR-03 por request | Permiso horario en API | `apps/authentication/tests/test_services.py::test_operating_hours_enforced_per_request` |

**Nota de consistencia:** El ERS describe la UX web («redirige al dashboard»); los tests API validan **contrato HTTP** equivalente (códigos, cuerpo JSON, tokens), que es lo verificable en backend sin UI.

---

## RF-003 — Catálogo / BR-12

| Criterio | Cobertura |
|----------|-----------|
| SKU con patrón 1–4 letras + guion + 1–4 dígitos (BR-12) | `apps/catalog/tests/test_models.py::test_product_full_clean_rejects_invalid_sku_format` (`Product.clean()` / Admin) |
| Barcode estable, write-once y consumible por frontend como payload listo | `apps/catalog/tests/test_services.py::test_create_product_auto_generates_stable_barcode`, `apps/catalog/tests/test_services.py::test_update_product_keeps_existing_barcode`, `apps/catalog/tests/test_services.py::test_update_product_backfills_missing_barcode`, `apps/catalog/tests/test_views.py::test_product_barcode_endpoint_returns_ready_to_consume_payload` |

**Nota de alcance:** el barcode deja de depender de `sku` o `name`; se genera una sola vez desde la identidad técnica del producto y el frontend consume el payload ya renderizado en `GET /api/v1/catalog/products/<id>/barcode/`.

---

## RF-004 / BR-11 — Stock por ubicación (derivado)

| Criterio | Cobertura |
|----------|-----------|
| Stock derivado del ledger; no edición arbitraria en Admin (coherente con ERS BR-11 e informe: ledger fuente de verdad) | `apps/inventory/tests/test_admin.py::test_stock_by_location_admin_is_least_privilege_derived_stock` |
| Consultas de stock / totales | `apps/inventory/tests/test_selectors.py`, `apps/inventory/tests/test_services.py`, `apps/inventory/tests/test_views.py` |

---

## RF-006 — Despacho (Gherkin Scenarios 1–2 en ERS)

| Escenario ERS | Cobertura principal |
|-----------------|---------------------|
| Scenario 2 — Validación cruzada falla | `apps/movements/tests/test_services.py::test_dispatch_cross_validation_fails_wrong_sku` |
| Scenario 1 / flujo mayor (datos cliente, BR-08, BR-13) | Parcialmente en servicios e integración; ampliar con tests dedicados si el contrato API de venta mayor se estabiliza |

---

## RF-007 — Traslados / BR-06 / BR-11

| Criterio | Cobertura |
|----------|-----------|
| Traslado no altera stock global | `apps/movements/tests/test_services.py::test_internal_transfer_does_not_change_global_stock` |
| Corrección en ventana (implementación README 5 min + compensación ledger) | `apps/movements/tests/test_services.py::test_correction_within_window_creates_reversal_and_fixed` |

**Ambigüedad documentada:** El ERS (RF-007, BR-06) habla de **misma franja horaria** para el auxiliar; `docs/README_ARQUITECTURA.md` detalla **ventana de 5 minutos** y compensación por nuevos movimientos. El código sigue hoy la arquitectura README; los tests de servicio reflejan ese contrato. Unificar ERS vs README es decisión de producto/documentación.

---

## RF-008 — Devoluciones / BR-05

| Escenario ERS (bloqueo no retornable) | `apps/movements/tests/test_services.py::test_return_blocked_for_non_returnable_category` |

---

## RF-009 — Ajustes / BR-07

| Criterio | `apps/movements/tests/test_services.py::test_adjustment_requires_justification` |

---

## Cómo ejecutar (por módulo / test)

```bash
# Toda la suite
pytest -q

# Solo trazabilidad RF-001 / refresh
pytest tests/test_api_integration.py -k "token_refresh" -v

# RF-003 BR-12
pytest apps/catalog/tests/test_models.py::test_product_full_clean_rejects_invalid_sku_format -v

# RF-004 Admin stock
pytest apps/inventory/tests/test_admin.py -v
```

---

## Próximos refuerzos sugeridos por Gherkin (sin implementarlos aquí)

- **RF-006 Scenario 1** end-to-end API: venta mayor con datos cliente + validación cruzada + factura BR-13.
- **RF-008** flujo en dos etapas (pendiente / aprobación almacenista) según escenarios 3–4 del ERS.
- **RF-007** escenarios Gherkin 2–3 (stock insuficiente, mismo origen/destino) como tests de servicio explícitos.
