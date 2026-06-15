# Índice de tests auxiliares

| Categoría | Prefijo | Tests | Sub-índice |
|---|---|---|---|
| tests de scripts | SCR | 69 | [scripts/index.md](./scripts/index.md) |
| tests de utilidades compartidas | SHA | 8 | [shared/index.md](./shared/index.md) |
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
| SCR-0021 | test_ci_flag | [SCR-0021.md](./scripts/SCR-0021.md) |
| SCR-0022 | test_default_ci_is_false | [SCR-0022.md](./scripts/SCR-0022.md) |
| SCR-0023 | test_default_dry_run_is_false | [SCR-0023.md](./scripts/SCR-0023.md) |
| SCR-0024 | test_default_list_is_false | [SCR-0024.md](./scripts/SCR-0024.md) |
| SCR-0025 | test_default_only_is_empty | [SCR-0025.md](./scripts/SCR-0025.md) |
| SCR-0026 | test_default_output_path | [SCR-0026.md](./scripts/SCR-0026.md) |
| SCR-0027 | test_default_skip_is_empty | [SCR-0027.md](./scripts/SCR-0027.md) |
| SCR-0028 | test_dry_run_flag | [SCR-0028.md](./scripts/SCR-0028.md) |
| SCR-0029 | test_list_flag | [SCR-0029.md](./scripts/SCR-0029.md) |
| SCR-0030 | test_only_and_skip_parsed_together | [SCR-0030.md](./scripts/SCR-0030.md) |
| SCR-0031 | test_only_flag | [SCR-0031.md](./scripts/SCR-0031.md) |
| SCR-0032 | test_output_custom | [SCR-0032.md](./scripts/SCR-0032.md) |
| SCR-0033 | test_skip_flag | [SCR-0033.md](./scripts/SCR-0033.md) |
| SCR-0034 | test_empty_only_returns_all | [SCR-0034.md](./scripts/SCR-0034.md) |
| SCR-0035 | test_only_and_skip_both_empty_returns_all | [SCR-0035.md](./scripts/SCR-0035.md) |
| SCR-0036 | test_only_returns_matching_tools | [SCR-0036.md](./scripts/SCR-0036.md) |
| SCR-0037 | test_only_selects_multiple_tools | [SCR-0037.md](./scripts/SCR-0037.md) |
| SCR-0038 | test_only_selects_specific_tool | [SCR-0038.md](./scripts/SCR-0038.md) |
| SCR-0039 | test_skip_excludes_tool | [SCR-0039.md](./scripts/SCR-0039.md) |
| SCR-0040 | test_skip_multiple_tools | [SCR-0040.md](./scripts/SCR-0040.md) |
| SCR-0041 | test_unknown_only_raises_system_exit | [SCR-0041.md](./scripts/SCR-0041.md) |
| SCR-0042 | test_unknown_skip_raises_system_exit | [SCR-0042.md](./scripts/SCR-0042.md) |
| SCR-0043 | test_ci_flag_applies_ci_flags | [SCR-0043.md](./scripts/SCR-0043.md) |
| SCR-0044 | test_ci_flag_no_ci_flags_unchanged | [SCR-0044.md](./scripts/SCR-0044.md) |
| SCR-0045 | test_dry_run_never_executes | [SCR-0045.md](./scripts/SCR-0045.md) |
| SCR-0046 | test_dry_run_returns_ok_and_command | [SCR-0046.md](./scripts/SCR-0046.md) |
| SCR-0047 | test_file_not_found_returns_fail | [SCR-0047.md](./scripts/SCR-0047.md) |
| SCR-0048 | test_ascii_punctuation_passes | [SCR-0048.md](./scripts/SCR-0048.md) |
| SCR-0049 | test_empty_string | [SCR-0049.md](./scripts/SCR-0049.md) |
| SCR-0050 | test_plain_text_passes_through | [SCR-0050.md](./scripts/SCR-0050.md) |
| SCR-0051 | test_unicode_box_chars_stripped | [SCR-0051.md](./scripts/SCR-0051.md) |
| SCR-0052 | test_unicode_checkmark_stripped | [SCR-0052.md](./scripts/SCR-0052.md) |
| SCR-0053 | test_unicode_xmark_stripped | [SCR-0053.md](./scripts/SCR-0053.md) |
| SCR-0054 | test_all_tools_defined | [SCR-0054.md](./scripts/SCR-0054.md) |
| SCR-0055 | test_bandit_cmd | [SCR-0055.md](./scripts/SCR-0055.md) |
| SCR-0056 | test_each_tool_has_required_keys | [SCR-0056.md](./scripts/SCR-0056.md) |
| SCR-0057 | test_mypy_cmd | [SCR-0057.md](./scripts/SCR-0057.md) |
| SCR-0058 | test_ruff_lint_cmd | [SCR-0058.md](./scripts/SCR-0058.md) |
| SCR-0059 | test_semgrep_has_ci_flags | [SCR-0059.md](./scripts/SCR-0059.md) |
| SCR-0060 | test_tool_names_are_unique | [SCR-0060.md](./scripts/SCR-0060.md) |
| SCR-0061 | test_all_category_slugs_declared | [SCR-0061.md](./scripts/SCR-0061.md) |
| SCR-0062 | test_all_product_skus_valid_format | [SCR-0062.md](./scripts/SCR-0062.md) |
| SCR-0063 | test_combo_items_reference_known_skus | [SCR-0063.md](./scripts/SCR-0063.md) |
| SCR-0064 | test_electroterapia_requires_serial | [SCR-0064.md](./scripts/SCR-0064.md) |
| SCR-0065 | test_expiration_products_have_valid_skus | [SCR-0065.md](./scripts/SCR-0065.md) |
| SCR-0066 | test_no_duplicate_product_skus | [SCR-0066.md](./scripts/SCR-0066.md) |
| SCR-0067 | test_clean_removes_seed_data_preserves_base | [SCR-0067.md](./scripts/SCR-0067.md) |
| SCR-0068 | test_seed_creates_catalog_and_movements | [SCR-0068.md](./scripts/SCR-0068.md) |
| SCR-0069 | test_seed_is_idempotent | [SCR-0069.md](./scripts/SCR-0069.md) |

