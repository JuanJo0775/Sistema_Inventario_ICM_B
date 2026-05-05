from apps.authentication.views import (HealthCheckView, ICMTokenObtainPairView,
                                       UserListCreateView)


def test_auth_views_are_exposed():
    assert HealthCheckView is not None
    assert ICMTokenObtainPairView is not None
    assert UserListCreateView is not None
