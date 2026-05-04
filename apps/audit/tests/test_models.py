from apps.audit.models import AuditEventType, AuditLog


def test_audit_model_exposes_event_types():
    assert AuditEventType.LOGIN_SUCCESS == "LOGIN_SUCCESS"
    assert AuditLog._meta.get_field("id").primary_key is True