## tests de utilidades compartidas

| Código | Test | Archivo |
|---|---|---|
| SHA-0001 | test_get_for_update_or_404_custom_message | [SHA-0001.md](./shared/SHA-0001.md) |
| SHA-0002 | test_get_for_update_or_404_found | [SHA-0002.md](./shared/SHA-0002.md) |
| SHA-0003 | test_get_for_update_or_404_not_found | [SHA-0003.md](./shared/SHA-0003.md) |
| SHA-0004 | test_validate_destination_passes_for_non_blocked | [SHA-0004.md](./shared/SHA-0004.md) |
| SHA-0005 | test_validate_destination_raises_for_blocked_archived | [SHA-0005.md](./shared/SHA-0005.md) |
| SHA-0006 | test_validate_origin_passes_for_active | [SHA-0006.md](./shared/SHA-0006.md) |
| SHA-0007 | test_validate_origin_raises_for_blocked_archived | [SHA-0007.md](./shared/SHA-0007.md) |
| SHA-0008 | test_validate_origin_raises_for_maintenance_restricted | [SHA-0008.md](./shared/SHA-0008.md) |

## tests de SLA (Service Level Agreement)

| Código | Test | Archivo |
|---|---|---|
| SLA-0001 | test_dashboard_kpis_completes_within_sla | [SLA-0001.md](./sla/SLA-0001.md) |
| SLA-0002 | test_inventory_selector_completes_within_sla | [SLA-0002.md](./sla/SLA-0002.md) |
| SLA-0003 | test_ledger_net_qty_completes_within_sla | [SLA-0003.md](./sla/SLA-0003.md) |
| SLA-0004 | test_register_entry_completes_within_sla | [SLA-0004.md](./sla/SLA-0004.md) |

