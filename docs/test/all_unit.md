<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\index.md -->

# Ãndice de tests (unitarios)
| CÃ³digo | Test | Archivo |
|---|---|---|
| UNIT-0001 | test_alert_type_low_stock | [UNIT-0001.md](./UNIT-0001.md) |
| UNIT-0002 | test_resolve_alert_almacenista | [UNIT-0002.md](./UNIT-0002.md) |
| UNIT-0003 | test_resolve_alert_rejects_auxiliar | [UNIT-0003.md](./UNIT-0003.md) |
| UNIT-0004 | test_sync_expiry_alerts_for_product_creates_lot_alert | [UNIT-0004.md](./UNIT-0004.md) |
| UNIT-0005 | test_alerts_views_are_available | [UNIT-0005.md](./UNIT-0005.md) |
| UNIT-0006 | test_audit_model_exposes_event_types | [UNIT-0006.md](./UNIT-0006.md) |
| UNIT-0007 | test_audit_log_metadata_mutable_in_memory | [UNIT-0007.md](./UNIT-0007.md) |
| UNIT-0008 | test_login_failure_logged | [UNIT-0008.md](./UNIT-0008.md) |
| UNIT-0009 | test_login_success_logged | [UNIT-0009.md](./UNIT-0009.md) |
| UNIT-0010 | test_movement_creation_logged | [UNIT-0010.md](./UNIT-0010.md) |
| UNIT-0011 | test_audit_views_are_available | [UNIT-0011.md](./UNIT-0011.md) |
| UNIT-0012 | test_user_model_exposes_role_choices | [UNIT-0012.md](./UNIT-0012.md) |
| UNIT-0013 | test_auxiliar_blocked_outside_hours | [UNIT-0013.md](./UNIT-0013.md) |
| UNIT-0014 | test_disabled_user_cannot_login | [UNIT-0014.md](./UNIT-0014.md) |
| UNIT-0015 | test_only_almacenista_creates_users | [UNIT-0015.md](./UNIT-0015.md) |
| UNIT-0016 | test_only_almacenista_disables_users | [UNIT-0016.md](./UNIT-0016.md) |
| UNIT-0017 | test_only_almacenista_updates_users | [UNIT-0017.md](./UNIT-0017.md) |
| UNIT-0018 | test_operating_hours_enforced_per_request | [UNIT-0018.md](./UNIT-0018.md) |
| UNIT-0019 | test_administrador_can_read_users_but_cannot_write | [UNIT-0019.md](./UNIT-0019.md) |
| UNIT-0020 | test_auth_views_are_exposed | [UNIT-0020.md](./UNIT-0020.md) |
| UNIT-0021 | test_category_slug_unique | [UNIT-0021.md](./UNIT-0021.md) |
| UNIT-0022 | test_product_full_clean_rejects_invalid_sku_format | [UNIT-0022.md](./UNIT-0022.md) |
| UNIT-0023 | test_product_sku_field | [UNIT-0023.md](./UNIT-0023.md) |
| UNIT-0024 | test_catalog_service_exports_identifier_resolver | [UNIT-0024.md](./UNIT-0024.md) |
| UNIT-0025 | test_create_product_auto_generates_stable_barcode | [UNIT-0025.md](./UNIT-0025.md) |
| UNIT-0026 | test_update_product_backfills_missing_barcode | [UNIT-0026.md](./UNIT-0026.md) |
| UNIT-0027 | test_update_product_keeps_existing_barcode | [UNIT-0027.md](./UNIT-0027.md) |
| UNIT-0028 | test_catalog_views_are_available | [UNIT-0028.md](./UNIT-0028.md) |
| UNIT-0029 | test_product_barcode_endpoint_returns_ready_to_consume_payload | [UNIT-0029.md](./UNIT-0029.md) |
| UNIT-0030 | test_stock_by_location_admin_is_least_privilege_derived_stock | [UNIT-0030.md](./UNIT-0030.md) |
| UNIT-0031 | test_inventory_models_define_location_and_stock_cache | [UNIT-0031.md](./UNIT-0031.md) |
| UNIT-0032 | test_negative_stock_constraint_enforced | [UNIT-0032.md](./UNIT-0032.md) |
| UNIT-0033 | test_search_products_performance_under_2s | [UNIT-0033.md](./UNIT-0033.md) |
| UNIT-0034 | test_stock_query_returns_per_location_and_total | [UNIT-0034.md](./UNIT-0034.md) |
| UNIT-0035 | test_inventory_service_exports_current_stock_reader | [UNIT-0035.md](./UNIT-0035.md) |
| UNIT-0036 | test_inventory_views_are_available | [UNIT-0036.md](./UNIT-0036.md) |
| UNIT-0037 | test_movement_type_labels | [UNIT-0037.md](./UNIT-0037.md) |
| UNIT-0038 | test_adjustment_requires_justification | [UNIT-0038.md](./UNIT-0038.md) |
| UNIT-0039 | test_correction_within_window_creates_reversal_and_fixed | [UNIT-0039.md](./UNIT-0039.md) |
| UNIT-0040 | test_dispatch_chooses_earliest_lot_when_expiring_product | [UNIT-0040.md](./UNIT-0040.md) |
| UNIT-0041 | test_dispatch_cross_validation_fails_wrong_sku | [UNIT-0041.md](./UNIT-0041.md) |
| UNIT-0042 | test_entry_discrepancy_note_required_when_qty_mismatch | [UNIT-0042.md](./UNIT-0042.md) |
| UNIT-0043 | test_entry_electroterapia_without_serial_fails | [UNIT-0043.md](./UNIT-0043.md) |
| UNIT-0044 | test_entry_increments_stock_and_creates_ledger_record | [UNIT-0044.md](./UNIT-0044.md) |
| UNIT-0045 | test_entry_with_lot_persists_lot_on_movement | [UNIT-0045.md](./UNIT-0045.md) |
| UNIT-0046 | test_internal_transfer_does_not_change_global_stock | [UNIT-0046.md](./UNIT-0046.md) |
| UNIT-0047 | test_return_blocked_for_non_returnable_category | [UNIT-0047.md](./UNIT-0047.md) |
| UNIT-0048 | test_stock_can_be_reconstructed_from_ledger | [UNIT-0048.md](./UNIT-0048.md) |
| UNIT-0049 | test_movement_views_are_available | [UNIT-0049.md](./UNIT-0049.md) |
| UNIT-0050 | test_reports_app_has_no_domain_models | [UNIT-0050.md](./UNIT-0050.md) |
| UNIT-0051 | test_generate_kpis_returns_dashboard_keys | [UNIT-0051.md](./UNIT-0051.md) |
| UNIT-0052 | test_get_expiring_products_returns_lot_rows | [UNIT-0052.md](./UNIT-0052.md) |
| UNIT-0053 | test_reports_dataset_view_is_available | [UNIT-0053.md](./UNIT-0053.md) |
| UNIT-0054 | test_reports_expiring_view_returns_lots | [UNIT-0054.md](./UNIT-0054.md) |
| UNIT-0055 | test_reports_views_are_available | [UNIT-0055.md](./UNIT-0055.md) |


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0001.md -->

