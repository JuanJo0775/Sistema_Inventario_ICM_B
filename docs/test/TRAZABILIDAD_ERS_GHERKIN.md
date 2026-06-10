# Trazabilidad tests ↔ ERS (Gherkin) e informe de elicitación

Este documento enlaza pruebas automatizadas con **requisitos** y **criterios de aceptación en estilo Gherkin** del `docs/requisitos/ERS_ICM_Requisitos.md`, complementados con el contexto de negocio del `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (BR, roles, ubicaciones).

**Cobertura 1:1 ERS:** la suite `tests/ers/test_gherkin_dynamic.py` genera 1 función de test por escenario; la implementación vive en `tests/ers/impl/<dominio>.py`; cada escenario tiene su ficha en `docs/test/scenarios/<ID>.md`.

**Fuentes de verdad (orden):** ERS + informe de elicitación → código → tests.

---

## Workflow para añadir un nuevo escenario

> Ver guía completa en `docs/test/README_TEST.md`. Resumen ejecutivo:

1. **ERS primero** — escribir el escenario en `docs/requisitos/ERS_ICM_Requisitos.md` bajo la sección *Criterios de Aceptación (Formato Gherkin)* del RF correspondiente. El identificador sigue el patrón `RFxxx-SNN`.

2. **Regenerar metadatos** — `python -m scripts.generate_docs` actualiza `gherkin_scenarios.json` y crea `docs/test/scenarios/RFxxx-SNN.md`.

3. **Decidir tipo:**
   - Backend automatable → implementar en `tests/ers/impl/<dominio>.py` y registrar en `IMPLEMENTATIONS` del mismo archivo.
   - Backend aplazado → añadir entrada en `docs/test/gherkin_pending.json`.
   - Solo E2E/UI → añadir entrada en `docs/test/gherkin_out_of_scope.json`.

4. **Verificar** — `pytest tests/ers --collect-only -q` no debe mostrar errores; `pytest tests/ers -q` no debe mostrar `[MISSING]`.

5. **Actualizar esta matriz** — añadir fila en la sección del RF correspondiente con el escenario y su cobertura.

### Archivos de implementación por dominio

| Módulo | Archivo de implementación |
|--------|--------------------------|
| RF001–RF002 (Autenticación) | `tests/ers/impl/auth.py` |
| RF003 (Catálogo) | `tests/ers/impl/catalog.py` |
| RF004 (Inventario / Storage) | `tests/ers/impl/inventory.py` |
| RF005–RF009 (Movimientos) | `tests/ers/impl/movements.py` |
| RF010 (Reportes) | `tests/ers/impl/reports.py` |
| RF011 (Alertas) | `tests/ers/impl/alerts.py` |
| RF012 (Auditoría) | `tests/ers/impl/audit.py` |
| RF013 (Precios / Facturación) | `tests/ers/impl/pricing.py` |
| RF019–RF025 (Compras) | `tests/ers/impl/purchasing.py` |
| RNF003–RNF006 (No funcionales) | `tests/ers/impl/nonfunctional.py` |

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

## RF-004 / BR-14 — Estado operativo de ubicación restringe movimientos

| Criterio ERS (Scenarios 11–14) | Cobertura |
|--------------------------------|-----------|
| S11 — Mantenimiento bloquea despacho | `apps/movements/tests/test_services.py::test_dispatch_fails_when_origin_location_is_in_maintenance` + `tests/ers/test_gherkin_dynamic.py::test_RF004_S11` |
| S12 — Archivar fuerza is_active=False | `tests/ers/test_gherkin_dynamic.py::test_RF004_S12` |
| S13 — Archived rechaza entrada | `apps/movements/tests/test_services.py::test_entry_fails_when_destination_is_archived` + `tests/ers/test_gherkin_dynamic.py::test_RF004_S13` |
| S14 — Restricted bloquea despacho, permite entrada | `apps/movements/tests/test_services.py::test_dispatch_fails_when_origin_is_restricted` + `test_entry_allows_destination_in_restricted` + `tests/ers/test_gherkin_dynamic.py::test_RF004_S14` |
| Blocked bloquea traslado destino | `apps/movements/tests/test_services.py::test_internal_transfer_fails_when_destination_is_blocked` |
| Return a blocked/archived rechazado (BR-14) | `apps/movements/tests/test_services.py::test_return_fails_when_destination_is_blocked` + `test_return_fails_when_destination_is_archived` |
| Archived bloquea despacho origen | `apps/movements/tests/test_services.py::test_dispatch_fails_when_origin_is_archived` |

---

## RF-004 / BR-15 — StorageType activo requerido para asignación

| Criterio ERS (Scenarios 8–9) | Cobertura |
|------------------------------|-----------|
| S08 — Crear tipo y asignar a ubicación | `apps/inventory/tests/test_storage_types.py::test_storage_type_crud_and_location_binding` + `tests/ers/test_gherkin_dynamic.py::test_RF004_S08` |
| S09 — Tipo inactivo rechazado en create | `apps/inventory/tests/test_storage_types.py::test_inactive_storage_type_rejected_on_create_location` + `tests/ers/test_gherkin_dynamic.py::test_RF004_S09` |
| Tipo inactivo rechazado en PATCH | `apps/inventory/tests/test_storage_types.py::test_inactive_storage_type_rejected_on_patch_location` |

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

## RF-010 — Dashboard operacional

| Criterio | Cobertura |
|----------|-----------|
| Dashboard agregado (`overview`) con métricas, alertas, KPIs y movimientos recientes | `apps/dashboard/tests/test_views.py::test_dashboard_overview_returns_composable_payload` |
| KPIs con metadatos de precisión y clasificación explícita | `apps/dashboard/tests/test_views.py::test_dashboard_kpis_expose_precision_metadata` |
| Ownership centralizado de KPIs sin drift entre reports y dashboard | `apps/reports/tests/test_services.py::test_generate_kpis_returns_dashboard_keys` y la delegación desde `apps/reports/selectors.py::get_kpi_dashboard` |

---

## RF-NEW-05 / BR-16 — Precio congelado en despacho

| Criterio ERS (Escenarios RFNEW05-S01, S02, S04) | Cobertura |
|--------------------------------------------------|-----------|
| S01 — Despacho captura unit_price, subtotal, tax_amount, total_amount | `apps/movements/tests/test_dispatch_pricing.py::test_dispatch_retail_captures_sale_price_retail_as_unit_price` + `test_dispatch_calculates_subtotal_tax_total_correctly` |
| S01 — Despacho mayorista captura sale_price_wholesale | `apps/movements/tests/test_dispatch_pricing.py::test_dispatch_wholesale_captures_sale_price_wholesale` |
| S01 — Despacho con descuento calcula discount_amount correctamente | `apps/movements/tests/test_dispatch_pricing.py::test_dispatch_with_discount_calculates_correctly` |
| S01 — Producto sin precio almacena null sin bloquear el flujo | `apps/movements/tests/test_dispatch_pricing.py::test_dispatch_without_product_price_stores_null_gracefully` |
| S02 — Precio en Movement no cambia tras actualizar precio del producto | `apps/movements/tests/test_dispatch_pricing.py::test_price_snapshot_immutable_after_product_price_change` |
| S04 — customer_snapshot persiste datos del cliente en el Movement | `apps/movements/tests/test_dispatch_pricing.py::test_customer_snapshot_persisted_on_wholesale_dispatch` |
| S04 — Factura contiene totales consolidados correctos | `apps/movements/tests/test_invoice.py::test_invoice_totals_match_sum_of_movements` |
| S04 — Factura de venta mayor contiene datos del cliente | `apps/movements/tests/test_invoice.py::test_invoice_has_customer_data_on_wholesale` |

---

## RF-NEW-05 / BR-17 — Historial auditado de cambios de precio

| Criterio ERS (Escenario RFNEW05-S03) | Cobertura |
|--------------------------------------|-----------|
| S03 — Actualizar precio crea fila en ProductPriceHistory con old/new value y usuario | `apps/catalog/tests/test_product_pricing.py::test_update_price_creates_history_record` + `test_price_history_tracks_old_and_new_value` |
| S03 — Valor idéntico al actual no genera registro de historial | `apps/catalog/tests/test_product_pricing.py::test_update_with_same_value_does_not_create_history` |
| S03 — Actualizar múltiples campos crea una fila por cada campo | `apps/catalog/tests/test_product_pricing.py::test_update_multiple_price_fields_creates_multiple_history_records` |
| S03 — GET /prices/ retorna historial completo del producto | `apps/catalog/tests/test_product_pricing.py::test_api_get_price_history_returns_list` |
| S03 — Solo almacenista puede actualizar precios | `apps/catalog/tests/test_product_pricing.py::test_update_prices_requires_almacenista_role` + `test_api_patch_prices_rejects_auxiliar` |

---

## RF-021 / BR-022 — Creación de recepciones con distribución avanzada

| Criterio ERS | Cobertura |
|--------------|-----------|
| S01 — Recepción parcial simple de una OC | `apps/purchasing/tests/test_services.py::test_create_reception_borrador` + `apps/purchasing/tests/test_views.py::test_create_reception` |
| S02 — Superar cantidad pendiente rechaza la creación | `apps/purchasing/tests/test_services.py::test_create_reception_exceeds_quantity_raises` |
| S03 — OC en BORRADOR rechazada | `apps/purchasing/tests/test_services.py::test_create_reception_po_not_receivable_raises` |
| S04 — Recepción avanzada por lote y ubicación | `apps/purchasing/tests/test_services.py::test_confirm_reception_advanced_distribution_by_lots_and_locations` + `apps/purchasing/tests/test_views.py::test_create_reception_with_allocations` |
| S05 — Distribución avanzada con suma inconsistente rechazada | `apps/purchasing/tests/test_services.py::test_create_reception_advanced_distribution_requires_matching_quantity` |

---

## RF-022 / BR-022 — Confirmación de recepción y movimientos por porción

| Criterio ERS | Cobertura |
|--------------|-----------|
| S01 — Confirmación simple crea Movement único y actualiza stock | `apps/purchasing/tests/test_services.py::test_confirm_reception_creates_movements_and_updates_stock` |
| S02 — Recepción completa marca la OC como COMPLETADA | `apps/purchasing/tests/test_services.py::test_confirm_reception_partial_marks_po_partial` + `test_confirm_reception_partial_second_delivery_matches_pending_without_note` |
| S03 — Recepción parcial marca la OC como PARCIALMENTE_RECIBIDA | `apps/purchasing/tests/test_services.py::test_confirm_reception_partial_marks_po_partial` |
| S04 — Error en generación de Movement revierte toda la recepción | `apps/purchasing/tests/test_services.py::test_confirm_reception_is_atomic_on_error` |
| S05 — Discrepancia sin nota es rechazada | `apps/purchasing/tests/test_services.py::test_confirm_reception_discrepancy_requires_note` |
| S06 — Confirmación avanzada genera un Movement por porción | `apps/purchasing/tests/test_services.py::test_confirm_reception_advanced_distribution_by_lots_and_locations` + `test_confirm_reception_advanced_distribution_by_locations_only` |
| S07 — Suma inconsistente en confirmación avanzada es rechazada | `apps/purchasing/tests/test_services.py::test_create_reception_advanced_distribution_requires_matching_quantity` |

---

## RF-024 / Trazabilidad ciclo de compras

| Criterio | Cobertura |
|----------|-----------|
| Movement ENTRADA navega a ReceptionItem y a la OC | `apps/purchasing/tests/test_views.py::test_confirm_reception_endpoint` |
| Distribuciones avanzadas navegan a su Location y Movement por porción | `apps/purchasing/tests/test_views.py::test_create_reception_with_allocations` |

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
