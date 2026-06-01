"""Logging y generación del reporte final de importación."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from .importer import ImportResult
from .validator import ValidationReport

logger = logging.getLogger(__name__)


def print_validation_report(report: ValidationReport) -> None:
    print("\n--- Validación del Excel ---")
    print(f"  OK (SKU válido):       {len(report.ok)}")
    print(f"  Sin código (S/C):      {len(report.needs_autogen)}")
    print(f"  SKU inválido:          {len(report.invalid_sku)}")
    print(f"  Errores:               {len(report.errors)}")

    if report.needs_autogen:
        print("\n  Productos con SKU auto-generado:")
        for row in report.needs_autogen:
            print(f"    [{row.sheet_name}] {row.codigo!r} -> {row.producto}")

    if report.invalid_sku:
        print("\n  SKUs invalidos (se intentara transformar):")
        for row in report.invalid_sku:
            print(f"    [{row.sheet_name}] {row.codigo!r} -> {row.producto}")

    if report.errors:
        print("\n  Errores de validación:")
        for row, msg in report.errors:
            print(f"    [{row.sheet_name}] {row.codigo!r}: {msg}")


def print_import_result(result: ImportResult, *, dry_run: bool = False) -> None:
    label = "[DRY-RUN] " if dry_run else ""
    print(f"\n--- {label}Resultado de importación ---")
    print(f"  Categorías creadas:          {result.categories_created}")
    print(f"  Categorías ya existentes:    {result.categories_skipped}")
    print(f"  Productos creados:           {result.products_created}")
    print(f"  Productos con precio:        {result.products_with_prices}")
    print(f"  Productos ya existentes:     {result.products_skipped}")

    if result.products_generated_sku:
        print(f"\n  SKUs auto-generados ({len(result.products_generated_sku)}):")
        for sku in result.products_generated_sku:
            print(f"    {sku}")

    if result.products_transformed_sku:
        print(f"\n  SKUs transformados ({len(result.products_transformed_sku)}):")
        for orig, new in result.products_transformed_sku:
            print(f"    {orig!r} -> {new!r}")

    if result.errors:
        print(f"\n  Errores durante importación ({len(result.errors)}):")
        for sku, msg in result.errors:
            print(f"    {sku}: {msg}")


def save_report(
    result: ImportResult,
    *,
    output_dir: str | Path = ".",
    dry_run: bool = False,
) -> Path:
    """Persiste el resultado como JSON y retorna la ruta del archivo."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_dryrun" if dry_run else ""
    path = output_dir / f"import_report{suffix}_{timestamp}.json"

    data = {
        "timestamp": timestamp,
        "dry_run": dry_run,
        "categories_created": result.categories_created,
        "categories_skipped": result.categories_skipped,
        "products_created": result.products_created,
        "products_skipped": result.products_skipped,
        "products_with_prices": result.products_with_prices,
        "products_generated_sku": result.products_generated_sku,
        "products_transformed_sku": result.products_transformed_sku,
        "errors": result.errors,
    }

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Reporte guardado en: %s", path)
    return path