**CÃ³digo:** UNIT-0001

# test_alert_type_low_stock

## Nombre del test

`apps/alerts/tests/test_models.py::test_alert_type_low_stock`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/alerts/tests/test_models.py::test_alert_type_low_stock -v
```

CÃ³digo: [`apps/alerts/tests/test_models.py`](../../apps/alerts/tests/test_models.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0002.md -->

**CÃ³digo:** UNIT-0002

# test_resolve_alert_almacenista

## Nombre del test

`apps/alerts/tests/test_services.py::test_resolve_alert_almacenista`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/alerts/tests/test_services.py::test_resolve_alert_almacenista -v
```

CÃ³digo: [`apps/alerts/tests/test_services.py`](../../apps/alerts/tests/test_services.py) (aprox. lÃ­nea 12)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0003.md -->

**CÃ³digo:** UNIT-0003

# test_resolve_alert_rejects_auxiliar

## Nombre del test

`apps/alerts/tests/test_services.py::test_resolve_alert_rejects_auxiliar`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/alerts/tests/test_services.py::test_resolve_alert_rejects_auxiliar -v
```

CÃ³digo: [`apps/alerts/tests/test_services.py`](../../apps/alerts/tests/test_services.py) (aprox. lÃ­nea 25)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0004.md -->

**CÃ³digo:** UNIT-0004

# test_sync_expiry_alerts_for_product_creates_lot_alert

## Nombre del test

`apps/alerts/tests/test_services.py::test_sync_expiry_alerts_for_product_creates_lot_alert`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/alerts/tests/test_services.py::test_sync_expiry_alerts_for_product_creates_lot_alert -v
```

