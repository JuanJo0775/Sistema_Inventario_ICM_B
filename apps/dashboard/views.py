from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.serializers import (
    DashboardAlertSummarySerializer,
    DashboardKPISummarySerializer,
    DashboardMetricSummarySerializer,
    DashboardMovementSerializer,
    DashboardOverviewSerializer,
)
from apps.dashboard.services import (
    build_dashboard_alerts,
    build_dashboard_kpis,
    build_dashboard_metrics,
    build_dashboard_movements,
    build_dashboard_overview,
)
from shared.openapi import TAG_DASHBOARD, standard_error_responses
from shared.permissions import IsAlmacenista
from shared.utils.params import clamp_limit, clamp_period_days


class DashboardOverviewView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Resumen general del dashboard",
        description="Devuelve el resumen general del dashboard ejecutivo.",
        parameters=[
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Ventana histórica para el overview del dashboard.",
            ),
            OpenApiParameter(
                name="movements_limit",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Cantidad máxima de movimientos recientes.",
            ),
        ],
        responses={
            200: DashboardOverviewSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_DASHBOARD],
    )
    def get(self, request):
        period_days = clamp_period_days(request.query_params.get("period_days", 30))
        movements_limit = clamp_limit(request.query_params.get("movements_limit", 10))
        return Response(
            build_dashboard_overview(
                period_days=period_days, movements_limit=movements_limit
            )
        )


class DashboardMetricsView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Métricas operativas",
        description="Devuelve las métricas operativas del dashboard.",
        parameters=[
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ],
        responses={
            200: DashboardMetricSummarySerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_DASHBOARD],
    )
    def get(self, request):
        period_days = clamp_period_days(request.query_params.get("period_days", 30))
        return Response(build_dashboard_metrics(period_days=period_days))


class DashboardAlertsView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Resumen de alertas",
        description="Devuelve el resumen de alertas del dashboard.",
        parameters=[
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="expiring_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: DashboardAlertSummarySerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_DASHBOARD],
    )
    def get(self, request):
        period_days = clamp_period_days(request.query_params.get("period_days", 30))
        expiring_days = clamp_period_days(request.query_params.get("expiring_days", 30))
        return Response(
            build_dashboard_alerts(period_days=period_days, expiring_days=expiring_days)
        )


class DashboardKPIsView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Resumen de KPI",
        description="Devuelve el resumen de KPI del dashboard.",
        parameters=[
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ],
        responses={
            200: DashboardKPISummarySerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_DASHBOARD],
    )
    def get(self, request):
        period_days = clamp_period_days(request.query_params.get("period_days", 30))
        return Response(build_dashboard_kpis(period_days=period_days))


class DashboardMovementsView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Movimientos recientes",
        description="Devuelve los movimientos recientes visibles en el dashboard.",
        parameters=[
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: DashboardMovementSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_DASHBOARD],
    )
    def get(self, request):
        period_days = clamp_period_days(request.query_params.get("period_days", 30))
        limit = clamp_limit(request.query_params.get("limit", 10))
        return Response(build_dashboard_movements(period_days=period_days, limit=limit))
