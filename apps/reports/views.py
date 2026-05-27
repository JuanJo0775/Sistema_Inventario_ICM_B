"""Vistas de reportes de solo lectura (RF-010)."""

from __future__ import annotations

from uuid import UUID

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from drf_spectacular.utils import (OpenApiParameter, OpenApiResponse,
                                   extend_schema)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.movements.serializers import MovementSerializer
from apps.reports.selectors import (get_expiring_products,
                                    get_inventory_summary, get_invoice_history,
                                    get_kpi_dashboard, get_movement_report,
                                    get_top_dispatched_products,
                                    movement_counts_by_period,
                                    movement_history, sales_dispatch_totals)
from apps.reports.serializers import (ExpiringLotReportItemSerializer,
                                      InventorySummaryItemSerializer,
                                      KpiDashboardSerializer,
                                      ReportDatasetSerializer,
                                      MovementReportItemSerializer,
                                      MovementSummaryResponseSerializer,
                                      SalesSummaryResponseSerializer,
                                      TopDispatchedProductSerializer)
from shared.openapi import TAG_REPORTS, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenistaOrAdministrador


def _parse_range(request):
    start = parse_datetime(request.query_params.get("start", ""))
    end = parse_datetime(request.query_params.get("end", ""))
    if not start or not end:
        raise ValidationError(
            {"detail": "Parámetros start y end son obligatorios (ISO-8601)."}
        )
    return start, end


def _report_filters_payload(request):
    filters: dict[str, object] = {}
    for key in ("start", "end", "invoice_number", "type", "days", "limit", "period_days", "kind"):
        value = request.query_params.get(key)
        if value not in (None, ""):
            filters[key] = value
    for key in ("product_id", "user_id"):
        value = request.query_params.get(key)
        if value not in (None, ""):
            filters[key] = value
    return filters


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
        responses={
            200: MovementSummaryResponseSerializer,
            **standard_error_responses(include_403=True),
        },
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
        responses={
            200: SalesSummaryResponseSerializer,
            **standard_error_responses(include_403=True),
        },
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
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
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
        responses={
            200: OpenApiResponse(description="Historial de movimientos."),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        start = (
            parse_datetime(request.query_params.get("start", ""))
            if request.query_params.get("start")
            else None
        )
        end = (
            parse_datetime(request.query_params.get("end", ""))
            if request.query_params.get("end")
            else None
        )
        raw_pid = request.query_params.get("product_id")
        product_id = UUID(str(raw_pid)) if raw_pid else None
        qs = movement_history(
            product_id=product_id,
            user_id=int(request.query_params["user_id"])
            if request.query_params.get("user_id")
            else None,
            start=start,
            end=end,
        )[:200]
        return Response(MovementSerializer(qs, many=True).data)


class InventorySummaryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        responses={
            200: InventorySummaryItemSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        return Response(get_inventory_summary())


class MovementReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="end", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="type", type=str, location=OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={
            200: MovementReportItemSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
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
            OpenApiParameter(
                name="limit", type=int, location=OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: TopDispatchedProductSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        period_days = int(request.query_params.get("period_days", 30))
        return Response(
            get_top_dispatched_products(limit=limit, period_days=period_days)
        )


class InvoiceHistoryReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start", type=str, location=OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                name="end", type=str, location=OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                name="invoice_number",
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
            200: MovementSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
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
        return paginator.get_paginated_response(
            MovementSerializer(page, many=True).data
        )


class KpiDashboardReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        responses={
            200: KpiDashboardSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        return Response(get_kpi_dashboard())


class ExpiringProductsReportView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="days", type=int, location=OpenApiParameter.QUERY, required=False
            )
        ],
        responses={
            200: ExpiringLotReportItemSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = get_expiring_products(days=days)
        return Response(ExpiringLotReportItemSerializer(data, many=True).data)


class ReportDatasetView(APIView):
    """Contrato estable para que el frontend consuma datos y arme exportaciones."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="kind",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description=(
                    "Tipo de dataset: inventory-summary, movements-summary, movements-report, "
                    "movements-history, sales-summary, top-products, invoices, kpi, expiring."
                ),
            ),
            OpenApiParameter(
                name="start",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Inicio del rango (ISO-8601).",
            ),
            OpenApiParameter(
                name="end",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Fin del rango (ISO-8601).",
            ),
            OpenApiParameter(
                name="product_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID del producto.",
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="ID del usuario operario.",
            ),
            OpenApiParameter(
                name="invoice_number",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="type",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="days",
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
            OpenApiParameter(
                name="period_days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: ReportDatasetSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_REPORTS],
    )
    def get(self, request):
        kind = request.query_params.get("kind")
        if not kind:
            raise ValidationError({"detail": "Parámetro kind es obligatorio."})

        filters = _report_filters_payload(request)
        generated_at = timezone.now()

        if kind == "inventory-summary":
            data = get_inventory_summary()
        elif kind == "movements-summary":
            start, end = _parse_range(request)
            data = {"counts": movement_counts_by_period(start=start, end=end)}
        elif kind == "movements-report":
            start, end = _parse_range(request)
            report_filters = {}
            if mtype := request.query_params.get("type"):
                report_filters["type"] = mtype
            data = get_movement_report(start, end, report_filters)
        elif kind == "movements-history":
            start = (
                parse_datetime(request.query_params.get("start", ""))
                if request.query_params.get("start")
                else None
            )
            end = (
                parse_datetime(request.query_params.get("end", ""))
                if request.query_params.get("end")
                else None
            )
            raw_pid = request.query_params.get("product_id")
            product_id = UUID(str(raw_pid)) if raw_pid else None
            qs = movement_history(
                product_id=product_id,
                user_id=int(request.query_params["user_id"])
                if request.query_params.get("user_id")
                else None,
                start=start,
                end=end,
            )[:200]
            data = MovementSerializer(qs, many=True).data
        elif kind == "sales-summary":
            start, end = _parse_range(request)
            data = {"sales": sales_dispatch_totals(start=start, end=end)}
        elif kind == "top-products":
            limit = int(request.query_params.get("limit", 10))
            period_days = int(request.query_params.get("period_days", 30))
            data = get_top_dispatched_products(limit=limit, period_days=period_days)
        elif kind == "invoices":
            filters_map: dict = {}
            if s := request.query_params.get("start"):
                filters_map["start"] = parse_datetime(s)
            if e := request.query_params.get("end"):
                filters_map["end"] = parse_datetime(e)
            if inv := request.query_params.get("invoice_number"):
                filters_map["invoice_number"] = inv
            if pid := request.query_params.get("product_id"):
                filters_map["product_id"] = UUID(str(pid))
            qs = get_invoice_history(filters_map)
            data = MovementSerializer(list(qs), many=True).data
        elif kind == "kpi":
            data = get_kpi_dashboard()
        elif kind == "expiring":
            days = int(request.query_params.get("days", 30))
            data = ExpiringLotReportItemSerializer(
                get_expiring_products(days=days), many=True
            ).data
        else:
            raise ValidationError(
                {
                    "detail": (
                        "kind debe ser uno de: inventory-summary, movements-summary, "
                        "movements-report, movements-history, sales-summary, top-products, "
                        "invoices, kpi, expiring."
                    )
                }
            )

        payload = {
            "report": kind,
            "generated_at": generated_at,
            "filters": filters,
            "data": data,
            "suggested_filename": f"{kind}-{generated_at:%Y%m%d-%H%M%S}",
        }
        return Response(payload)