CÃ³digo: [`apps/alerts/tests/test_services.py`](../../apps/alerts/tests/test_services.py) (aprox. lÃ­nea 37)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0005.md -->

**CÃ³digo:** UNIT-0005

# test_alerts_views_are_available

## Nombre del test

`apps/alerts/tests/test_views.py::test_alerts_views_are_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/alerts/tests/test_views.py::test_alerts_views_are_available -v
```

CÃ³digo: [`apps/alerts/tests/test_views.py`](../../apps/alerts/tests/test_views.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0006.md -->

**CÃ³digo:** UNIT-0006

# test_audit_model_exposes_event_types

## Nombre del test

`apps/audit/tests/test_models.py::test_audit_model_exposes_event_types`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_models.py::test_audit_model_exposes_event_types -v
```

CÃ³digo: [`apps/audit/tests/test_models.py`](../../apps/audit/tests/test_models.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0007.md -->

**CÃ³digo:** UNIT-0007

# test_audit_log_metadata_mutable_in_memory

## Nombre del test

`apps/audit/tests/test_services.py::test_audit_log_metadata_mutable_in_memory`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_services.py::test_audit_log_metadata_mutable_in_memory -v
```

CÃ³digo: [`apps/audit/tests/test_services.py`](../../apps/audit/tests/test_services.py) (aprox. lÃ­nea 48)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0008.md -->

**CÃ³digo:** UNIT-0008

# test_login_failure_logged

## Nombre del test

`apps/audit/tests/test_services.py::test_login_failure_logged`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_services.py::test_login_failure_logged -v
```

CÃ³digo: [`apps/audit/tests/test_services.py`](../../apps/audit/tests/test_services.py) (aprox. lÃ­nea 23)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0009.md -->

**CÃ³digo:** UNIT-0009

# test_login_success_logged

## Nombre del test

`apps/audit/tests/test_services.py::test_login_success_logged`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_services.py::test_login_success_logged -v
```

CÃ³digo: [`apps/audit/tests/test_services.py`](../../apps/audit/tests/test_services.py) (aprox. lÃ­nea 13)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0010.md -->

**CÃ³digo:** UNIT-0010

# test_movement_creation_logged

## Nombre del test

`apps/audit/tests/test_services.py::test_movement_creation_logged`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_services.py::test_movement_creation_logged -v
```

CÃ³digo: [`apps/audit/tests/test_services.py`](../../apps/audit/tests/test_services.py) (aprox. lÃ­nea 30)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0011.md -->

**CÃ³digo:** UNIT-0011

# test_audit_views_are_available

## Nombre del test

`apps/audit/tests/test_views.py::test_audit_views_are_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/audit/tests/test_views.py::test_audit_views_are_available -v
```

CÃ³digo: [`apps/audit/tests/test_views.py`](../../apps/audit/tests/test_views.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0012.md -->

**CÃ³digo:** UNIT-0012

# test_user_model_exposes_role_choices

## Nombre del test

`apps/authentication/tests/test_models.py::test_user_model_exposes_role_choices`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_models.py::test_user_model_exposes_role_choices -v
```

CÃ³digo: [`apps/authentication/tests/test_models.py`](../../apps/authentication/tests/test_models.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0013.md -->

**CÃ³digo:** UNIT-0013

# test_auxiliar_blocked_outside_hours

## Nombre del test

`apps/authentication/tests/test_services.py::test_auxiliar_blocked_outside_hours`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_services.py::test_auxiliar_blocked_outside_hours -v
```

CÃ³digo: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. lÃ­nea 25)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0014.md -->

**CÃ³digo:** UNIT-0014

# test_disabled_user_cannot_login

## Nombre del test

`apps/authentication/tests/test_services.py::test_disabled_user_cannot_login`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_services.py::test_disabled_user_cannot_login -v
```

CÃ³digo: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. lÃ­nea 72)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0015.md -->

**CÃ³digo:** UNIT-0015

# test_only_almacenista_creates_users

## Nombre del test

`apps/authentication/tests/test_services.py::test_only_almacenista_creates_users`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_services.py::test_only_almacenista_creates_users -v
```

CÃ³digo: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. lÃ­nea 35)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0016.md -->

**CÃ³digo:** UNIT-0016

# test_only_almacenista_disables_users

## Nombre del test

`apps/authentication/tests/test_services.py::test_only_almacenista_disables_users`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_services.py::test_only_almacenista_disables_users -v
```

CÃ³digo: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. lÃ­nea 64)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0017.md -->

