"""Tests de lectura del Excel."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.import_catalog.reader import RawRow, read_excel

EXCEL_PATH = (
    Path(__file__).resolve().parent.parent.parent / "Clasificacion_Productos.xlsx"
)


@pytest.mark.skipif(
    not EXCEL_PATH.exists(),
    reason="Excel del cliente no disponible en esta máquina.",
)
class TestReadExcel:
    def test_returns_rows_for_all_products(self):
        rows = read_excel(EXCEL_PATH)
        assert len(rows) > 200

    def test_skips_resumen_sheet(self):
        rows = read_excel(EXCEL_PATH)
        sheet_names = {r.sheet_name.lower() for r in rows}
        assert "resumen" not in sheet_names

    def test_has_all_expected_categories(self):
        rows = read_excel(EXCEL_PATH)
        categories = {r.sheet_name for r in rows}
        expected = {
            "Camillas",
            "Agujas",
            "Terapias de Mano",
            "Suelo Pélvico",
            "Electroterapia",
            "Pelotas",
            "Bandas",
            "Masajeadores",
            "Cintas",
            "Pedales",
            "Accesorios",
        }
        for cat in expected:
            assert cat in categories, f"Categoría faltante: {cat!r}"

    def test_skips_total_rows(self):
        rows = read_excel(EXCEL_PATH)
        for row in rows:
            assert (
                not str(row.codigo).lower().startswith("total")
            ), f"Fila de total no fue omitida: {row}"

    def test_all_rows_have_product_name(self):
        rows = read_excel(EXCEL_PATH)
        for row in rows:
            assert row.producto, f"Fila sin nombre en hoja '{row.sheet_name}': {row}"

    def test_all_rows_are_raw_row_instances(self):
        rows = read_excel(EXCEL_PATH)
        for row in rows:
            assert isinstance(row, RawRow)

    def test_camillas_count(self):
        rows = read_excel(EXCEL_PATH)
        camillas = [r for r in rows if r.sheet_name == "Camillas"]
        assert len(camillas) == 2

    def test_agujas_count(self):
        rows = read_excel(EXCEL_PATH)
        agujas = [r for r in rows if r.sheet_name == "Agujas"]
        assert len(agujas) == 10
