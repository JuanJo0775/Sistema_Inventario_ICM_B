# Índice de tests auxiliares

| Categoría | Prefijo | Tests | Sub-índice |
|---|---|---|---|
| tests de scripts | SCR | 29 | [scripts/index.md](./scripts/index.md) |
| tests de utilidades compartidas | SHA | 5 | [shared/index.md](./shared/index.md) |
| tests de SLA (Service Level Agreement) | SLA | 4 | [sla/index.md](./sla/index.md) |

---

## tests de scripts

| Código | Test | Archivo |
|---|---|---|
| SCR-0001 | test_classify_test_coverage | [SCR-0001.md](./scripts/SCR-0001.md) |
| SCR-0002 | test_docnode_short_name_class_method | [SCR-0002.md](./scripts/SCR-0002.md) |
| SCR-0003 | test_docnode_short_name_simple | [SCR-0003.md](./scripts/SCR-0003.md) |
| SCR-0004 | test_generation_summary_absorb_does_not_unset_changed | [SCR-0004.md](./scripts/SCR-0004.md) |
| SCR-0005 | test_generation_summary_absorb_merges_paths | [SCR-0005.md](./scripts/SCR-0005.md) |
| SCR-0006 | test_remove_stale_check_mode_does_not_delete | [SCR-0006.md](./scripts/SCR-0006.md) |
| SCR-0007 | test_remove_stale_deletes_unexpected_files | [SCR-0007.md](./scripts/SCR-0007.md) |
| SCR-0008 | test_remove_stale_nonexistent_dir_returns_empty | [SCR-0008.md](./scripts/SCR-0008.md) |
| SCR-0009 | test_write_check_mode_does_not_write | [SCR-0009.md](./scripts/SCR-0009.md) |
| SCR-0010 | test_write_creates_file | [SCR-0010.md](./scripts/SCR-0010.md) |
| SCR-0011 | test_write_skips_if_content_unchanged | [SCR-0011.md](./scripts/SCR-0011.md) |
| SCR-0012 | test_write_updates_if_content_changed | [SCR-0012.md](./scripts/SCR-0012.md) |
| SCR-0013 | test_change_report_detects_additions_and_removals | [SCR-0013.md](./scripts/SCR-0013.md) |
| SCR-0014 | test_semantic_comment_for_services_is_specific | [SCR-0014.md](./scripts/SCR-0014.md) |
| SCR-0015 | test_tree_ignores_noise_and_keeps_relevant_nodes | [SCR-0015.md](./scripts/SCR-0015.md) |
| SCR-0016 | test_wrapper_is_alias_of_generate_docs_main | [SCR-0016.md](./scripts/SCR-0016.md) |
| SCR-0017 | test_wrapper_passthrough_return_values | [SCR-0017.md](./scripts/SCR-0017.md) |
| SCR-0018 | test_has_wait_time | [SCR-0018.md](./scripts/SCR-0018.md) |
| SCR-0019 | test_imports_cleanly | [SCR-0019.md](./scripts/SCR-0019.md) |
| SCR-0020 | test_tasks_defined | [SCR-0020.md](./scripts/SCR-0020.md) |
| SCR-0021 | test_all_category_slugs_declared | [SCR-0021.md](./scripts/SCR-0021.md) |
| SCR-0022 | test_all_product_skus_valid_format | [SCR-0022.md](./scripts/SCR-0022.md) |
| SCR-0023 | test_combo_items_reference_known_skus | [SCR-0023.md](./scripts/SCR-0023.md) |
| SCR-0024 | test_electroterapia_requires_serial | [SCR-0024.md](./scripts/SCR-0024.md) |
| SCR-0025 | test_expiration_products_have_valid_skus | [SCR-0025.md](./scripts/SCR-0025.md) |
| SCR-0026 | test_no_duplicate_product_skus | [SCR-0026.md](./scripts/SCR-0026.md) |
| SCR-0027 | test_clean_removes_seed_data_preserves_base | [SCR-0027.md](./scripts/SCR-0027.md) |
| SCR-0028 | test_seed_creates_catalog_and_movements | [SCR-0028.md](./scripts/SCR-0028.md) |
| SCR-0029 | test_seed_is_idempotent | [SCR-0029.md](./scripts/SCR-0029.md) |

## tests de utilidades compartidas

| Código | Test | Archivo |
|---|---|---|
| SHA-0001 | test_validate_destination_passes_for_non_blocked | [SHA-0001.md](./shared/SHA-0001.md) |
| SHA-0002 | test_validate_destination_raises_for_blocked_archived | [SHA-0002.md](./shared/SHA-0002.md) |
| SHA-0003 | test_validate_origin_passes_for_active | [SHA-0003.md](./shared/SHA-0003.md) |
| SHA-0004 | test_validate_origin_raises_for_blocked_archived | [SHA-0004.md](./shared/SHA-0004.md) |
| SHA-0005 | test_validate_origin_raises_for_maintenance_restricted | [SHA-0005.md](./shared/SHA-0005.md) |

## tests de SLA (Service Level Agreement)

| Código | Test | Archivo |
|---|---|---|
| SLA-0001 | test_dashboard_kpis_completes_within_sla | [SLA-0001.md](./sla/SLA-0001.md) |
| SLA-0002 | test_inventory_selector_completes_within_sla | [SLA-0002.md](./sla/SLA-0002.md) |
| SLA-0003 | test_ledger_net_qty_completes_within_sla | [SLA-0003.md](./sla/SLA-0003.md) |
| SLA-0004 | test_register_entry_completes_within_sla | [SLA-0004.md](./sla/SLA-0004.md) |