**CÃ³digo:** UNIT-0017

# test_only_almacenista_updates_users

## Nombre del test

`apps/authentication/tests/test_services.py::test_only_almacenista_updates_users`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_services.py::test_only_almacenista_updates_users -v
```

CÃ³digo: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. lÃ­nea 51)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0018.md -->

**CÃ³digo:** UNIT-0018

# test_operating_hours_enforced_per_request

## Nombre del test

`apps/authentication/tests/test_services.py::test_operating_hours_enforced_per_request`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_services.py::test_operating_hours_enforced_per_request -v
```

CÃ³digo: [`apps/authentication/tests/test_services.py`](../../apps/authentication/tests/test_services.py) (aprox. lÃ­nea 79)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0019.md -->

**CÃ³digo:** UNIT-0019

# test_administrador_can_read_users_but_cannot_write

## Nombre del test

`apps/authentication/tests/test_views.py::test_administrador_can_read_users_but_cannot_write`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_views.py::test_administrador_can_read_users_but_cannot_write -v
```

CÃ³digo: [`apps/authentication/tests/test_views.py`](../../apps/authentication/tests/test_views.py) (aprox. lÃ­nea 13)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0020.md -->

**CÃ³digo:** UNIT-0020

# test_auth_views_are_exposed

## Nombre del test

`apps/authentication/tests/test_views.py::test_auth_views_are_exposed`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/authentication/tests/test_views.py::test_auth_views_are_exposed -v
```

CÃ³digo: [`apps/authentication/tests/test_views.py`](../../apps/authentication/tests/test_views.py) (aprox. lÃ­nea 44)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0021.md -->

**CÃ³digo:** UNIT-0021

# test_category_slug_unique

## Nombre del test

`apps/catalog/tests/test_models.py::test_category_slug_unique`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_models.py::test_category_slug_unique -v
```

CÃ³digo: [`apps/catalog/tests/test_models.py`](../../apps/catalog/tests/test_models.py) (aprox. lÃ­nea 12)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0022.md -->

**CÃ³digo:** UNIT-0022

# test_product_full_clean_rejects_invalid_sku_format

## Nombre del test

`apps/catalog/tests/test_models.py::test_product_full_clean_rejects_invalid_sku_format`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_models.py::test_product_full_clean_rejects_invalid_sku_format -v
```

CÃ³digo: [`apps/catalog/tests/test_models.py`](../../apps/catalog/tests/test_models.py) (aprox. lÃ­nea 17)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0023.md -->

**CÃ³digo:** UNIT-0023

# test_product_sku_field

## Nombre del test

`apps/catalog/tests/test_models.py::test_product_sku_field`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_models.py::test_product_sku_field -v
```

CÃ³digo: [`apps/catalog/tests/test_models.py`](../../apps/catalog/tests/test_models.py) (aprox. lÃ­nea 8)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0024.md -->

**CÃ³digo:** UNIT-0024

# test_catalog_service_exports_identifier_resolver

## Nombre del test

`apps/catalog/tests/test_services.py::test_catalog_service_exports_identifier_resolver`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_services.py::test_catalog_service_exports_identifier_resolver -v
```

CÃ³digo: [`apps/catalog/tests/test_services.py`](../../apps/catalog/tests/test_services.py) (aprox. lÃ­nea 9)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0025.md -->

**CÃ³digo:** UNIT-0025

# test_create_product_auto_generates_stable_barcode

## Nombre del test

