# Guía: Importación del Catálogo Inicial desde Excel

## Descripción

Este proceso importa el catálogo de productos del cliente desde el archivo `Clasificacion_Productos.xlsx` hacia la base de datos del sistema. Crea automáticamente categorías y productos, respeta las validaciones del dominio (formato SKU, auditoría), y es **idempotente**: puede ejecutarse múltiples veces sin duplicar datos.

---

## Prerrequisitos

- Python y entorno virtual activado
- Django configurado y base de datos con migraciones aplicadas (`python manage.py migrate`)
- Archivo `.env` con las variables listadas abajo
- Archivo Excel en la ruta configurada

---

## Variables de entorno requeridas

Agrega estas variables a tu archivo `.env` (ver `.env.example` como referencia):

```env
# Ruta al Excel (relativa a la raíz del proyecto, o absoluta)
IMPORT_EXCEL_PATH=docs/guias/Clasificacion_Productos.xlsx

# Ejecutar en modo lectura sin escribir en BD (True/False)
IMPORT_DRY_RUN=False

# Credenciales del usuario almacenista inicial
ALMACENISTA_USERNAME=almacenista
ALMACENISTA_EMAIL=almacenista@icm.local
ALMACENISTA_PASSWORD=contraseña-segura-aqui
```

---

## Orden de ejecución

### 1. Crear el usuario almacenista

```bash
python manage.py create_almacenista
```

- Crea el usuario con rol `almacenista` usando las variables del `.env`
- Si el usuario ya existe, muestra un aviso y no hace nada (idempotente)
- Registra el evento en el `AuditLog`

### 2. Verificar con dry-run

```bash
python manage.py import_catalog --dry-run
```

- Lee el Excel, valida y transforma los datos
- Muestra cuántas categorías y productos se crearían
- **No escribe nada en la base de datos**
- Genera un reporte JSON con sufijo `_dryrun`

### 3. Ejecutar la importación real

```bash
python manage.py import_catalog
```

- Crea las 11 categorías y todos los productos
- Omite productos cuyo SKU ya existe en BD
- Genera el reporte JSON en la raíz del proyecto

### 4. Verificar integridad post-importación

```bash
python manage.py verify_stock_integrity
```

Confirma que no hay discrepancias de stock (debe reportar cero).

---

## Estructura del Excel esperada

| Elemento | Descripción |
|---|---|
| Hoja "Resumen" | Se omite automáticamente |
| Resto de hojas | Una hoja por categoría (ej. "Camillas", "Agujas") |
| Fila 0 de cada hoja | Título de la categoría en mayúsculas (se omite) |
| Fila 1 de cada hoja | Encabezados: `Código`, `#`, `Producto` (se omite) |
| Filas de datos | Código SKU, número secuencial, nombre del producto |
| Última fila de cada hoja | "Total: X productos" (se omite) |

**Formato de SKU válido:** `^[A-Za-z]{1,4}-\d{1,4}$`
- Ejemplos válidos: `CM-01`, `AGJ-001`, `ABCD-1234`, `T-01`
- Ejemplos inválidos: `MPC-01A` (sufijo letra), `S/C` (sin código)

---

## Manejo de casos especiales

### Productos sin código (S/C)

Los productos con código "S/C" reciben un SKU auto-generado con la regla:
- Prefijo: primeras 2 letras del primer word del nombre del producto (uppercase)
- Número: el valor de la columna `#` con zero-padding a 4 dígitos

