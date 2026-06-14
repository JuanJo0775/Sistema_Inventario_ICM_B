from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
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
from apps.audit.models import AuditEventType
from apps.audit.services import log_event
from shared.exporters import export_to_csv, export_to_xlsx
from shared.openapi import TAG_ALERTS, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista, IsAlmacenistaOrAdministrador

_ALERT_EXPORT_HEADERS = [
    "id",
    "product_sku",
    "lot_code",
    "lot_expiration_date",
    "location",
    "alert_type",
    "severity",
    "category",
    "message",
    "is_resolved",
    "resolved_at",
    "created_at",
]

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
        try:
            filters["product_id"] = UUID(str(pid))
        except (ValueError, AttributeError):
            raise ValidationError({"product_id": "UUID inválido."})
    if lid := query_params.get("location_id"):
        try:
            filters["location_id"] = UUID(str(lid))
        except (ValueError, AttributeError):
            raise ValidationError({"location_id": "UUID inválido."})
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
        summary="Listar alertas activas",
        description="Lista las alertas activas y permite exportarlas.",
        parameters=_ALERT_QUERY_PARAMS,
        responses={
            200: AlertSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_ALERTS],
    )
    def get(self, request, *args, **kwargs):
        export = request.query_params.get("export", "").lower()
        if export in ("csv", "xlsx"):
            log_event(
                AuditEventType.REPORT_GENERATED,
                user=request.user,
                detail={
                    "kind": "alerts",
                    "format": export,
                    "_origin": "API",
                },
            )
            qs = self.get_queryset()
            rows = [dict(item) for item in AlertSerializer(qs, many=True).data]
            if export == "csv":
                return export_to_csv(_ALERT_EXPORT_HEADERS, rows, "alerts.csv")
            return export_to_xlsx(_ALERT_EXPORT_HEADERS, rows, "alerts.xlsx")
        return super().get(request, *args, **kwargs)


class AlertHistoryView(generics.ListAPIView):
    """GET — Historial de alertas resueltas (RF-011)."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = AlertSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        return get_resolved_alerts(_build_alert_filters(self.request.query_params))

    @extend_schema(
        summary="Historial de alertas resueltas",
        description="Lista las alertas resueltas dentro de los filtros aplicados.",
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
        summary="Métricas de alertas",
        description="Obtiene métricas resumidas de alertas activas.",
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
        summary="Detalle de alerta",
        description="Obtiene el detalle de una alerta específica.",
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
        summary="Resolver alerta",
        description="Marca una alerta como resuelta.",
        responses={
            200: AlertSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_ALERTS],
    )
    def post(self, request, pk):
        alert = resolve_alert(request.user, pk)
        return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)


class AlertPollView(APIView):
    """GET — Polling de alertas nuevas desde un timestamp (NEW-04).

    Uso: GET /api/v1/alerts/poll/?since=<ISO-timestamp>&severity=CRITICA,ALTA

    El cliente debe usar `server_timestamp` de cada respuesta como siguiente `since`.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Polling de alertas",
        description="Consulta alertas nuevas desde un timestamp dado.",
        parameters=[
            OpenApiParameter(
                name="since",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="ISO-8601 timestamp. Retorna alertas creadas después de este momento. Default: últimas 24 horas.",
            ),
            OpenApiParameter(
                name="severity",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtrar por severidades separadas por coma. Ej: CRITICA,ALTA",
            ),
        ],
        responses={200: AlertSerializer(many=True), **standard_error_responses()},
        tags=[TAG_ALERTS],
    )
    def get(self, request):
        from django.utils.dateparse import parse_datetime

        since_str = request.query_params.get("since")
        if since_str:
            since = parse_datetime(since_str)
            if since is None:
                return Response(
                    {"detail": "Formato de 'since' inválido. Use ISO-8601."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            from datetime import timedelta

            from django.utils import timezone as tz

            since = tz.now() - timedelta(hours=24)

        qs = Alert.objects.select_related("product", "location").filter(
            created_at__gt=since
        )

        severity_param = request.query_params.get("severity")
        if severity_param:
            severities = [s.strip() for s in severity_param.split(",") if s.strip()]
            qs = qs.filter(severity__in=severities)

        qs = qs.order_by("-created_at")[:50]

        from django.utils import timezone as tz

        return Response(
            {
                "server_timestamp": tz.now().isoformat(),
                "count": qs.count(),
                "results": AlertSerializer(qs, many=True).data,
            }
        )
