from django.urls import path

from apps.alerts.views import (
    AlertDetailView,
    AlertHistoryView,
    AlertListView,
    AlertPollView,
    AlertResolveView,
    AlertStatsView,
)

urlpatterns = [
    path("", AlertListView.as_view(), name="alerts-list"),
    path("poll/", AlertPollView.as_view(), name="alerts-poll"),
    path("history/", AlertHistoryView.as_view(), name="alerts-history"),
    path("stats/", AlertStatsView.as_view(), name="alerts-stats"),
    path("<int:pk>/", AlertDetailView.as_view(), name="alerts-detail"),
    path("<int:pk>/resolve/", AlertResolveView.as_view(), name="alerts-resolve"),
]
