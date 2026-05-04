"""Vistas del ledger (RF-005–RF-009)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.movements.models import Movement
from apps.movements.serializers import (
    AdjustmentCreateSerializer,
    CorrectionCreateSerializer,
    DispatchCreateSerializer,
    EntryCreateSerializer,
    MovementSerializer,
    ReturnApproveSerializer,
    ReturnCreateSerializer,
    ReturnRejectSerializer,
    TransferCreateSerializer,
)
from apps.movements.services import (
    approve_return,
    correct_movement_within_window,
    register_adjustment,
    register_dispatch,
    register_entry,
    register_internal_transfer,
    register_return,
    reject_return,
)
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista, IsAlmacenistaOrAuxiliar


@extend_schema_view(
    get=extend_schema(summary="Listar movimientos", responses={200: MovementSerializer(many=True)}),
)
class MovementListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MovementSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = Movement.objects.select_related("product", "executed_by").all().order_by("-created_at")
        product = self.request.query_params.get("product_id")
        movement_type = self.request.query_params.get("movement_type")
        if product:
            qs = qs.filter(product_id=product)
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        return qs


@extend_schema_view(
    get=extend_schema(summary="Detalle de movimiento", responses={200: MovementSerializer}),
)
class MovementDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Movement.objects.select_related("product", "executed_by")
    serializer_class = MovementSerializer


class EntryCreateView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(request=EntryCreateSerializer, responses=MovementSerializer)
    def post(self, request):
        ser = EntryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_entry(
            request.user,
            d["product_id"],
            d["location_id"],
            d["quantity"],
            serial_number=d.get("serial_number"),
            qty_invoiced=d.get("qty_invoiced"),
            discrepancy_note=d.get("discrepancy_note"),
            cold_chain_acknowledged=d.get("cold_chain_acknowledged", False),
            electrical_safety_acknowledged=d.get("electrical_safety_acknowledged", False),
        )
        return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class DispatchCreateView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(request=DispatchCreateSerializer, responses=MovementSerializer)
    def post(self, request):
        ser = DispatchCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_dispatch(
            request.user,
            d["product_id"],
            d["location_id"],
            d["quantity"],
            d["movement_type"],
            scanned_code=d["scanned_code"],
            order_sku=d["order_sku"],
            customer_data=d.get("customer_data"),
            note=d.get("note"),
            cold_chain_acknowledged=d.get("cold_chain_acknowledged", False),
            electrical_safety_acknowledged=d.get("electrical_safety_acknowledged", False),
            privacy_notice_acknowledged=d.get("privacy_notice_acknowledged", False),
        )
        return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class TransferCreateView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(request=TransferCreateSerializer, responses=MovementSerializer)
    def post(self, request):
        ser = TransferCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_internal_transfer(
            request.user,
            d["product_id"],
            d["origin_id"],
            d["destination_id"],
            d["quantity"],
            cold_chain_acknowledged=d.get("cold_chain_acknowledged", False),
            electrical_safety_acknowledged=d.get("electrical_safety_acknowledged", False),
        )
        return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class ReturnCreateView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(request=ReturnCreateSerializer, responses=MovementSerializer)
    def post(self, request):
        ser = ReturnCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_return(
            request.user,
            d["product_id"],
            d["serial_number"],
            d["reason"],
            d["product_condition"],
        )
        return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class ReturnApproveView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(request=ReturnApproveSerializer, responses=MovementSerializer)
    def post(self, request, pk):
        ser = ReturnApproveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        movement = approve_return(request.user, pk, ser.validated_data["destination_location_id"])
        return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class ReturnRejectView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(request=ReturnRejectSerializer, responses={204: None})
    def post(self, request, pk):
        ser = ReturnRejectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reject_return(request.user, pk, ser.validated_data["reason"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdjustmentCreateView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(request=AdjustmentCreateSerializer, responses=MovementSerializer)
    def post(self, request):
        ser = AdjustmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        movement = register_adjustment(
            request.user,
            d["product_id"],
            d["location_id"],
            d["new_quantity"],
            d["justification"],
        )
        return Response(MovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class MovementCorrectionView(APIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrAuxiliar)

    @extend_schema(request=CorrectionCreateSerializer, responses=MovementSerializer(many=True))
    def post(self, request, pk):
        ser = CorrectionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        movements = correct_movement_within_window(request.user, pk, ser.validated_data)
        return Response(MovementSerializer(movements, many=True).data, status=status.HTTP_201_CREATED)
