from django.urls import path

from apps.webhooks.views import (
    WebhookDeliveryListView,
    WebhookEndpointDetailView,
    WebhookEndpointListCreateView,
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
        "endpoints/<uuid:pk>/test/",
        WebhookTestView.as_view(),
        name="webhooks-endpoint-test",
    ),
    path("deliveries/", WebhookDeliveryListView.as_view(), name="webhooks-deliveries"),
    path("stats/", WebhookStatsView.as_view(), name="webhooks-stats"),
]
