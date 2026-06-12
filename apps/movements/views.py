"""Vistas del ledger (RF-005–RF-009)."""

from __future__ import annotations

from django.http import FileResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import log_immutable_modification_attempt
from apps.movements.models import Invoice, Movement, MovementType
from apps.movements.serializers import (
    AdjustmentCorrectionSerializer,
    AdjustmentCreateSerializer,
    ComboDispatchSerializer,
    CorrectionCreateSerializer,
    DispatchCreateSerializer,
    EntryCreateSerializer,
    InvoiceSerializer,
    MovementSerializer,
    ReturnCreateSerializer,
    TransferCreateSerializer,
)
from apps.movements.services import (
    correct_movement_within_window,
    dispatch_combo,
    register_adjustment,
    register_dispatch,
    register_entry,
    register_internal_transfer,
    register_return,
)
from shared.exceptions import ImmutableRecordError
from shared.openapi import TAG_MOVEMENTS, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista, IsAlmacenistaOrAuxiliar


@extend_schema_view(
    get=extend_schema(
        summary="Listar movimientos",
        description="Lista los movimientos del ledger con filtros opcionales.",
        responses={
            200: MovementSerializer(many=True),
            **standard_error_responses(),
        },
    ),
)
class MovementListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MovementSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = (
            Movement.objects.select_related("product", "lot", "executed_by")
            .all()
            .order_by("-created_at")
        )
        product = self.request.query_params.get("product_id")
        movement_type = self.request.query_params.get("movement_type")
        if product:
            qs = qs.filter(product_id=product)
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        return qs