`apps/catalog/tests/test_services.py::test_create_product_auto_generates_stable_barcode`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_services.py::test_create_product_auto_generates_stable_barcode -v
```

CÃ³digo: [`apps/catalog/tests/test_services.py`](../../apps/catalog/tests/test_services.py) (aprox. lÃ­nea 14)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0026.md -->

**CÃ³digo:** UNIT-0026

# test_update_product_backfills_missing_barcode

## Nombre del test

`apps/catalog/tests/test_services.py::test_update_product_backfills_missing_barcode`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_services.py::test_update_product_backfills_missing_barcode -v
```

CÃ³digo: [`apps/catalog/tests/test_services.py`](../../apps/catalog/tests/test_services.py) (aprox. lÃ­nea 63)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0027.md -->

**CÃ³digo:** UNIT-0027

# test_update_product_keeps_existing_barcode

## Nombre del test

`apps/catalog/tests/test_services.py::test_update_product_keeps_existing_barcode`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_services.py::test_update_product_keeps_existing_barcode -v
```

CÃ³digo: [`apps/catalog/tests/test_services.py`](../../apps/catalog/tests/test_services.py) (aprox. lÃ­nea 41)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0028.md -->

**CÃ³digo:** UNIT-0028

# test_catalog_views_are_available

## Nombre del test

`apps/catalog/tests/test_views.py::test_catalog_views_are_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_views.py::test_catalog_views_are_available -v
```

CÃ³digo: [`apps/catalog/tests/test_views.py`](../../apps/catalog/tests/test_views.py) (aprox. lÃ­nea 7)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0029.md -->

**CÃ³digo:** UNIT-0029

# test_product_barcode_endpoint_returns_ready_to_consume_payload

## Nombre del test

`apps/catalog/tests/test_views.py::test_product_barcode_endpoint_returns_ready_to_consume_payload`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/catalog/tests/test_views.py::test_product_barcode_endpoint_returns_ready_to_consume_payload -v
```

CÃ³digo: [`apps/catalog/tests/test_views.py`](../../apps/catalog/tests/test_views.py) (aprox. lÃ­nea 15)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0030.md -->

**CÃ³digo:** UNIT-0030

# test_stock_by_location_admin_is_least_privilege_derived_stock

## Nombre del test

`apps/inventory/tests/test_admin.py::test_stock_by_location_admin_is_least_privilege_derived_stock`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_admin.py::test_stock_by_location_admin_is_least_privilege_derived_stock -v
```

CÃ³digo: [`apps/inventory/tests/test_admin.py`](../../apps/inventory/tests/test_admin.py) (aprox. lÃ­nea 15)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0031.md -->

**CÃ³digo:** UNIT-0031

# test_inventory_models_define_location_and_stock_cache

## Nombre del test

`apps/inventory/tests/test_models.py::test_inventory_models_define_location_and_stock_cache`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_models.py::test_inventory_models_define_location_and_stock_cache -v
```

