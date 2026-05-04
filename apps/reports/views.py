"""Vistas de reportes de solo lectura (RF-010)."""

from __future__ import annotations

from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.movements.serializers import MovementSerializer
from apps.reports.selectors import movement_counts_by_period, movement_history, sales_dispatch_totals
from apps.reports.serializers import MovementSummaryResponseSerializer, SalesSummaryResponseSerializer
from shared.openapi import TAG_REPORTS
from shared.permissions import IsAlmacenistaOrAdministrador


def _parse_range(request):
    start = parse_datetime(request.query_params.get("start", ""))
    end = parse_datetime(request.query_params.get("end", ""))
    if not start or not end:
        raise ValidationError({"detail": "Parámetros start y end son obligatorios (ISO-8601)."})
    return start, end


class MovementSummaryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Inicio del rango (ISO-8601).",
            ),
            OpenApiParameter(
                name="end",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Fin del rango (ISO-8601).",
            ),
        ],
        responses={200: MovementSummaryResponseSerializer},
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        start, end = _parse_range(request)
        return Response({"counts": movement_counts_by_period(start=start, end=end)})


class SalesSummaryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Inicio del rango (ISO-8601).",
            ),
            OpenApiParameter(
                name="end",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Fin del rango (ISO-8601).",
            ),
        ],
        responses={200: SalesSummaryResponseSerializer},
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        start, end = _parse_range(request)
        return Response({"sales": sales_dispatch_totals(start=start, end=end)})


class MovementHistoryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="product_id", type=int, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="user_id", type=int, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(
                name="start",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtro inferior de fecha (ISO-8601).",
            ),
            OpenApiParameter(
                name="end",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtro superior de fecha (ISO-8601).",
            ),
        ],
        responses={200: MovementSerializer(many=True)},
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        start = parse_datetime(request.query_params.get("start", "")) if request.query_params.get("start") else None
        end = parse_datetime(request.query_params.get("end", "")) if request.query_params.get("end") else None
        qs = movement_history(
            product_id=int(request.query_params["product_id"]) if request.query_params.get("product_id") else None,
            user_id=int(request.query_params["user_id"]) if request.query_params.get("user_id") else None,
            start=start,
            end=end,
        )[:200]
        return Response(MovementSerializer(qs, many=True).data)
