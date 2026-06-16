from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny, IsAdminUser


def _schema_permissions():
    """En producción (RESTRICT_API_SCHEMA=True) solo staff; en dev/test, público."""
    if getattr(settings, "RESTRICT_API_SCHEMA", False):
        return [IsAdminUser]
    return [AllowAny]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/movements/", include("apps.movements.urls")),
    path("api/v1/purchasing/", include("apps.purchasing.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/alerts/", include("apps.alerts.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/webhooks/", include("apps.webhooks.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=_schema_permissions()),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            permission_classes=_schema_permissions(),
        ),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            permission_classes=_schema_permissions(),
        ),
        name="redoc",
    ),
]

if settings.DEBUG:
    from shared.media_views import protected_media

    urlpatterns += [
        path("media/<path:path>", protected_media, name="protected-media"),
    ]