CÃ³digo: [`apps/inventory/tests/test_models.py`](../../apps/inventory/tests/test_models.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0032.md -->

**CÃ³digo:** UNIT-0032

# test_negative_stock_constraint_enforced

## Nombre del test

`apps/inventory/tests/test_selectors.py::test_negative_stock_constraint_enforced`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_selectors.py::test_negative_stock_constraint_enforced -v
```

CÃ³digo: [`apps/inventory/tests/test_selectors.py`](../../apps/inventory/tests/test_selectors.py) (aprox. lÃ­nea 31)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0033.md -->

**CÃ³digo:** UNIT-0033

# test_search_products_performance_under_2s

## Nombre del test

`apps/inventory/tests/test_selectors.py::test_search_products_performance_under_2s`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_selectors.py::test_search_products_performance_under_2s -v
```

CÃ³digo: [`apps/inventory/tests/test_selectors.py`](../../apps/inventory/tests/test_selectors.py) (aprox. lÃ­nea 42)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0034.md -->

**CÃ³digo:** UNIT-0034

# test_stock_query_returns_per_location_and_total

## Nombre del test

`apps/inventory/tests/test_selectors.py::test_stock_query_returns_per_location_and_total`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_selectors.py::test_stock_query_returns_per_location_and_total -v
```

CÃ³digo: [`apps/inventory/tests/test_selectors.py`](../../apps/inventory/tests/test_selectors.py) (aprox. lÃ­nea 13)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0035.md -->

**CÃ³digo:** UNIT-0035

# test_inventory_service_exports_current_stock_reader

## Nombre del test

`apps/inventory/tests/test_services.py::test_inventory_service_exports_current_stock_reader`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_services.py::test_inventory_service_exports_current_stock_reader -v
```

CÃ³digo: [`apps/inventory/tests/test_services.py`](../../apps/inventory/tests/test_services.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0036.md -->

**CÃ³digo:** UNIT-0036

# test_inventory_views_are_available

## Nombre del test

`apps/inventory/tests/test_views.py::test_inventory_views_are_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/inventory/tests/test_views.py::test_inventory_views_are_available -v
```

CÃ³digo: [`apps/inventory/tests/test_views.py`](../../apps/inventory/tests/test_views.py) (aprox. lÃ­nea 6)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0037.md -->

**CÃ³digo:** UNIT-0037

# test_movement_type_labels

## Nombre del test

`apps/movements/tests/test_models.py::test_movement_type_labels`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_models.py::test_movement_type_labels -v
```

CÃ³digo: [`apps/movements/tests/test_models.py`](../../apps/movements/tests/test_models.py) (aprox. lÃ­nea 4)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0038.md -->

**CÃ³digo:** UNIT-0038

# test_adjustment_requires_justification

## Nombre del test

`apps/movements/tests/test_services.py::test_adjustment_requires_justification`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_adjustment_requires_justification -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 225)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0039.md -->

**CÃ³digo:** UNIT-0039

# test_correction_within_window_creates_reversal_and_fixed

## Nombre del test

`apps/movements/tests/test_services.py::test_correction_within_window_creates_reversal_and_fixed`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_correction_within_window_creates_reversal_and_fixed -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 259)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0040.md -->

**CÃ³digo:** UNIT-0040

# test_dispatch_chooses_earliest_lot_when_expiring_product

## Nombre del test

`apps/movements/tests/test_services.py::test_dispatch_chooses_earliest_lot_when_expiring_product`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_dispatch_chooses_earliest_lot_when_expiring_product -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 70)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0041.md -->

**CÃ³digo:** UNIT-0041

# test_dispatch_cross_validation_fails_wrong_sku

## Nombre del test

`apps/movements/tests/test_services.py::test_dispatch_cross_validation_fails_wrong_sku`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_dispatch_cross_validation_fails_wrong_sku -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 163)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0042.md -->

**CÃ³digo:** UNIT-0042

# test_entry_discrepancy_note_required_when_qty_mismatch

## Nombre del test

`apps/movements/tests/test_services.py::test_entry_discrepancy_note_required_when_qty_mismatch`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_entry_discrepancy_note_required_when_qty_mismatch -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 146)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0043.md -->

**CÃ³digo:** UNIT-0043

# test_entry_electroterapia_without_serial_fails

## Nombre del test

`apps/movements/tests/test_services.py::test_entry_electroterapia_without_serial_fails`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_entry_electroterapia_without_serial_fails -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 130)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0044.md -->

**CÃ³digo:** UNIT-0044

# test_entry_increments_stock_and_creates_ledger_record

## Nombre del test

`apps/movements/tests/test_services.py::test_entry_increments_stock_and_creates_ledger_record`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_entry_increments_stock_and_creates_ledger_record -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 26)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0045.md -->

**CÃ³digo:** UNIT-0045

# test_entry_with_lot_persists_lot_on_movement

## Nombre del test

`apps/movements/tests/test_services.py::test_entry_with_lot_persists_lot_on_movement`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_entry_with_lot_persists_lot_on_movement -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 45)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0046.md -->

**CÃ³digo:** UNIT-0046

# test_internal_transfer_does_not_change_global_stock

## Nombre del test

`apps/movements/tests/test_services.py::test_internal_transfer_does_not_change_global_stock`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_internal_transfer_does_not_change_global_stock -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 185)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0047.md -->

**CÃ³digo:** UNIT-0047

# test_return_blocked_for_non_returnable_category

## Nombre del test

`apps/movements/tests/test_services.py::test_return_blocked_for_non_returnable_category`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_return_blocked_for_non_returnable_category -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 213)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0048.md -->

**CÃ³digo:** UNIT-0048

# test_stock_can_be_reconstructed_from_ledger

## Nombre del test

`apps/movements/tests/test_services.py::test_stock_can_be_reconstructed_from_ledger`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_services.py::test_stock_can_be_reconstructed_from_ledger -v
```

CÃ³digo: [`apps/movements/tests/test_services.py`](../../apps/movements/tests/test_services.py) (aprox. lÃ­nea 237)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0049.md -->

**CÃ³digo:** UNIT-0049

# test_movement_views_are_available

## Nombre del test

`apps/movements/tests/test_views.py::test_movement_views_are_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/movements/tests/test_views.py::test_movement_views_are_available -v
```

CÃ³digo: [`apps/movements/tests/test_views.py`](../../apps/movements/tests/test_views.py) (aprox. lÃ­nea 6)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0050.md -->

**CÃ³digo:** UNIT-0050

# test_reports_app_has_no_domain_models

## Nombre del test

`apps/reports/tests/test_models.py::test_reports_app_has_no_domain_models`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/reports/tests/test_models.py::test_reports_app_has_no_domain_models -v
```

CÃ³digo: [`apps/reports/tests/test_models.py`](../../apps/reports/tests/test_models.py) (aprox. lÃ­nea 1)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0051.md -->

**CÃ³digo:** UNIT-0051

# test_generate_kpis_returns_dashboard_keys

## Nombre del test

`apps/reports/tests/test_services.py::test_generate_kpis_returns_dashboard_keys`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/reports/tests/test_services.py::test_generate_kpis_returns_dashboard_keys -v
```

CÃ³digo: [`apps/reports/tests/test_services.py`](../../apps/reports/tests/test_services.py) (aprox. lÃ­nea 35)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0052.md -->

**CÃ³digo:** UNIT-0052

# test_get_expiring_products_returns_lot_rows

## Nombre del test

`apps/reports/tests/test_services.py::test_get_expiring_products_returns_lot_rows`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/reports/tests/test_services.py::test_get_expiring_products_returns_lot_rows -v
```

CÃ³digo: [`apps/reports/tests/test_services.py`](../../apps/reports/tests/test_services.py) (aprox. lÃ­nea 5)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0053.md -->

**CÃ³digo:** UNIT-0053

# test_reports_dataset_view_is_available

## Nombre del test

`apps/reports/tests/test_views.py::test_reports_dataset_view_is_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/reports/tests/test_views.py::test_reports_dataset_view_is_available -v
```

CÃ³digo: [`apps/reports/tests/test_views.py`](../../apps/reports/tests/test_views.py) (aprox. lÃ­nea 12)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0054.md -->

**CÃ³digo:** UNIT-0054

# test_reports_expiring_view_returns_lots

## Nombre del test

`apps/reports/tests/test_views.py::test_reports_expiring_view_returns_lots`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/reports/tests/test_views.py::test_reports_expiring_view_returns_lots -v
```

CÃ³digo: [`apps/reports/tests/test_views.py`](../../apps/reports/tests/test_views.py) (aprox. lÃ­nea 21)


<!-- file: C:\Users\JUAN JOSE\PycharmProjects\Sistema_Inventario_ICM\docs\test\unit\UNIT-0055.md -->

**CÃ³digo:** UNIT-0055

# test_reports_views_are_available

## Nombre del test

`apps/reports/tests/test_views.py::test_reports_views_are_available`

## PropÃ³sito

Prueba unitaria del backend ICM.

## Requisito o caso de negocio asociado

Ver docstring del test y mÃ³dulo; trazabilidad RF/BR en `docs/test/TRAZABILIDAD_ERS_GHERKIN.md` cuando aplique.

## Inputs

Fixtures pytest (`conftest.py`, `tests/factories.py`) y datos creados en el propio test. Ver implementaciÃ³n.

## Resultado esperado

Aserciones del test (`assert`); ver cÃ³digo en la lÃ­nea indicada abajo.

## Link directo al test

```bash
pytest apps/reports/tests/test_views.py::test_reports_views_are_available -v
```

CÃ³digo: [`apps/reports/tests/test_views.py`](../../apps/reports/tests/test_views.py) (aprox. lÃ­nea 53)
