from django.urls import path

from apps.alerts.views import (
    AlertDetailView,
    AlertHistoryView,
    AlertListView,
    AlertResolveView,
    AlertStatsView,
)

urlpatterns = [
    path("", AlertListView.as_view(), name="alerts-list"),
    path("history/", AlertHistoryView.as_view(), name="alerts-history"),
    path("stats/", AlertStatsView.as_view(), name="alerts-stats"),
    path("<uuid:pk>/", AlertDetailView.as_view(), name="alerts-detail"),
    path("<uuid:pk>/resolve/", AlertResolveView.as_view(), name="alerts-resolve"),
]
