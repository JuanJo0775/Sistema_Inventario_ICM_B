from apps.alerts.views import AlertDetailView, AlertListView, AlertResolveView


def test_alerts_views_are_available():
    assert AlertListView is not None
    assert AlertDetailView is not None
    assert AlertResolveView is not None
