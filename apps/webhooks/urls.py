from django.urls import path

from apps.webhooks.views import (
    WebhookDeliveryListView,
    WebhookEndpointDetailView,
    WebhookEndpointDisableView,
    WebhookEndpointEnableView,
    WebhookEndpointListCreateView,
    WebhookEndpointRestoreView,
    WebhookStatsView,
    WebhookTestView,
)

urlpatterns = [
    path(
        "endpoints/", WebhookEndpointListCreateView.as_view(), name="webhooks-endpoints"
    ),
    path(
        "endpoints/<uuid:pk>/",
        WebhookEndpointDetailView.as_view(),
        name="webhooks-endpoint-detail",
    ),
    path(
        "endpoints/<uuid:pk>/restore/",
        WebhookEndpointRestoreView.as_view(),
        name="webhooks-endpoint-restore",
    ),
    path(
        "endpoints/<uuid:pk>/disable/",
        WebhookEndpointDisableView.as_view(),
        name="webhooks-endpoint-disable",
    ),
    path(
        "endpoints/<uuid:pk>/enable/",
        WebhookEndpointEnableView.as_view(),
        name="webhooks-endpoint-enable",
    ),
    path(
        "endpoints/<uuid:pk>/test/",
        WebhookTestView.as_view(),
        name="webhooks-endpoint-test",
    ),
    path("deliveries/", WebhookDeliveryListView.as_view(), name="webhooks-deliveries"),
    path("stats/", WebhookStatsView.as_view(), name="webhooks-stats"),
]
