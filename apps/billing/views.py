"""Vistas del módulo de facturación comercial (billing)."""

from __future__ import annotations

import datetime

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.serializers import (
    CompanyInfoSerializer,
    InvoiceCreateSerializer,
    InvoiceDetailSerializer,
    InvoiceListSerializer,
    InvoiceStatsSerializer,
    InvoiceVoidSerializer,
)
from apps.billing.services import (
    create_multi_dispatch_invoice,
    get_company_info,
    get_invoice_stats,
    update_company_info,
    void_invoice,
)
from apps.movements.models import Invoice
from shared.openapi import TAG_BILLING, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import (
    IsAlmacenista,
    IsAlmacenistaOrAdministrador,
    IsAlmacenistaOrAuxiliar,
    IsWithinOperatingHours,
)


@extend_schema_view(
    get=extend_schema(
        summary="Listar facturas",
        description=(
            "Lista las facturas comerciales con filtros de fecha, tipo y búsqueda."
            " Soporta ?start_date=, ?end_date=, ?invoice_type=, ?search= (número, cliente, doc),"
            " ?include_voided= (default false)."
        ),
        tags=[TAG_BILLING],
        parameters=[
            OpenApiParameter(
                "start_date", str, description="Fecha inicio ISO 8601 (YYYY-MM-DD)."
            ),
            OpenApiParameter(
                "end_date", str, description="Fecha fin ISO 8601 (YYYY-MM-DD)."
            ),
            OpenApiParameter(
                "invoice_type", str, description="'retail' | 'wholesale'."
            ),
            OpenApiParameter(
                "search",
                str,
                description="Busca en número, nombre o documento de cliente.",
            ),
            OpenApiParameter(
                "include_voided",
                bool,
                description="Si true, incluye facturas anuladas.",
            ),
        ],
        responses={
            200: InvoiceListSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Crear factura multi-producto",
        description=(
            "RF-006, BR-13 — Crea una factura agrupando múltiples productos en una única transacción atómica."
            " Genera movements de salida por cada ítem y un Invoice compartido con numeración ICM-XXXX."
        ),
        tags=[TAG_BILLING],
        request=InvoiceCreateSerializer,
        responses={
            201: InvoiceDetailSerializer,
            **standard_error_responses(include_403=True, include_409=True),
        },
    ),
)
class InvoiceListCreateView(generics.GenericAPIView):
    pagination_class = ICMPageNumberPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [
                IsAuthenticated(),
                IsAlmacenistaOrAuxiliar(),
                IsWithinOperatingHours(),
            ]
        return [IsAuthenticated(), IsAlmacenistaOrAdministrador()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvoiceCreateSerializer
        return InvoiceListSerializer

    def get_queryset(self):
        qs = (
            Invoice.objects.prefetch_related("movements")
            .select_related("issued_by", "voided_by")
            .order_by("-issued_at")
        )

        include_voided = (
            self.request.query_params.get("include_voided", "false").lower() == "true"
        )
        if not include_voided:
            qs = qs.filter(is_voided=False)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        invoice_type = self.request.query_params.get("invoice_type")
        search = self.request.query_params.get("search", "").strip()

        if start_date:
            try:
                datetime.date.fromisoformat(start_date)
                qs = qs.filter(issued_at__date__gte=start_date)
            except ValueError:
                pass  # parámetro inválido → ignorar silenciosamente
        if end_date:
            try:
                datetime.date.fromisoformat(end_date)
                qs = qs.filter(issued_at__date__lte=end_date)
            except ValueError:
                pass
        if invoice_type in ("retail", "wholesale"):
            qs = qs.filter(invoice_type=invoice_type)
        if search:
            qs = qs.filter(
                Q(number__icontains=search)
                | Q(customer_name__icontains=search)
                | Q(customer_id_number__icontains=search)
            )
        return qs

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InvoiceListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        ser = InvoiceCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        invoice = create_multi_dispatch_invoice(
            request.user,
            invoice_type=d["invoice_type"],
            location_id=d["location_id"],
            customer_data=d["customer"],
            items=d["items"],
            note=d.get("note") or None,
            privacy_notice_acknowledged=d.get("privacy_notice_acknowledged", False),
        )
        return Response(
            InvoiceDetailSerializer(invoice).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de factura",
        description="Retorna el detalle completo de una factura por ID, incluyendo todos sus movements.",
        tags=[TAG_BILLING],
        responses={
            200: InvoiceDetailSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
)
class InvoiceDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)
    serializer_class = InvoiceDetailSerializer

    def get_queryset(self):
        return Invoice.objects.prefetch_related("movements__product").select_related(
            "issued_by", "voided_by"
        )


class InvoiceVoidView(APIView):
    """POST /billing/invoices/{id}/void/ — Anula una factura y revierte el stock."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        summary="Anular factura",
        description=(
            "Anula la factura y crea movements ANULACION compensatorios que revierten el stock."
            " Solo el almacenista puede anular. Los movements originales son inmutables (BR-10)."
            " Retorna 409 si la factura ya fue anulada."
        ),
        tags=[TAG_BILLING],
        request=InvoiceVoidSerializer,
        responses={
            200: InvoiceDetailSerializer,
            **standard_error_responses(
                include_403=True, include_404=True, include_409=True
            ),
        },
    )
    def post(self, request, pk):
        ser = InvoiceVoidSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        # void_invoice() maneja internamente Http404 si el Invoice no existe
        invoice = void_invoice(
            pk, user=request.user, reason=ser.validated_data["reason"]
        )
        return Response(InvoiceDetailSerializer(invoice).data)


class InvoiceStatsView(APIView):
    """GET /billing/invoices/stats/ — Métricas de ventas hoy y mes actual."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAdministrador)

    @extend_schema(
        summary="Estadísticas de facturación",
        description="Retorna totales de ventas y cantidad de facturas para hoy y el mes en curso.",
        tags=[TAG_BILLING],
        responses={
            200: InvoiceStatsSerializer,
            **standard_error_responses(),
        },
    )
    def get(self, request):
        stats = get_invoice_stats()
        return Response(InvoiceStatsSerializer(stats).data)


class CompanyConfigView(APIView):
    """GET/PUT /billing/config/company/ — Datos fiscales de la empresa."""

    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated(), IsAlmacenistaOrAdministrador()]

    @extend_schema(
        summary="Obtener datos de empresa",
        description="Retorna la configuración fiscal de la empresa usada en los encabezados de factura.",
        tags=[TAG_BILLING],
        responses={
            200: CompanyInfoSerializer,
            **standard_error_responses(),
        },
    )
    def get(self, request):
        info = get_company_info()
        return Response(CompanyInfoSerializer(info).data)

    @extend_schema(
        summary="Actualizar datos de empresa",
        description="Actualiza los datos fiscales de la empresa (razón social, NIT, resolución DIAN, etc.). Solo almacenista.",
        tags=[TAG_BILLING],
        request=CompanyInfoSerializer,
        responses={
            200: CompanyInfoSerializer,
            **standard_error_responses(include_403=True),
        },
    )
    def put(self, request):
        ser = CompanyInfoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        info = update_company_info(request.user, ser.validated_data)
        return Response(CompanyInfoSerializer(info).data)
