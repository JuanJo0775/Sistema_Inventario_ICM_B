"""Configuración de producción (RNF-002, RNF-003)."""

from datetime import timedelta

from .base import *  # noqa: F401,F403

# SECRET_KEY no tiene default — arranca con ImproperlyConfigured si no está en el entorno.
SECRET_KEY = config("DJANGO_SECRET_KEY")  # type: ignore[assignment]  # noqa: F405

DEBUG = False

_allowed_raw = config("DJANGO_ALLOWED_HOSTS", default="")  # noqa: F405
ALLOWED_HOSTS = [h.strip() for h in _allowed_raw.split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError(
        "DJANGO_ALLOWED_HOSTS debe estar configurado en producción. "
        "Ejemplo: DJANGO_ALLOWED_HOSTS=api.tudominio.com"
    )

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# DATABASES viene de base.py con el switch DB_PROVIDER (local/neon)
# Solo se fuerza connect_timeout para producción:
if config("DB_PROVIDER", default="local") == "local":  # noqa: F405
    DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 10  # noqa: F405

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [config("FRONTEND_URL", default="https://example.com").strip()]  # noqa: F405

SIMPLE_JWT.update(  # noqa: F405
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    }
)

LOGGING["root"]["level"] = "INFO"  # noqa: F405

# MEDIA-15: JSON structured logging for production log pipelines
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "shared.logging_formatters.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# MEDIA-11: WhiteNoise serves static files without a separate web server
MIDDLEWARE = (  # noqa: F405
    [
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ]
    + MIDDLEWARE[2:]  # noqa: F405
)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# M-06: Restringir acceso a documentación OpenAPI solo a staff en producción.
RESTRICT_API_SCHEMA = True
