# Guía de Variables de Entorno — Sistema Inventario ICM

Esta guía explica cada variable del archivo `.env.example` y cómo configurarlas para desarrollo local, staging y producción.

## Cómo empezar

```bash
# Copiar la plantilla al archivo real
copy .env.example .env      # Windows
cp .env.example .env        # macOS/Linux
```

El archivo `.env` **nunca** se sube al repositorio (está en `.gitignore`). El archivo `.env.example` sí — es la plantilla pública sin secretos reales.

---

## 1. Django Core

| Variable | Default | Descripción |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(inseguro)* | Clave criptográfica para firmar sesiones, CSRF y tokens. **Cambiar obligatoriamente en producción.** |
| `DJANGO_DEBUG` | `True` (development) / `False` (base) | `True` en desarrollo muestra trazas de error completas. `False` en producción (obligatorio). El default en `base.py` es `False`; `development.py` lo sobreescribe a `True`. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts que el servidor acepta. En producción: el dominio real, ej. `tuapp.com,www.tuapp.com`. El default en `base.py` es `localhost,127.0.0.1`; `development.py` usa `*`. |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | Módulo de settings a cargar. Opciones: `development`, `test`, `production`. |

**Producción:**
```
DJANGO_SECRET_KEY=<genera con: python -c "import secrets; print(secrets.token_urlsafe(50))">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tuapp.com,www.tuapp.com
DJANGO_SETTINGS_MODULE=config.settings.production
```

---

## 2. Base de datos (PostgreSQL)

| Variable | Default local | Descripción |
|---|---|---|
| `DB_NAME` | `icm_db` | Nombre de la base de datos |
| `DB_USER` | `icm_user` | Usuario de PostgreSQL |
| `DB_PASSWORD` | `icm_password` | Contraseña del usuario |
| `DB_HOST` | `localhost` | Host de PostgreSQL. En Docker: nombre del servicio, ej. `db` |
| `DB_PORT` | `5432` | Puerto de PostgreSQL |

**Crear la BD local (una sola vez):**
```sql
CREATE DATABASE icm_db;
CREATE USER icm_user WITH PASSWORD 'icm_password';
GRANT ALL PRIVILEGES ON DATABASE icm_db TO icm_user;
```

---

## 3. JWT (tokens de acceso)

| Variable | Default | Descripción |
|---|---|---|
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | Vida del access token en minutos. En dev se sobreescribe a 24 h. |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Vida del refresh token en días. En dev se sobreescribe a 30 días. |

En producción usa valores más cortos para el access token (15–30 min) y activa la rotación de refresh tokens.

---

## 4. Aplicación

| Variable | Default | Descripción |
|---|---|---|
| `APP_TIMEZONE` | `America/Bogota` | Zona horaria del negocio. Usada en restricciones horarias del `auxiliar_despacho`. |
| `INVOICE_SEQUENCE_PREFIX` | `ICM` | Prefijo de numeración de facturas (`ICM-0001`, `ICM-0002`, …). |

---

## 5. Usuario inicial (seed)

Estas variables las usa el comando `python manage.py create_almacenista` para crear el primer usuario del sistema.

| Variable | Default | Descripción |
|---|---|---|
| `ALMACENISTA_USERNAME` | `almacenista` | Username del usuario inicial |
| `ALMACENISTA_EMAIL` | `almacenista@icm.local` | Email del usuario inicial |
| `ALMACENISTA_PASSWORD` | — | **Obligatorio.** Contraseña segura. Vacío = el comando falla con error explicativo. |

**Flujo de primer arranque:**
```bash
# 1. Configurar .env con ALMACENISTA_PASSWORD
# 2. Aplicar migraciones
python manage.py migrate
# 3. Crear el almacenista inicial
python manage.py create_almacenista
# 4. (Opcional) Cargar datos de prueba
python scripts/seed_db/run.py
```

---

## 6. Email (Mailtrap Sandbox / SMTP)

El sistema envía emails en el flujo de recuperación de contraseña (`forgot-password`).

| Variable | Desarrollo | Producción |
|---|---|---|
| `EMAIL_HOST` | `sandbox.smtp.mailtrap.io` | `smtp.gmail.com`, `smtp.mailgun.org`, etc. |
| `EMAIL_HOST_USER` | *(credencial Mailtrap)* | Cuenta del proveedor real |
| `EMAIL_HOST_PASSWORD` | *(credencial Mailtrap)* | Contraseña / API key del proveedor |
| `EMAIL_PORT` | `2525` | `587` (TLS) o `465` (SSL) en la mayoría de proveedores |
| `EMAIL_USE_TLS` | `True` | `True` para TLS (puerto 587), `False` para SSL directo |
| `DEFAULT_FROM_EMAIL` | `noreply@icm.local` | Dirección remitente que el destinatario ve |