@extend_schema_view(
    get=extend_schema(
        summary="Listar entradas",
        description="Lista las entradas de inventario registradas.",
        responses={
            200: MovementSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Registrar entrada",
        description="Registra una nueva entrada de inventario.",
        request=EntryCreateSerializer,
        responses={
            201: MovementSerializer,
            **standard_error_responses(include_403=True, include_409=True),
        },
    ),
)
class EntryListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)
    pagination_class = ICMPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EntryCreateSerializer
        return MovementSerializer

    def get_queryset(self):
        return (
            Movement.objects.filter(movement_type=MovementType.ENTRADA)
            .select_related("product", "lot", "executed_by", "destination_location")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_entry(
            request.user,
            d["product_id"],
            d["location_id"],
            d["quantity"],
            lot_code=d.get("lot_code"),
            lot_expiration_date=d.get("lot_expiration_date"),
            serial_number=d.get("serial_number"),
            qty_invoiced=d.get("qty_invoiced"),
            discrepancy_note=d.get("discrepancy_note"),
            cold_chain_acknowledged=d.get("cold_chain_acknowledged", False),
            electrical_safety_acknowledged=d.get(
                "electrical_safety_acknowledged", False
            ),
        )
        return Response(
            MovementSerializer(movement).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de entrada",
        description="Obtiene el detalle de una entrada de inventario.",
        responses={
            200: MovementSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
)
class EntryDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MovementSerializer

    def get_queryset(self):
        return Movement.objects.filter(
            movement_type=MovementType.ENTRADA
        ).select_related("product", "lot", "executed_by", "destination_location")


@extend_schema_view(
    get=extend_schema(
        summary="Listar despachos",
        description="Lista los despachos registrados en el ledger.",
        responses={
            200: MovementSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Registrar despacho",
        description="Registra un nuevo despacho de inventario (venta menor, venta mayor, daño o vencimiento).",
        request=DispatchCreateSerializer,
        responses={
            201: MovementSerializer,
            **standard_error_responses(include_403=True, include_409=True),
        },
    ),
)
class DispatchListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)
    pagination_class = ICMPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DispatchCreateSerializer
        return MovementSerializer

    def get_queryset(self):
        salidas = (
            MovementType.SALIDA_VENTA_MAYOR,
            MovementType.SALIDA_VENTA_MENOR,
            MovementType.SALIDA_DANO,
            MovementType.SALIDA_VENCIMIENTO,
        )
        return (
            Movement.objects.filter(movement_type__in=salidas)
            .select_related("product", "executed_by", "origin_location")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_dispatch(
            request.user,
            d["product_id"],
            d["location_id"],
            d["quantity"],
            d["movement_type"],
            lot_id=d.get("lot_id"),
            scanned_code=d.get("scanned_code"),
            order_sku=d.get("order_sku"),
            serial_id=d.get("serial_id"),
            customer_data=d.get("customer_data"),
            note=d.get("note"),
            cold_chain_acknowledged=d.get("cold_chain_acknowledged", False),
            electrical_safety_acknowledged=d.get(
                "electrical_safety_acknowledged", False
            ),
            privacy_notice_acknowledged=d.get("privacy_notice_acknowledged", False),
            discount_pct=d.get("discount_pct"),
        )
        # register_dispatch may return one Movement or a list of Movements
        if isinstance(movement, (list, tuple)):
            # backward-compat: if it's a single-item list, return an object
            if len(movement) == 1:
                data = MovementSerializer(movement[0]).data
            else:
                data = MovementSerializer(movement, many=True).data
        else:
            data = MovementSerializer(movement).data
        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de despacho",
        description="Obtiene el detalle de un despacho registrado.",
        responses={
            200: MovementSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
)
class DispatchDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MovementSerializer

    def get_queryset(self):
        salidas = (
            MovementType.SALIDA_VENTA_MAYOR,
            MovementType.SALIDA_VENTA_MENOR,
            MovementType.SALIDA_DANO,
            MovementType.SALIDA_VENCIMIENTO,
        )
        return Movement.objects.filter(movement_type__in=salidas).select_related(
            "product", "executed_by", "origin_location"
        )


class DispatchInvoiceDownloadView(APIView):
    """BR-13 — Descarga del PDF de factura asociado al despacho."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(
        summary="Descargar PDF de factura",
        description="Descarga el PDF de factura asociado a un despacho.",
        responses={
            200: None,
            **standard_error_responses(include_404=True),
        },
    )
    def get(self, request, pk):
        salidas = (
            MovementType.SALIDA_VENTA_MAYOR,
            MovementType.SALIDA_VENTA_MENOR,
            MovementType.SALIDA_DANO,
            MovementType.SALIDA_VENCIMIENTO,
        )
        movement = Movement.objects.filter(pk=pk, movement_type__in=salidas).first()
        if not movement or not movement.invoice_pdf:
            from django.http import Http404

            raise Http404("Factura no disponible.")
        return FileResponse(
            movement.invoice_pdf.open("rb"),
            as_attachment=True,
            filename=movement.invoice_pdf.name.split("/")[-1],
        )


@extend_schema_view(
    get=extend_schema(
        summary="Listar traslados",
        description="Lista los traslados internos registrados.",
        responses={
            200: MovementSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Registrar traslado",
        description="Registra un traslado interno entre ubicaciones.",
        request=TransferCreateSerializer,
        responses={
            201: MovementSerializer,
            **standard_error_responses(include_403=True, include_409=True),
        },
    ),
)
class TransferListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)
    pagination_class = ICMPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TransferCreateSerializer
        return MovementSerializer

    def get_queryset(self):
        return (
            Movement.objects.filter(movement_type=MovementType.TRASLADO)
            .select_related(
                "product", "executed_by", "origin_location", "destination_location"
            )
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_internal_transfer(
            request.user,
            d["product_id"],
            d["origin_id"],
            d["destination_id"],
            d["quantity"],
            lot_id=d.get("lot_id"),
            serial_id=d.get("serial_id"),
            cold_chain_acknowledged=d.get("cold_chain_acknowledged", False),
            electrical_safety_acknowledged=d.get(
                "electrical_safety_acknowledged", False
            ),
        )
        return Response(
            MovementSerializer(movement).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        summary="Listar devoluciones",
        description="Lista las devoluciones registradas en el ledger.",
        responses={
            200: MovementSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Registrar devolución",
        description="Registra una devolución de inventario.",
        request=ReturnCreateSerializer,
        responses={
            201: MovementSerializer,
            **standard_error_responses(include_403=True, include_409=True),
        },
    ),
)
class ReturnListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    pagination_class = ICMPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReturnCreateSerializer
        return MovementSerializer

    def get_queryset(self):
        return (
            Movement.objects.filter(movement_type=MovementType.DEVOLUCION)
            .select_related("product", "executed_by", "destination_location")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_return(
            request.user,
            d["product_id"],
            d["location_id"],
            d["quantity"],
            lot_id=d.get("lot_id"),
            serial_id=d.get("serial_id"),
            related_movement_id=d.get("related_movement_id"),
        )
        return Response(
            MovementSerializer(movement).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        summary="Listar ajustes",
        description="Lista los ajustes de inventario registrados.",
        responses={
            200: MovementSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Registrar ajuste",
        description="Registra un ajuste de inventario.",
        request=AdjustmentCreateSerializer,
        responses={
            201: MovementSerializer,
            **standard_error_responses(include_403=True, include_409=True),
        },
    ),
)
class AdjustmentListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    pagination_class = ICMPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdjustmentCreateSerializer
        return MovementSerializer

    def get_queryset(self):
        return (
            Movement.objects.filter(movement_type=MovementType.AJUSTE)
            .select_related(
                "product", "executed_by", "origin_location", "destination_location"
            )
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_adjustment(
            request.user,
            d["product_id"],
            d["location_id"],
            d["new_quantity"],
            d["justification"],
            serial_id=d.get("serial_id"),
        )
        return Response(
            MovementSerializer(movement).data, status=status.HTTP_201_CREATED
        )


class AdjustmentCorrectView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(
        summary="Corregir ajuste dentro de ventana de tiempo",
        description="Corrige un ajuste dentro de la ventana permitida por la regla de negocio.",
        request=AdjustmentCorrectionSerializer,
        responses={
            201: MovementSerializer(many=True),
            **standard_error_responses(
                include_403=True, include_404=True, include_405=True, include_409=True
            ),
        },
    )
    def post(self, request):
        ser = AdjustmentCorrectionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = dict(ser.validated_data)
        mid = d.pop("movement_id")
        movements = correct_movement_within_window(request.user, mid, d)
        return Response(
            MovementSerializer(movements, many=True).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de movimiento",
        description="Obtiene el detalle de un movimiento del ledger.",
        responses={
            200: MovementSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
)
class MovementDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Movement.objects.select_related("product", "executed_by")
    serializer_class = MovementSerializer

    def http_method_not_allowed(self, request, *args, **kwargs):
        log_immutable_modification_attempt(
            user=(
                request.user
                if getattr(request.user, "is_authenticated", False)
                else None
            ),
            request=request,
            detail={"resource": "movement", "movement_id": str(kwargs.get("pk") or "")},
        )
        raise ImmutableRecordError()


class MovementCorrectionView(APIView):
    """Corrección por id de movimiento en URL (compatibilidad)."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(
        summary="Corrección de movimiento (URL)",
        description="Corrige un movimiento usando su identificador en la URL.",
        request=CorrectionCreateSerializer,
        responses={
            201: MovementSerializer(many=True),
            **standard_error_responses(
                include_403=True, include_404=True, include_405=True, include_409=True
            ),
        },
    )
    def post(self, request, pk):
        ser = CorrectionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        movements = correct_movement_within_window(request.user, pk, ser.validated_data)
        return Response(
            MovementSerializer(movements, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class ComboDispatchView(APIView):
    """RF-003, Opción B — Despacha un combo completo descontando stock por ítem."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(
        summary="Despachar combo (descuenta stock por ítem)",
        description="Despacha un combo completo y descuenta stock por cada ítem.",
        request=ComboDispatchSerializer,
        tags=[TAG_MOVEMENTS],
        responses={
            201: MovementSerializer(many=True),
            **standard_error_responses(
                include_403=True, include_404=True, include_409=True
            ),
        },
    )
    def post(self, request):
        from apps.catalog.models import ProductCombo

        ser = ComboDispatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            movements = dispatch_combo(
                request.user,
                d["combo_id"],
                d["location_id"],
                serial_id=d.get("serial_id"),
                request=request,
            )
        except ProductCombo.DoesNotExist:
            return Response(
                {"detail": "Combo no encontrado o inactivo."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            MovementSerializer(movements, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class InvoiceDetailView(APIView):
    """GET /movements/invoices/<number>/ — detalle de factura con totales y movements."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(
        summary="Detalle de factura comercial",
        description="Retorna el detalle de una factura por número, incluyendo totales y lista de movimientos asociados.",
        responses={
            200: InvoiceSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_MOVEMENTS],
    )
    def get(self, request, number):
        from django.shortcuts import get_object_or_404

        invoice = get_object_or_404(
            Invoice.objects.prefetch_related("movements"), number=number
        )
        return Response(InvoiceSerializer(invoice).data)


class InvoicePDFDownloadView(APIView):
    """GET /movements/invoices/<number>/pdf/ — descarga el PDF enriquecido de la factura."""

    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(
        summary="Descargar PDF de factura comercial",
        description="Descarga el PDF de la factura con todos los datos del despacho, precios e información del cliente.",
        responses={
            200: None,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_MOVEMENTS],
    )
    def get(self, request, number):
        from django.http import Http404
        from django.shortcuts import get_object_or_404

        invoice = get_object_or_404(Invoice, number=number)
        if not invoice.pdf:
            raise Http404("PDF no disponible para esta factura.")
        return FileResponse(
            invoice.pdf.open("rb"),
            as_attachment=True,
            filename=f"{invoice.number}.pdf",
        )
