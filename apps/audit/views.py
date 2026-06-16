from __future__ import annotations

import contextlib

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.audit.models import AuditLog
from apps.audit.selectors import get_audit_log
from apps.audit.serializers import AuditLogSerializer
from apps.audit.services import log_immutable_modification_attempt
from shared.exceptions import ImmutableRecordError
from shared.openapi import TAG_AUDIT, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenistaOrAdministrador


class AuditLogListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AuditLogSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        filters: dict = {}
        if et := self.request.query_params.get("event_type"):
            filters["event_type"] = et
        if uid := self.request.query_params.get("user_id"):
            with contextlib.suppress(ValueError, TypeError):
                filters["user_id"] = int(uid)
        if s := self.request.query_params.get("start"):
            filters["start"] = s
        if e := self.request.query_params.get("end"):
            filters["end"] = e
        return get_audit_log(
            filters, executor_role=getattr(self.request.user, "role", "")
        )

    @extend_schema(
        summary="Listar auditoría",
        description="Lista los registros de auditoría con filtros opcionales.",
        parameters=[
            OpenApiParameter(
                name="event_type",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="start", type=str, location=OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                name="end", type=str, location=OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={
            200: AuditLogSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_AUDIT],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AuditLogDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("user", "movement").all()
    lookup_field = "pk"

    def http_method_not_allowed(self, request, *args, **kwargs):
        log_immutable_modification_attempt(
            user=(
                request.user
                if getattr(request.user, "is_authenticated", False)
                else None
            ),
            request=request,
            detail={
                "resource": "audit_log",
                "audit_log_id": str(kwargs.get("pk") or ""),
            },
        )
        raise ImmutableRecordError()

    @extend_schema(
        summary="Detalle de evento de auditoría",
        description="Obtiene el detalle de un evento de auditoría.",
        responses={
            200: AuditLogSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_AUDIT],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
