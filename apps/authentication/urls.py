"""Rutas de autenticación ICM."""

from django.urls import path

from apps.authentication.views import (
    HealthCheckView,
    ICMTokenObtainPairView,
    ICMTokenRefreshView,
    LogoutView,
    MeView,
    TemporaryPermitRevokeView,
    UserDetailView,
    UserDisableView,
    UserEnableView,
    UserListCreateView,
    UserScheduleDetailView,
    UserTemporaryPermitListCreateView,
)

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="auth-health"),
    path("login/", ICMTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", ICMTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("users/", UserListCreateView.as_view(), name="auth-users"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="auth-user-detail"),
    path(
        "users/<uuid:pk>/disable/", UserDisableView.as_view(), name="auth-user-disable"
    ),
    path("users/<uuid:pk>/enable/", UserEnableView.as_view(), name="auth-user-enable"),
    path(
        "users/<uuid:pk>/schedule/",
        UserScheduleDetailView.as_view(),
        name="auth-user-schedule",
    ),
    path(
        "users/<uuid:pk>/temporary-permits/",
        UserTemporaryPermitListCreateView.as_view(),
        name="auth-user-temporary-permits",
    ),
    path(
        "temporary-permits/<uuid:pk>/revoke/",
        TemporaryPermitRevokeView.as_view(),
        name="auth-temporary-permit-revoke",
    ),
]
