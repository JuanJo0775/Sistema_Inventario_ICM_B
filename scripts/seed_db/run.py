"""
Seed unificado ICM: catalogo completo + movimientos de prueba.

Incluye: categorias, marcas, productos con precios,
proveedores, ubicaciones, stock via OC, traslados, ventas, ajustes y combos.

Prerequisito:
    python manage.py create_almacenista

Uso:
    python scripts/seed_db/run.py
    python scripts/seed_db/run.py --force
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.development"

import django  # noqa: E402

django.setup()

from scripts.seed_db.seeder import Seeder, SeedResult  # noqa: E402


def _print_summary(result: SeedResult) -> None:
    print("\n--- Resumen ---")
    print(
        f"  Categorias:          {result.categories_created} creadas, {result.categories_skipped} existentes"
    )
    print(f"  Marcas:              {result.subcategories_created} creadas")
    print(
        f"  Productos:           {result.products_created} creados, {result.products_skipped} existentes"
    )
    print(f"  OC totales:          {result.purchase_orders}")
    print(f"  Movimientos totales: {result.movements}")
    print(f"  Filas de stock:      {result.stock_rows}")
    for tipo, n in result.movements_by_type.items():
        print(f"    {tipo:20s}: {n}")

    if result.stock_by_location:
        print("\n  Stock por ubicacion:")
        for nombre, data in result.stock_by_location.items():
            print(
                f"    {nombre:25s}: {data['activos']} SKUs con stock"
                f" | {data['agotados']} agotados | {data['total_units']} uds totales"
            )

    if not result.skipped_movement_phase:
        print("\n  Escenarios disponibles:")
        scenarios = [
            "Catalogo completo: categorias, marcas, productos con precios",
            "Productos con reorder_point configurado",
            "Stock alto en bodega principal",
            "Stock bajo en vitrina tras ventas",
            "Productos agotados en vitrina",
            "Stock en 4 ubicaciones (bodega, vitrina, bodega-norte, vitrina-2)",
            "Ventas al por mayor con datos de cliente completos",
            "Ajustes positivos y negativos con justificacion",
            "Combos de productos activos",
            "5 proveedores con OC confirmadas",
            "5 clientes de ventas mayor",
        ]
        for s in scenarios:
            print(f"    [OK] {s}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed unificado ICM: catalogo completo + movimientos de prueba."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenera movimientos aunque ya existan.",
    )
    args = parser.parse_args()

    seeder = Seeder(write_fn=print, warn_fn=lambda msg: print(f"  [!] {msg}"))
    try:
        result = seeder.run(force=args.force)
        _print_summary(result)
        sys.exit(0)
    except RuntimeError as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
