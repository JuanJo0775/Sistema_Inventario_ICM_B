from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = (
            "id",
            "event_type",
            "user",
            "ip_address",
            "movement",
            "description",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
