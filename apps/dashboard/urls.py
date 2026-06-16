from django.urls import path

from apps.dashboard.views import (
    DashboardAlertsView,
    DashboardKPIsView,
    DashboardMetricsView,
    DashboardMovementsView,
    DashboardOverviewView,
)

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("metrics/", DashboardMetricsView.as_view(), name="dashboard-metrics"),
    path("alerts/", DashboardAlertsView.as_view(), name="dashboard-alerts"),
    path("kpis/", DashboardKPIsView.as_view(), name="dashboard-kpis"),
    path("movements/", DashboardMovementsView.as_view(), name="dashboard-movements"),
]
