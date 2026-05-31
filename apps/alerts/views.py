from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import Alert
from apps.alerts.selectors import (
    get_active_alerts,
    get_alert_stats,
    get_resolved_alerts,
)
from apps.alerts.serializers import AlertSerializer
from apps.alerts.services import resolve_alert
from shared.openapi import TAG_ALERTS, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista, IsAlmacenistaOrAdministrador

_ALERT_QUERY_PARAMS = [
    OpenApiParameter(
        name="alert_type", type=str, location=OpenApiParameter.QUERY, required=False
    ),
    OpenApiParameter(
        name="severity", type=str, location=OpenApiParameter.QUERY, required=False
    ),
    OpenApiParameter(
        name="category", type=str, location=OpenApiParameter.QUERY, required=False
    ),
    OpenApiParameter(
        name="product_id",
        type=str,
        location=OpenApiParameter.QUERY,
        required=False,
        description="UUID del producto.",
    ),
    OpenApiParameter(
        name="location_id",
        type=str,
        location=OpenApiParameter.QUERY,
        required=False,
        description="UUID de la ubicación.",
    ),
    OpenApiParameter(
        name="date_from",
        type=str,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Fecha desde (YYYY-MM-DD).",
    ),
    OpenApiParameter(
        name="date_to",
        type=str,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Fecha hasta (YYYY-MM-DD).",
    ),
]


def _build_alert_filters(query_params) -> dict:
    filters: dict = {}
    if t := query_params.get("alert_type"):
        filters["alert_type"] = t
    if sv := query_params.get("severity"):
        filters["severity"] = sv
    if cat := query_params.get("category"):
        filters["category"] = cat
    if pid := query_params.get("product_id"):
        filters["product_id"] = UUID(str(pid))
    if lid := query_params.get("location_id"):
        filters["location_id"] = UUID(str(lid))
    if df := query_params.get("date_from"):
        filters["date_from"] = df
    if dt := query_params.get("date_to"):
        filters["date_to"] = dt
    return filters


class AlertListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AlertSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        return get_active_alerts(_build_alert_filters(self.request.query_params))

    @extend_schema(
        parameters=_ALERT_QUERY_PARAMS,
        responses={
            200: AlertSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_ALERTS],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlertHistoryView(generics.ListAPIView):
    """GET — Historial de alertas resueltas (RF-011)."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AlertSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        return get_resolved_alerts(_build_alert_filters(self.request.query_params))

    @extend_schema(
        parameters=_ALERT_QUERY_PARAMS,
        responses={
            200: AlertSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_ALERTS],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlertStatsView(APIView):
    """GET — Conteos de alertas activas por severidad y categoría (RF-011)."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        responses={200: dict, **standard_error_responses(include_403=True)},
        tags=[TAG_ALERTS],
    )
    def get(self, request):
        return Response(get_alert_stats(), status=status.HTTP_200_OK)


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
