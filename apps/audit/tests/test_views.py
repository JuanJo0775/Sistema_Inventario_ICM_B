from apps.audit.views import AuditLogListView


def test_audit_view_is_available():
    assert AuditLogListView is not None
