# Docker — Sistema Inventario ICM

## Estructura de archivos

```
.dockerignore
docker/
  Dockerfile          # Multi-stage: python-deps, dev, test, production
  entrypoint.sh       # Punto de entrada inteligente
docker-compose.yml       # Desarrollo (web + PostgreSQL)
docker-compose.test.yml  # Tests (SQLite, sin BD externa)
docker-compose.prod.yml  # Producción (Gunicorn + PostgreSQL)
```

## Stack de contenedores

| Servicio | Imagen | Propósito |
|----------|--------|-----------|
| `db` | postgres:15 / postgres:15-alpine | Base de datos PostgreSQL |
| `web` | icm-web (build local) | Django dev (runserver) |
| `test` | icm-web (target: test) | Ejecución de pytest |
| `production` | icm-web (target: production) | Gunicorn WSGI |

## Prerrequisitos

- Docker Engine 24+ y Docker Compose v2

## Uso rápido

### 1. Desarrollo local

```bash
# Construir e iniciar servicios (web + db)
docker compose up --build

# La API estará disponible en: http://localhost:8000
# Swagger UI: http://localhost:8000/api/docs/
```

Variables de entorno desde `.env` (DB_HOST se sobreescribe automáticamente a `db` dentro del contenedor).

```bash
# Ver logs
docker compose logs -f web

# Ejecutar comandos dentro del contenedor web
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py create_almacenista
docker compose exec web python scripts/seed_db/run.py

# Detener servicios
docker compose down
```

### 2. Ejecutar tests

Los tests usan SQLite en memoria (`config/settings.test`), **no requieren PostgreSQL**.

```bash
# Opción A — Test service dedicado (recomendado)
docker compose -f docker-compose.test.yml build
docker compose -f docker-compose.test.yml run --rm test

# Opción B — Dentro del contenedor web en ejecución
docker compose exec web pytest

# Opción C — Con argumentos personalizados
docker compose -f docker-compose.test.yml run --rm test pytest -v -k "test_serial"
docker compose -f docker-compose.test.yml run --rm test pytest --cov=apps
docker compose -f docker-compose.test.yml run --rm test pytest -n auto
```

### 3. Producción

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## Modo test — explicación

El entrypoint detecta el modo test mediante la variable `SKIP_DB_WAIT=1`:

```
Sin SKIP_DB_WAIT → espera PostgreSQL, ejecuta migrate + collectstatic, arranca comando
Con SKIP_DB_WAIT=1 → salta todo, ejecuta el comando directamente (pytest)
```

Esto permite que los tests corran sin PostgreSQL, usando `config/settings.test.py` que configura SQLite en memoria.

## Comandos útiles

```bash
# Reconstruir imágenes sin cache
docker compose build --no-cache
docker compose -f docker-compose.test.yml build --no-cache

# Verificar salud de la BD
docker compose exec db pg_isready -U icm_user

# Acceder a la consola de Django
docker compose exec web python manage.py shell

# Ver contenedores activos
docker compose ps

# Limpiar volúmenes (pierde datos locales)
docker compose down -v
```

## Personalización

Las variables del `.env` controlan nombres de BD, usuarios, puertos mapeados, etc.

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DB_PORT_MAP` | `5432` | Puerto PostgreSQL expuesto en host |
| `WEB_PORT_MAP` | `8000` | Puerto web expuesto en host |
| `DB_NAME` | `icm_db` | Nombre de la base de datos |
| `DB_USER` | `icm_user` | Usuario de la base de datos |
| `DB_PASSWORD` | `icm_password` | Contraseña de la base de datos |

## Notas técnicas

- El multi-stage build separa dependencias: base → dev/test agregan `development.txt`, production agrega solo `production.txt` + gunicorn.
- En desarrollo se monta `.:/app` como bind mount para hot-reload de código.
- En tests el mismo montaje permite probar cambios sin reconstruir.
- `psycopg2-binary` se instala desde `requirements/base.txt`; no requiere `libpq-dev` en runtime, pero se necesita `gcc` para compilar `WeasyPrint` y otras dependencias.
