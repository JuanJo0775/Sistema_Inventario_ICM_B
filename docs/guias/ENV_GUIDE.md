# Guía de Variables de Entorno — Sistema Inventario ICM

## Estructura de archivos

El proyecto usa archivos `.env` segregados por entorno. Cada uno se carga automáticamente según `DJANGO_SETTINGS_MODULE`:

```
Proyecto/
├── .env.development           # Variables reales de desarrollo (ignorado por git)
├── .env.production            # Variables reales de producción (ignorado por git)
├── .env                       # Fallback legacy (ignorado por git)
├── .env.development.example   # Template público de desarrollo (versionado)
├── .env.production.example    # Template público de producción (versionado)
└── .env.example               # Referencia general (versionado)
```

## Cómo funciona el switch

`DJANGO_SETTINGS_MODULE` determina qué `.env` se carga. Es automático según el entry point:

| Entry point | Default DJANGO_SETTINGS_MODULE | .env cargado |
|---|---|---|
| `python manage.py runserver` | `config.settings.development` | `.env.development` |
| `gunicorn config.wsgi` | `config.settings.production` | `.env.production` |
| `uvicorn config.asgi` | `config.settings.production` | `.env.production` |

Para forzar un entorno manualmente:

```bash
# PowerShell
$env:DJANGO_SETTINGS_MODULE="config.settings.production"; python manage.py shell

# CMD
set DJANGO_SETTINGS_MODULE=config.settings.production && python manage.py shell

# Git Bash / Linux
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py shell
```

## Primer arranque (desarrollo local)

```bash
# 1. Copiar la plantilla de desarrollo
cp .env.development.example .env.development

# 2. Ajustar credenciales si es necesario (BD local, email, etc.)
#    Por defecto ya funciona con PostgreSQL local sin cambios.

# 3. Crear la base de datos (una sola vez)
psql -U postgres -c "CREATE DATABASE icm_db;"
psql -U postgres -c "CREATE USER icm_user WITH PASSWORD 'icm_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE icm_db TO icm_user;"

# 4. Migrar y crear usuario inicial
python manage.py migrate
python manage.py create_almacenista

# 5. (Opcional) Cargar datos de prueba
python scripts/seed_db/run.py

# 6. Iniciar servidor
python manage.py runserver
```

## Variables por sección

### Django Core

| Variable | Default dev | Default prod | Descripción |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | `insecure-dev-key-...` | *(requerido)* | Clave para firmar sesiones, CSRF, tokens. **Generar segura en producción.** |
| `DJANGO_DEBUG` | `True` | `False` | `True` muestra trazas de error. `False` obligatorio en producción. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | `api.icm.com.co` | Hosts que Django acepta, separados por coma. |

**Generar secret key para producción:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Base de datos

| Variable | Default dev | Default prod | Descripción |
|---|---|---|---|
| `DB_PROVIDER` | `local` | `neon` | `local` = PostgreSQL directo, `neon` = Neon Tech cloud |

**Cuando DB_PROVIDER=local:**

| Variable | Default | Descripción |
|---|---|---|
| `DB_NAME` | `icm_db` | Nombre de la base de datos |
| `DB_USER` | `icm_user` | Usuario PostgreSQL |
| `DB_PASSWORD` | `icm_password` | Contraseña |
| `DB_HOST` | `localhost` | Host (en Docker: nombre del servicio `db`) |
| `DB_PORT` | `5432` | Puerto |

**Cuando DB_PROVIDER=neon:**

| Variable | Ejemplo | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@ep-xxxx.sa-east-1.aws.neon.tech/db?sslmode=require` | URL completa de conexión a Neon |

### Email (SMTP Gmail)

| Variable | Default | Descripción |
|---|---|---|
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP |
| `EMAIL_PORT` | `587` | Puerto TLS |
| `EMAIL_USE_TLS` | `True` | Usar TLS |
| `EMAIL_HOST_USER` | — | Correo electrónico de la cuenta |
| `EMAIL_HOST_PASSWORD` | — | App password de Google |

> **Importante:** Gmail requiere una *App Password* (no la contraseña normal de la cuenta).
> Generar en: Cuenta Google → Seguridad → Verificación en dos pasos → Contraseñas de aplicación.

El email se usa exclusivamente para el flujo de recuperación de contraseña (`forgot-password`). Se envía en formato HTML con branding de ICM LogiStock.

### JWT

| Variable | Default dev | Default prod | Descripción |
|---|---|---|---|
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `1440` (24 h) | `60` (1 h) | Vida del access token |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `30` | `7` | Vida del refresh token |

En desarrollo los tokens son más largos para no re-loguearse seguido. En producción deben ser cortos por seguridad.

### Aplicación

| Variable | Default dev | Default prod | Descripción |
|---|---|---|---|
| `APP_TIMEZONE` | `America/Bogota` | `America/Bogota` | Zona horaria del negocio |
| `INVOICE_SEQUENCE_PREFIX` | `ICM` | `ICM` | Prefijo de facturas (`ICM-0001`) |
| `FRONTEND_URL` | `http://localhost:5173` | `https://app.icm.com.co` | URL del frontend para emails de recuperación |
| `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES` | `60` | `10` | Minutos de validez del token de reset |

### CORS

| Variable | Default dev | Default prod | Descripción |
|---|---|---|---|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173,http://localhost:8000` | `https://app.icm.com.co` | Orígenes permitidos separados por coma |

En desarrollo `development.py` sobreescribe `CORS_ALLOW_ALL_ORIGINS=True`, lo que permite cualquier origen sin importar esta variable.

### Seed / Usuario inicial

| Variable | Default | Descripción |
|---|---|---|
| `ALMACENISTA_USERNAME` | `almacenista` | Username del usuario inicial |
| `ALMACENISTA_EMAIL` | `almacenista@icm.local` | Email del usuario inicial |
| `ALMACENISTA_PASSWORD` | *(requerido)* | Contraseña. **Cambiar por una segura en producción.** |

## Producción — checklist de configuración

Antes de desplegar, verificar:

1. **`DJANGO_SECRET_KEY`** — Generar clave segura (no usar la de desarrollo)
2. **`DJANGO_DEBUG=False`** — Obligatorio
3. **`DJANGO_ALLOWED_HOSTS`** — Dominio real de producción
4. **Base de datos** — Configurar `DB_PROVIDER` y credenciales correspondientes
5. **Email** — Configurar Gmail con app password
6. **`FRONTEND_URL`** — URL real del frontend
7. **`CORS_ALLOWED_ORIGINS`** — Solo el dominio de producción
8. **`ALMACENISTA_PASSWORD`** — Contraseña segura

```bash
cp .env.production.example .env.production
# Editar .env.production con valores reales
```

## Tests

La suite de tests usa `config/settings/test.py` con `django.core.mail.backends.locmem.EmailBackend` — los emails nunca salen a la red, se capturan en `django.core.mail.outbox`. No se necesita configuración SMTP para correr `pytest`.

## Variables futuras (no implementar aún)

Comentadas en los templates. No descomentar hasta que los módulos existan:

```
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
```
