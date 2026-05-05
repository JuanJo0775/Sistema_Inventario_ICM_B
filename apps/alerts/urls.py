from django.urls import path

from apps.alerts.views import AlertDetailView, AlertListView, AlertResolveView

urlpatterns = [
    path("", AlertListView.as_view(), name="alerts-list"),
    path("<uuid:pk>/", AlertDetailView.as_view(), name="alerts-detail"),
    path("<uuid:pk>/resolve/", AlertResolveView.as_view(), name="alerts-resolve"),
]