Ejemplos del Excel actual:
- "Flexbar Amarillo- ICMTHERAPY" (fila #32) → `FL-0032`
- "Flexbar Azul- ICMTHERAPY" (fila #33) → `FL-0033`

### SKUs con sufijo letra (ej: MPC-01A)

Se transforma moviendo el sufijo letra al final del prefijo:
- `MPC-01A` → `MPCA-01`
- `MPC-02A` → `MPCA-02`
- `EC-01b` → `ECB-01`

Todos los SKUs transformados se registran en el reporte final.

---

## Opciones del comando import_catalog

```
python manage.py import_catalog [--excel-path PATH] [--dry-run] [--actor-username USERNAME]
```

| Opción | Descripción |
|---|---|
| `--excel-path PATH` | Sobreescribe `IMPORT_EXCEL_PATH` del .env |
| `--dry-run` | Ejecuta sin escribir en BD (sobreescribe `IMPORT_DRY_RUN`) |
| `--actor-username USERNAME` | Usuario almacenista actor de la importación |

---

## Archivos generados

Cada ejecución genera un archivo JSON en la raíz del proyecto:

```
import_report_20260531_143022.json          # ejecución real
import_report_dryrun_20260531_143000.json   # dry-run
```

Contenido del reporte:
```json
{
  "timestamp": "20260531_143022",
  "dry_run": false,
  "categories_created": 11,
  "categories_skipped": 0,
  "products_created": 215,
  "products_skipped": 0,
  "products_generated_sku": ["FL-0032", "FL-0033"],
  "products_transformed_sku": [
    ["MPC-01A", "MPCA-01"],
    ["MPC-02A", "MPCA-02"],
    ["EC-01b", "ECB-01"]
  ],
  "errors": []
}
```

---

## Cómo agregar productos en el futuro

### Opción A: Desde el sistema (recomendada)

Usar la API REST del catálogo:
```
POST /api/v1/products/
Authorization: Bearer <token-almacenista>

{
  "sku": "NUEVO-01",
  "name": "Nombre del producto",
  "category_id": "<uuid-de-la-categoria>"
}
```

### Opción B: Re-ejecutar el import con el Excel actualizado

1. Agregar el nuevo producto al Excel con un SKU válido
2. Ejecutar `python manage.py import_catalog`
3. El proceso omite los productos ya existentes y solo crea los nuevos

---

## Reutilización en otros entornos

El proceso no tiene rutas ni IDs hardcodeados. Para ejecutarlo en otra máquina:

1. Copiar el archivo `.env.example` → `.env`
2. Completar todas las variables (especialmente `DB_*` y `ALMACENISTA_PASSWORD`)
3. Colocar el Excel en la ruta configurada en `IMPORT_EXCEL_PATH`
4. Ejecutar en orden: `create_almacenista` → `import_catalog --dry-run` → `import_catalog`

---

## Arquitectura del módulo de importación

```
scripts/import_catalog/
├── config.py      ← Variables centralizadas (decouple)
├── reader.py      ← Lee el Excel con openpyxl → List[RawRow]
├── validator.py   ← Clasifica filas por estado de SKU → ValidationReport
├── transformer.py ← Normaliza y transforma → List[ImportRow]
├── importer.py    ← Inserta en BD via servicios del catálogo
└── reporter.py    ← Imprime resumen y guarda JSON
```

El pipeline completo es: `reader → validator → transformer → importer → reporter`

Los servicios del catálogo (`apps/catalog/services.py`) se reutilizan para garantizar validaciones de dominio y registro automático en `AuditLog`.

---

## Tests

```bash
# Todos los tests de importación
pytest tests/test_import/ -v

# Solo tests que no requieren el Excel real
pytest tests/test_import/ -v -k "not TestReadExcel"

# Tests de integración (requieren BD)
pytest tests/test_import/test_importer.py -v
```

---

## Troubleshooting

| Error | Causa probable | Solución |
|---|---|---|
| `Usuario 'almacenista' no encontrado` | No se ejecutó `create_almacenista` | Ejecutar `python manage.py create_almacenista` |
| `ALMACENISTA_PASSWORD está vacía` | Variable no configurada | Agregar `ALMACENISTA_PASSWORD` al `.env` |
| `FileNotFoundError: ...xlsx` | Excel no encontrado en la ruta | Verificar `IMPORT_EXCEL_PATH` en `.env` |
| `SKU duplicado en BD` | Producto ya existente | Normal en re-ejecución, se registra como `skipped` |
| `Formato SKU inválido` | SKU del Excel no cumple el patrón | Revisar el reporte; el transformer debería haberlo manejado |
| `El email ya está registrado` | Email del almacenista en uso | Cambiar `ALMACENISTA_EMAIL` en `.env` |

---

## Resumen de la importación inicial

| Dato | Valor |
|---|---|
| Fuente | `Clasificacion_Productos.xlsx` |
| Categorías | 11 (Camillas, Agujas, Terapias de Mano, Suelo Pélvico, Electroterapia, Pelotas, Bandas, Masajeadores, Cintas, Pedales, Accesorios) |
| Total productos | 215 |
| SKUs auto-generados | 2 (`FL-0032`, `FL-0033`) por productos Flexbar sin código |
| SKUs transformados | 3 (`MPC-01A→MPCA-01`, `MPC-02A→MPCA-02`, `EC-01b→ECB-01`) |
| Stock inicial | Ninguno (solo catálogo) |
| Subcategorías | No aplica (no presentes en el Excel) |
