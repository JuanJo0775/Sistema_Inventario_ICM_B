"""Vistas de reportes de solo lectura (RF-010)."""

from __future__ import annotations

from uuid import UUID

from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.serializers import ProductSerializer
from apps.movements.serializers import MovementSerializer
from apps.reports.selectors import (
    get_expiring_products,
    get_inventory_summary,
    get_invoice_history,
    get_kpi_dashboard,
    get_movement_report,
    get_top_dispatched_products,
    movement_counts_by_period,
    movement_history,
    sales_dispatch_totals,
)
from apps.reports.serializers import MovementSummaryResponseSerializer, SalesSummaryResponseSerializer
from shared.openapi import TAG_REPORTS
from shared.pagination import ICMPageNumberPagination
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
            OpenApiParameter(
                name="product_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID del producto.",
            ),
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
        raw_pid = request.query_params.get("product_id")
        product_id = UUID(str(raw_pid)) if raw_pid else None
        qs = movement_history(
            product_id=product_id,
            user_id=int(request.query_params["user_id"]) if request.query_params.get("user_id") else None,
            start=start,
            end=end,
        )[:200]
        return Response(MovementSerializer(qs, many=True).data)


class InventorySummaryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(tags=[TAG_REPORTS])
    def get(self, request):
        return Response(get_inventory_summary())


class MovementReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="start", type=str, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="end", type=str, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="type", type=str, location=OpenApiParameter.QUERY, required=False),
        ],
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        start, end = _parse_range(request)
        filters = {}
        if mtype := request.query_params.get("type"):
            filters["type"] = mtype
        return Response(get_movement_report(start, end, filters))


class TopDispatchedProductsReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="limit", type=int, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="period_days", type=int, location=OpenApiParameter.QUERY, required=False),
        ],
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        period_days = int(request.query_params.get("period_days", 30))
        return Response(get_top_dispatched_products(limit=limit, period_days=period_days))


class InvoiceHistoryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="start", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="end", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="invoice_number", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(
                name="product_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID del producto.",
            ),
        ],
        responses={200: MovementSerializer(many=True)},
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        filters: dict = {}
        if s := request.query_params.get("start"):
            filters["start"] = parse_datetime(s)
        if e := request.query_params.get("end"):
            filters["end"] = parse_datetime(e)
        if inv := request.query_params.get("invoice_number"):
            filters["invoice_number"] = inv
        if pid := request.query_params.get("product_id"):
            filters["product_id"] = UUID(str(pid))
        qs = get_invoice_history(filters)
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        return paginator.get_paginated_response(MovementSerializer(page, many=True).data)


class KpiDashboardReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(tags=[TAG_REPORTS])
    def get(self, request):
        return Response(get_kpi_dashboard())


class ExpiringProductsReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[OpenApiParameter(name="days", type=int, location=OpenApiParameter.QUERY, required=False)],
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        qs = get_expiring_products(days=days)
        return Response(ProductSerializer(qs, many=True).data)
