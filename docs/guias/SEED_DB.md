# Guía de `seed_db`

## Propósito

Esta guía explica cómo usar el seed unificado del proyecto ICM.

La carga inicial se hace con `scripts/seed_db/run.py` y la limpieza previa opcional con `scripts/seed_db/clean.py`.

## En qué se basa

`seed_db` toma como base el catálogo histórico de `Clasificacion_Productos.xlsx`, pero los datos que se cargan al sistema ya están embebidos en `scripts/seed_db/config.py`.

Eso significa:

- el Excel sirvió como fuente de verdad para construir el catálogo inicial
- el seed no necesita leer ese Excel en cada ejecución
- el comportamiento es idempotente y repetible

## Qué carga

El seed crea y/o reutiliza:

- categorías
- subcategorías / marcas
- productos con precios, IVA y puntos de reorden
- proveedores
- clientes
- ubicaciones adicionales
- usuarios de apoyo
- stock inicial y movimientos de prueba

## Variables de entorno

Para ejecutar `seed_db` solo necesitas las credenciales del usuario almacenista:

```env
ALMACENISTA_USERNAME=almacenista
ALMACENISTA_EMAIL=almacenista@icm.local
ALMACENISTA_PASSWORD=una-clave-segura
```

No se usan `IMPORT_EXCEL_PATH` ni `IMPORT_DRY_RUN` en el flujo actual.

## Comandos principales

### 1. Crear el usuario inicial

```bash
python manage.py create_almacenista
```

Este comando:

- crea el usuario `almacenista`
- es idempotente
- requiere `ALMACENISTA_PASSWORD`

### 2. Limpiar la base de datos del seed

```bash
python scripts/seed_db/clean.py
```

O sin confirmación interactiva:

```bash
python scripts/seed_db/clean.py --confirm
```

Este comando:

- elimina los datos generados por el seed
- conserva el usuario almacenista
- conserva las ubicaciones base `bodega` y `vitrina`
- deja la base lista para volver a sembrar desde cero

### 3. Ejecutar el seed completo

```bash
python scripts/seed_db/run.py
```

Este comando:

- carga el catálogo inicial
- crea el stock y los movimientos de prueba
- reutiliza datos existentes cuando ya están cargados

### 4. Regenerar movimientos

```bash
python scripts/seed_db/run.py --force
```

Úsalo cuando necesites reconstruir los escenarios de movimientos aunque ya existan registros previos.

## Flujo recomendado

### Primera ejecución

```bash
python manage.py migrate
python manage.py create_almacenista
python scripts/seed_db/run.py
```

### Rehacer todo desde cero

```bash
python scripts/seed_db/clean.py --confirm
python scripts/seed_db/run.py
```

## Dónde vive la lógica

- [`scripts/seed_db/config.py`](../../scripts/seed_db/config.py): datos estáticos del seed
- [`scripts/seed_db/seeder.py`](../../scripts/seed_db/seeder.py): lógica principal del seed
- [`scripts/seed_db/run.py`](../../scripts/seed_db/run.py): ejecución del seed
- [`scripts/seed_db/clean.py`](../../scripts/seed_db/clean.py): limpieza de base de datos
- [`apps/authentication/management/commands/create_almacenista.py`](../../apps/authentication/management/commands/create_almacenista.py): usuario inicial

## Troubleshooting

| Error | Causa probable | Solución |
|---|---|---|
| `Usuario 'almacenista' no encontrado` | No se ejecutó `create_almacenista` | Ejecutar `python manage.py create_almacenista` |
| `ALMACENISTA_PASSWORD está vacía` | La variable no está configurada | Definir `ALMACENISTA_PASSWORD` en `.env` |
| El seed no cambia nada | Ya existe la data y el flujo es idempotente | Ejecutar con `--force` o limpiar antes con `clean.py` |
| Quiero volver a un entorno limpio | Quedan datos previos del seed | Ejecutar `python scripts/seed_db/clean.py --confirm` |

## Referencias

- [scripts/README_SCRIPTS.md](../../scripts/README_SCRIPTS.md)
- [docs/README_ARQUITECTURA.md](../README_ARQUITECTURA.md)
