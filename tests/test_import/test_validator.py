"""Tests del validador de filas del Excel."""

from __future__ import annotations

import pytest

from scripts.import_catalog.reader import RawRow
from scripts.import_catalog.validator import validate


def make_row(
    codigo: str = "CM-01",
    producto: str = "Camilla Test",
    sheet: str = "Camillas",
    numero: int = 1,
) -> RawRow:
    return RawRow(sheet_name=sheet, codigo=codigo, numero=numero, producto=producto)


class TestValidate:
    def test_valid_sku_goes_to_ok(self):
        report = validate([make_row("CM-01")])
        assert len(report.ok) == 1
        assert len(report.needs_autogen) == 0
        assert len(report.invalid_sku) == 0
        assert len(report.errors) == 0

    def test_sc_sku_goes_to_needs_autogen(self):
        report = validate([make_row("S/C", producto="Flexbar Amarillo ICMTHERAPY")])
        assert len(report.needs_autogen) == 1
        assert len(report.ok) == 0

    def test_empty_sku_goes_to_needs_autogen(self):
        report = validate([make_row("")])
        assert len(report.needs_autogen) == 1

    def test_sc_uppercase_variants(self):
        for variant in ("S/C", "s/c", "SC", "sc"):
            report = validate([make_row(variant, producto="Flexbar")])
            assert len(report.needs_autogen) == 1, f"Fallo para variante: {variant!r}"

    def test_invalid_sku_format_goes_to_invalid(self):
        for bad_sku in ("MPC-01A", "MPC-02A", "EC-01b", "ABCDE-01", "CM-12345"):
            report = validate([make_row(bad_sku, producto="Producto")])
            assert len(report.invalid_sku) == 1, f"Esperaba inválido para: {bad_sku!r}"

    def test_valid_sku_boundary_cases(self):
        for valid_sku in ("A-1", "AB-12", "ABC-123", "ABCD-1234", "T-01"):
            report = validate([make_row(valid_sku, producto="Producto")])
            assert len(report.ok) == 1, f"Esperaba válido para: {valid_sku!r}"

    def test_empty_product_name_goes_to_errors(self):
        report = validate([make_row("CM-01", producto="")])
        assert len(report.errors) == 1
        assert len(report.ok) == 0

    def test_duplicate_sku_second_occurrence_goes_to_errors(self):
        rows = [
            make_row("CM-01", producto="Producto A"),
            make_row("CM-01", producto="Producto B"),
        ]
        report = validate(rows)
        assert (
            len(report.ok) == 2
        )  # ambas pasan a ok (pero la segunda también a errors)
        assert len(report.errors) == 1

    def test_multiple_valid_rows(self):
        rows = [make_row(f"CM-{i:02d}", producto=f"Producto {i}") for i in range(1, 6)]
        report = validate(rows)
        assert len(report.ok) == 5
        assert len(report.errors) == 0

    def test_mixed_rows(self):
        rows = [
            make_row("CM-01", producto="Válido"),
            make_row("S/C", producto="Sin código"),
            make_row("MPC-01A", producto="Inválido"),
            make_row("CM-02", producto=""),
        ]
        report = validate(rows)
        assert len(report.ok) == 1
        assert len(report.needs_autogen) == 1
        assert len(report.invalid_sku) == 1
        assert len(report.errors) == 1
