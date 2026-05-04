from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from shared.openapi import TAG_AUDIT
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


class AuditLogListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    serializer_class = AuditLogSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user", "movement").all()
        event_type = self.request.query_params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs.order_by("-created_at")

    @extend_schema(responses={200: AuditLogSerializer(many=True)}, tags=[TAG_AUDIT])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
