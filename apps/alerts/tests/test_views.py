from apps.alerts.views import AlertListView


def test_alerts_view_is_available():
    assert AlertListView is not None
