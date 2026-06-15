# Guía de `seed_db`

## Propósito

Explica cómo poblar la base de datos ICM desde cero: migraciones, usuario inicial y seed completo.

El seed carga **214 productos en 11 categorías**, stock en 4 ubicaciones (bodega, vitrina, bodega-norte, vitrina-2) más cuarto frío para cadena de frío, movimientos de todos los tipos, lotes, historial de precios, facturas, alertas y webhooks.

---

## Requisitos previos

- Entorno virtual activado (`.venv`)
- Variables de entorno correctas en `.env` (ver [ENV_GUIDE.md](ENV_GUIDE.md))
- Base de datos accesible (`DB_PROVIDER=local` o `DB_PROVIDER=neon`)

---

## Flujo completo (primera vez)

```powershell
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1          # PowerShell
# source .venv/bin/activate           # bash/zsh (Linux/Mac)

# 2. Aplicar migraciones
python manage.py migrate

# 3. Crear usuario almacenista inicial
python manage.py create_almacenista

# 4. Seed completo
python scripts/seed_db/run.py
```

El paso 4 tarda ~1 min en local y ~5–10 min contra Neon (latencia de red).

---

## Rehacerlo desde cero

```powershell
# Limpia todos los datos del seed (conserva almacenista y ubicaciones base)
python scripts/seed_db/clean.py --confirm

# Vuelve a sembrar
python scripts/seed_db/run.py
```

> `clean.py` **no borra** el usuario almacenista ni las ubicaciones `bodega` y `vitrina` creadas por las migraciones.

---

## Comandos de referencia

| Comando | Qué hace |
|---------|----------|
| `python manage.py migrate` | Crea/actualiza todas las tablas en la BD |
| `python manage.py create_almacenista` | Crea el usuario `almacenista` (idempotente) |
| `python scripts/seed_db/run.py` | Seed completo fases 1–23 (idempotente) |
| `python scripts/seed_db/run.py --force` | Regenera movimientos aunque ya existan |
| `python scripts/seed_db/clean.py` | Limpia datos del seed (pide confirmación) |
| `python scripts/seed_db/clean.py --confirm` | Limpia sin prompt interactivo |

---

## Qué crea el seed (fases 1–23)

| Fase | Contenido |
|------|-----------|
| 1 | Usuarios: `auxiliar_despacho_1`, `auxiliar_despacho_2`, `administrador_icm` |
| 2 | Ubicaciones adicionales: `bodega-norte`, `vitrina-2`, `cuarto-frio` |
| 3 | 11 categorías (Electroterapia, Masajeadores, Bandas, Cintas, Pelotas, Agujas, Accesorios, Camillas, Pedales, Suelo Pélvico, Terapias de Mano) |
| 4 | 14 marcas |
| 5 | 214 productos con precios, IVA, puntos de reorden y flags de trazabilidad |
| 5b | Corrección de flags: `requires_expiration`, `requires_cold_chain` por producto |
| 6 | 5 proveedores |
| 7–9 | 8 órdenes de compra confirmadas con recepciones y stock inicial |
| 10 | Traslados entre ubicaciones (incluyendo cuarto frío para cadena de frío) |
| 11–12 | Ventas al por mayor y menor |
| 13 | Ajustes positivos y negativos |
| 14 | Combos de productos |
| 15 | StorageTypes y StorageTemplates → asignados a ubicaciones |
| 16 | UserSchedules (horarios auxiliares) |
| 17 | Lotes con fechas de vencimiento variadas (activa alertas EXPIRATION_30/60) |
| 18 | Movimientos faltantes: DEVOLUCION, SALIDA_DANO, SALIDA_VENCIMIENTO, SALIDA_COMBO |
| 19 | OC en estado borrador y cancelada |
| 20 | Actualizaciones de precio → `ProductPriceHistory` |
| 21 | 2 facturas comerciales |
| 22 | `scan_alerts` → genera alertas de stock cero y vencimiento |
| 23 | WebhookEndpoint de ejemplo |

---

## Configuración de BD

### Local (PostgreSQL)

```env
DB_PROVIDER=local
DB_NAME=icm_db
DB_USER=icm_user
DB_PASSWORD=icm_password
DB_HOST=localhost
DB_PORT=5432
```

### Neon (cloud)

```env
DB_PROVIDER=neon
DATABASE_URL=postgresql://usuario:clave@host/neondb?sslmode=require
```

---

## Troubleshooting

### `no such table: authentication_user` (SQLite en vez de Neon/PostgreSQL)

**Causa:** PyCharm inyecta `DJANGO_SETTINGS_MODULE=config.settings.test` en la terminal al leer `pytest.ini`. El script detecta la variable ya puesta y usa SQLite en memoria.

**Solución:** Los scripts `run.py` y `clean.py` ya están corregidos para forzar siempre `config.settings.development`. Si el problema persiste, verifica que tienes la versión actualizada de los scripts.

Como alternativa temporal en la terminal:
```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.development"
python scripts/seed_db/run.py
```

---

### `relation "django_session" does not exist`

**Causa:** La base de datos está vacía — no se han aplicado migraciones.

**Solución:**
```powershell
python manage.py migrate
python manage.py create_almacenista
python scripts/seed_db/run.py
```

---

### `Usuario 'almacenista' no encontrado`

**Causa:** No se ejecutó `create_almacenista` antes del seed.

**Solución:**
```powershell
python manage.py create_almacenista
python scripts/seed_db/run.py
```

---

### `Inconsistencia en fecha de vencimiento del lote`

**Causa:** Correr `run.py --force` sobre una BD que ya tiene lotes de una recepción previa. Los lotes no se pueden modificar.

**Solución:** Limpiar primero con `clean.py --confirm` y luego `run.py`.

---

### El seed no cambia nada

**Causa:** El flujo es idempotente — si los datos ya existen, no los duplica.

**Solución:** Para regenerar movimientos usa `--force`. Para empezar desde cero usa `clean.py --confirm`.

---

## Dónde vive la lógica

| Archivo | Propósito |
|---------|-----------|
| [scripts/seed_db/config.py](../../scripts/seed_db/config.py) | Datos estáticos del seed (productos, categorías, etc.) |
| [scripts/seed_db/seeder.py](../../scripts/seed_db/seeder.py) | Lógica principal — fases 1–23 |
| [scripts/seed_db/run.py](../../scripts/seed_db/run.py) | Punto de entrada del seed |
| [scripts/seed_db/clean.py](../../scripts/seed_db/clean.py) | Limpieza de la BD |
| [apps/authentication/management/commands/create_almacenista.py](../../apps/authentication/management/commands/create_almacenista.py) | Comando `create_almacenista` |

## Referencias

- [scripts/README_SCRIPTS.md](../../scripts/README_SCRIPTS.md)
- [docs/README_ARQUITECTURA.md](../README_ARQUITECTURA.md)
- [docs/guias/ENV_GUIDE.md](ENV_GUIDE.md)