### Mailtrap Sandbox (desarrollo)

[Mailtrap](https://mailtrap.io) es un servidor SMTP ficticio: recibe los emails pero no los entrega realmente. Útil para probar el flujo sin spam real.

1. Registrarse en mailtrap.io → abrir el inbox de sandbox → copiar credenciales SMTP.
2. Pegar en `.env`:
```
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_HOST_USER=<tu_user_mailtrap>
EMAIL_HOST_PASSWORD=<tu_pass_mailtrap>
EMAIL_PORT=2525
EMAIL_USE_TLS=True
```
3. Al llamar `POST /api/v1/auth/forgot-password/` el email aparece en el inbox de Mailtrap, no en un correo real.

### Tests automáticos

Los tests usan `django.core.mail.backends.locmem.EmailBackend` (configurado en `config/settings/test.py`) — los emails nunca salen a la red; se capturan en `django.core.mail.outbox`. No se necesita Mailtrap para correr la suite.

### Gmail (producción rápida)

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-cuenta@gmail.com
EMAIL_HOST_PASSWORD=<app-password-de-google>
DEFAULT_FROM_EMAIL=noreply@tuapp.com
```

> Google requiere una *App Password* (no la contraseña normal de la cuenta). Se genera en: Cuenta Google → Seguridad → Verificación en dos pasos → Contraseñas de aplicación.

### Formato del email

Desde junio 2026, el email de recuperación de contraseña se envía en **formato HTML** con:
- Encabezado "ICM LogiStock" en color `#1a6b72`
- Botón "Restablecer contraseña" estilizado
- Enlace de respaldo "haz clic aquí" en color `#e07b39`
- Versión texto plano como fallback automático

---



## 7. Frontend

| Variable | Default | Descripción |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:5173` | URL base del frontend. El backend construye el link de reset de contraseña apuntando a esta URL: `{FRONTEND_URL}/reset-password?token=<token>`. En desarrollo con Vite el puerto por defecto es 5173 (no 3000). |

**Producción:**
```
FRONTEND_URL=https://tuapp.com
```

El link del email de recuperación queda: `https://tuapp.com/reset-password?token=<raw_token>`.

---

## 8. Token de recuperación de contraseña

| Variable | Default | Descripción |
|---|---|---|
| `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES` | `10` | Minutos de validez del token de reset. Pasado este tiempo el link del email queda inválido y el usuario debe solicitar uno nuevo. |

Aumentar si los usuarios reportan que el link llega expirado (correos lentos). El mínimo recomendado es 10 min; el máximo razonable es 60 min.

---

## 9. CORS

| Variable | Default dev | Descripción |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Orígenes permitidos. En desarrollo `CORS_ALLOW_ALL_ORIGINS=True` sobreescribe esto. |

**Producción:**
```
CORS_ALLOWED_ORIGINS=https://tuapp.com,https://www.tuapp.com
```

---

## 10. Futuros (no implementados aún)

Estas variables están comentadas en `.env.example` y **no deben descomentarse** hasta que los módulos correspondientes existan:

```
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
```

Se necesitarán si se añade procesamiento de tareas en background (envío de emails asíncrono, exportaciones pesadas, etc.).

---

## Resumen rápido para desarrollo local

Copia esto en tu `.env` y ajusta solo las credenciales de BD:

```
DJANGO_SECRET_KEY=dev-key-no-segura
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.development

DB_NAME=icm_db
DB_USER=icm_user
DB_PASSWORD=icm_password
DB_HOST=localhost
DB_PORT=5432

JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

APP_TIMEZONE=America/Bogota
INVOICE_SEQUENCE_PREFIX=ICM

ALMACENISTA_USERNAME=almacenista
ALMACENISTA_EMAIL=almacenista@icm.local
ALMACENISTA_PASSWORD=ICM@Admin2026!

EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_HOST_USER=<tu_user_mailtrap>
EMAIL_HOST_PASSWORD=<tu_pass_mailtrap>
EMAIL_PORT=2525
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@icm.local

FRONTEND_URL=http://localhost:5173
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES=10
```
