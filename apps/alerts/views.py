from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import Alert
from apps.alerts.selectors import get_active_alerts
from apps.alerts.serializers import AlertSerializer
from apps.alerts.services import resolve_alert
from shared.openapi import TAG_ALERTS, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista, IsAlmacenistaOrAdministrador


class AlertListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AlertSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        filters: dict = {}
        if t := self.request.query_params.get("alert_type"):
            filters["alert_type"] = t
        if pid := self.request.query_params.get("product_id"):
            filters["product_id"] = UUID(str(pid))
        return get_active_alerts(filters)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="alert_type",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="product_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID del producto.",
            ),
        ],
        responses={
            200: AlertSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_ALERTS],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlertDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AlertSerializer
    queryset = Alert.objects.select_related("product", "location").all()
    lookup_field = "pk"

    @extend_schema(
        responses={
            200: AlertSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_ALERTS],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlertResolveView(APIView):
    """POST — Marca alerta como resuelta (solo almacenista, RF-011)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        request=None,
        responses={
            200: AlertSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_ALERTS],
    )
    def post(self, request, pk):
        alert = resolve_alert(request.user, UUID(str(pk)))
        return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)
