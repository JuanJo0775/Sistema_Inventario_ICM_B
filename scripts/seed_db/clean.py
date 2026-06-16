"""
Limpia la base de datos ICM eliminando todos los datos generados por el seed.

Conserva:
  - Usuario almacenista (role=almacenista) y superusuarios Django.
  - Ubicaciones base creadas por migraciones (bodega, vitrina).
  - Tablas de framework: contenttypes, auth permissions/groups, migrations.

Elimina (en orden FK-safe):
  - Sesiones JWT y de Django
  - Facturas, movimientos, alertas
  - Ordenes de compra, recepciones
  - Combos, productos, lotes, historial de precios, stock
  - Marcas y categorias
  - Proveedores
  - Ubicaciones adicionales (bodega-norte, vitrina-2, etc.)
  - Usuarios adicionales (auxiliar_despacho, administrador)
  - Webhooks, audit logs, logs de admin

Uso:
    python scripts/seed_db/clean.py
    python scripts/seed_db/clean.py --confirm   # sin prompt interactivo
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

_FORCED_PROD = "--production" in sys.argv
if _FORCED_PROD:
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

_settings = os.environ["DJANGO_SETTINGS_MODULE"]
if "production" in _settings and not _FORCED_PROD:
    print(
        "[ERROR] clean.py no debe ejecutarse con settings de producción.",
        file=sys.stderr,
    )
    sys.exit(1)

import django  # noqa: E402

django.setup()


# Codigos de ubicaciones que las migraciones crean (no se tocan)
_BASE_LOCATION_CODES = {"bodega", "vitrina"}


def _confirm() -> bool:
    print("\n  ADVERTENCIA: Esta operacion elimina TODOS los datos del seed.")
    print(
        "  Se conservan: almacenista, superusuarios y ubicaciones base (bodega/vitrina)."
    )
    answer = input("\n  Escriba 'SI' para continuar: ").strip()
    return answer == "SI"


def _deleted(label: str, result: tuple) -> None:
    total = result[0] if isinstance(result, tuple) else result
    print(f"  - {label}: {total} registros eliminados")


def clean() -> None:
    from django.contrib.admin.models import LogEntry
    from django.contrib.auth import get_user_model
    from django.contrib.sessions.models import Session

    from apps.alerts.models import Alert
    from apps.audit.models import AuditLog, AuditLogArchive
    from apps.catalog.models import (
        Brand,
        Category,
        ComboItem,
        Lot,
        Product,
        ProductCombo,
        ProductPriceHistory,
        ProductSerial,
    )
    from apps.inventory.models import (
        Location,
        StockByLocation,
        StorageTemplate,
        StorageType,
    )
    from apps.movements.models import Invoice, InvoiceCounter, Movement
    from apps.purchasing.models import (
        PurchaseOrder,
        PurchaseOrderCounter,
        PurchaseOrderItem,
        Reception,
        ReceptionItem,
        Supplier,
    )
    from apps.webhooks.models import WebhookDelivery, WebhookEndpoint

    User = get_user_model()

    print("\n--- Limpiando sesiones y tokens ---")
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        _deleted("BlacklistedToken", BlacklistedToken.objects.all().delete())
        _deleted("OutstandingToken", OutstandingToken.objects.all().delete())
    except Exception:
        pass
    _deleted("Session Django", Session.objects.all().delete())

    print("\n--- Limpiando facturas ---")
    _deleted("Invoice", Invoice.objects.all().delete())
    _deleted("InvoiceCounter", InvoiceCounter.objects.all().delete())

    print("\n--- Limpiando ordenes de compra ---")
    # ReceptionItem referencia Movement con PROTECT: va primero
    _deleted("ReceptionItem", ReceptionItem.objects.all().delete())
    _deleted("Reception", Reception.objects.all().delete())
    _deleted("PurchaseOrderItem", PurchaseOrderItem.objects.all().delete())
    _deleted("PurchaseOrder", PurchaseOrder.objects.all().delete())
    _deleted("PurchaseOrderCounter", PurchaseOrderCounter.objects.all().delete())

    print("\n--- Limpiando movimientos ---")
    _deleted("Movement", Movement.objects.all().delete())

    print("\n--- Limpiando alertas ---")
    _deleted("Alert", Alert.objects.all().delete())

    print("\n--- Limpiando catalogo ---")
    _deleted("ComboItem", ComboItem.objects.all().delete())
    _deleted("ProductCombo", ProductCombo.objects.all().delete())
    _deleted("ProductPriceHistory", ProductPriceHistory.objects.all().delete())
    _deleted("Lot", Lot.objects.all().delete())
    _deleted("StockByLocation", StockByLocation.objects.all().delete())
    _deleted("ProductSerial", ProductSerial.objects.all().delete())
    _deleted("Product", Product.objects.all().delete())
    _deleted("Brand", Brand.objects.all().delete())
    _deleted("Category", Category.objects.all().delete())
    _deleted("Supplier", Supplier.objects.all().delete())

    print("\n--- Limpiando ubicaciones adicionales ---")
    extra_locs = Location.objects.exclude(code__in=_BASE_LOCATION_CODES)
    _deleted("Location adicional", extra_locs.delete())

    print("\n--- Limpiando tipos de almacenamiento ---")
    _deleted("StorageTemplate", StorageTemplate.objects.all().delete())
    # Desasignar tipo/plantilla en ubicaciones base para poder borrar StorageType
    Location.objects.filter(code__in=_BASE_LOCATION_CODES).update(
        storage_type=None, storage_template=None
    )
    _deleted("StorageType", StorageType.objects.all().delete())

    print("\n--- Limpiando usuarios adicionales ---")
    extra_users = User.objects.filter(role__in=["auxiliar_despacho", "administrador"])
    _deleted("User adicional", extra_users.delete())

    print("\n--- Limpiando webhooks y auditoria ---")
    _deleted("WebhookDelivery", WebhookDelivery.objects.all().delete())
    _deleted("WebhookEndpoint", WebhookEndpoint.objects.all().delete())
    _deleted("AuditLogArchive", AuditLogArchive.objects.all().delete())
    _deleted("AuditLog", AuditLog.objects.all().delete())
    _deleted("LogEntry (admin)", LogEntry.objects.all().delete())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Limpia la base de datos ICM (datos del seed)."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Omite el prompt interactivo y ejecuta directamente.",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Ejecuta clean contra base de datos de producción (Neon).",
    )
    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("  CLEAN DB ICM")
    print("=" * 50)

    if not args.confirm and not _confirm():
        print("\n  Operacion cancelada.")
        sys.exit(0)

    try:
        clean()
        print("\n" + "=" * 50)
        print("  Base de datos limpiada correctamente.")
        print("  Siguiente paso: python scripts/seed_db/run.py")
        print("=" * 50)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
