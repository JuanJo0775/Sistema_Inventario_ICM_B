"""Verificación de conexión Neon y estado del seed para producción."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.development"

import django
django.setup()

from django.db import connection, connections
from django.conf import settings

# -----------------------------------------------------------------------
# 1. Conexión
# -----------------------------------------------------------------------
print("=" * 60)
print("  VERIFICACIÓN NEON — ICM")
print("=" * 60)

try:
    with connection.cursor() as cur:
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.execute("SELECT current_database()")
        db_name = cur.fetchone()[0]
        cur.execute("SELECT inet_server_addr()")
        server_ip = cur.fetchone()[0]
    print(f"\n[OK] CONEXION EXITOSA")
    print(f"  PG version : {version.split(',')[0]}")
    print(f"  Base de datos : {db_name}")
    print(f"  Host (settings): {settings.DATABASES['default'].get('HOST', 'via DATABASE_URL')}")
    print(f"  SSL requerido : {settings.DATABASES['default'].get('OPTIONS', {}).get('sslmode', 'via conn_str')}")
except Exception as e:
    print(f"\n[FAIL] CONEXION FALLIDA: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------
# 2. Estado del seed en Neon
# -----------------------------------------------------------------------
print("\n--- Estado del seed ---")

from apps.catalog.models import Product, Category, Brand
from apps.inventory.models import Location, StockByLocation
from apps.movements.models import Movement
from apps.purchasing.models import PurchaseOrder, Supplier
from apps.authentication.models import User
from apps.alerts.models import Alert
from apps.webhooks.models import WebhookEndpoint
from apps.catalog.models import Lot, ProductPriceHistory

rows = [
    ("Categorias",       Category.objects.count()),
    ("Marcas",           Brand.objects.count()),
    ("Productos",        Product.objects.count()),
    ("Ubicaciones",      Location.objects.count()),
    ("Proveedores",      Supplier.objects.count()),
    ("OC totales",       PurchaseOrder.objects.count()),
    ("Movimientos",      Movement.objects.count()),
    ("Filas stock",      StockByLocation.objects.filter(current_stock__gt=0).count()),
    ("Lotes",            Lot.objects.count()),
    ("Historial precio", ProductPriceHistory.objects.count()),
    ("Alertas",          Alert.objects.count()),
    ("Webhooks",         WebhookEndpoint.objects.count()),
    ("Usuarios",         User.objects.count()),
]

for label, count in rows:
    status = "OK" if count > 0 else "VACIO"
    print(f"  [{status:5s}] {label:20s}: {count}")

# -----------------------------------------------------------------------
# 3. Verificaciones de integridad
# -----------------------------------------------------------------------
print("\n--- Integridad ---")

from apps.catalog.models import ProductSerial
from apps.inventory.models import StorageType, StorageTemplate

serials = ProductSerial.objects.count()
sin_serial = Product.objects.filter(
    category__requires_serial_number=True
).count()
cold_chain = Product.objects.filter(requires_cold_chain=True).count()
exp_products = Product.objects.filter(requires_expiration=True).count()

cuarto_frio = Location.objects.filter(code="cuarto-frio").first()
cf_stock = StockByLocation.objects.filter(
    location=cuarto_frio, current_stock__gt=0
).count() if cuarto_frio else 0

from apps.movements.models import MovementType
mt_counts = {
    row["movement_type"]: row["c"]
    for row in Movement.objects.values("movement_type").annotate(
        c=__import__("django.db.models", fromlist=["Count"]).Count("id")
    )
}

checks = [
    ("Seriales creados",                serials > 0,         str(serials)),
    ("Productos con serial obligatorio", sin_serial > 0,      str(sin_serial)),
    ("Productos con cadena de frio",    cold_chain == 2,     str(cold_chain)),
    ("Productos con vencimiento",       exp_products >= 14,  str(exp_products)),
    ("Stock en Cuarto Frio",            cf_stock >= 2,       str(cf_stock) + " SKUs"),
    ("StorageTypes configurados",       StorageType.objects.count() >= 4, str(StorageType.objects.count())),
    ("Tipo DEVOLUCION existe",          "DEVOLUCION" in mt_counts,       str(mt_counts.get("DEVOLUCION", 0))),
    ("Tipo SALIDA_COMBO existe",        "SALIDA_COMBO" in mt_counts,     str(mt_counts.get("SALIDA_COMBO", 0))),
    ("Tipo SALIDA_DANO existe",         "SALIDA_DANO" in mt_counts,      str(mt_counts.get("SALIDA_DANO", 0))),
]

for label, ok, val in checks:
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label:35s}: {val}")

# -----------------------------------------------------------------------
# 4. Alertas de producción
# -----------------------------------------------------------------------
print("\n--- Alertas de produccion ---")
issues = []

secret = settings.SECRET_KEY
if "insecure" in secret or "change" in secret.lower() or len(secret) < 40:
    issues.append("SECRET_KEY no es segura — cambiar antes de produccion")

if settings.DEBUG:
    issues.append("DEBUG=True — debe ser False en produccion")

allowed = settings.ALLOWED_HOSTS
if set(allowed) <= {"localhost", "127.0.0.1", "0.0.0.0"}:
    issues.append("ALLOWED_HOSTS solo tiene hosts locales — agregar dominio de produccion")

# CORS
cors_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
cors_all = getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False)
if cors_all:
    issues.append("CORS_ALLOW_ALL_ORIGINS=True — restringir en produccion")

if issues:
    for issue in issues:
        print(f"  [WARN] {issue}")
else:
    print("  Ninguna alerta critica detectada")

print("\n" + "=" * 60)
print("  Verificacion completada")
print("=" * 60)
