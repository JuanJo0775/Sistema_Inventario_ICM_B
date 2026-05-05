from apps.audit.views import AuditLogDetailView, AuditLogListView


def test_audit_views_are_available():
    assert AuditLogListView is not None
    assert AuditLogDetailView is not None
