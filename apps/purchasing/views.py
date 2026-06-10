"""Endpoints REST del módulo de compras."""

from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.openapi import TAG_PURCHASING, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista, IsWithinOperatingHours

from . import selectors, services
from .permissions import IsPurchasingViewer
from .serializers import (
    POCancelSerializer,
    PurchaseOrderCreateSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderUpdateSerializer,
    ReceptionCreateSerializer,
    ReceptionSerializer,
    SupplierSerializer,
    SupplierWriteSerializer,
)

_PERMS_OPERATOR = [IsAuthenticated, IsWithinOperatingHours, IsAlmacenista]
_PERMS_VIEWER = [IsAuthenticated, IsWithinOperatingHours, IsPurchasingViewer]


# ---------------------------------------------------------------------------
# Supplier views
# ---------------------------------------------------------------------------


@extend_schema(tags=[TAG_PURCHASING])
class SupplierListCreateView(APIView):
    pagination_class = ICMPageNumberPagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [p() for p in _PERMS_VIEWER]
        return [p() for p in _PERMS_OPERATOR]

    @extend_schema(
        summary="Listar proveedores", responses={200: SupplierSerializer(many=True)}
    )
    def get(self, request):
        is_active_param = request.query_params.get("is_active")
        is_active = None
        if is_active_param is not None:
            is_active = is_active_param.lower() in ("true", "1", "yes")
        qs = selectors.get_suppliers(is_active=is_active)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                SupplierSerializer(page, many=True).data
            )
        return Response(SupplierSerializer(qs, many=True).data)

    @extend_schema(
        summary="Crear proveedor",
        request=SupplierWriteSerializer,
        responses={
            201: SupplierSerializer,
            **standard_error_responses(include_422=True),
        },
    )
    def post(self, request):
        serializer = SupplierWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = services.create_supplier(
            request.user, serializer.validated_data, request=request
        )
        return Response(
            SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=[TAG_PURCHASING])
class SupplierDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [p() for p in _PERMS_VIEWER]
        return [p() for p in _PERMS_OPERATOR]

    @extend_schema(summary="Detalle de proveedor", responses={200: SupplierSerializer})
    def get(self, request, pk: UUID):
        supplier = selectors.get_supplier(pk)
        return Response(SupplierSerializer(supplier).data)

    @extend_schema(
        summary="Actualizar proveedor (completo)",
        request=SupplierWriteSerializer,
        responses={
            200: SupplierSerializer,
            **standard_error_responses(include_422=True),
        },
    )
    def put(self, request, pk: UUID):
        serializer = SupplierWriteSerializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        supplier = services.update_supplier(
            request.user, pk, serializer.validated_data, request=request
        )
        return Response(SupplierSerializer(supplier).data)

    @extend_schema(
        summary="Actualizar proveedor (parcial)",
        request=SupplierWriteSerializer,
        responses={
            200: SupplierSerializer,
            **standard_error_responses(include_422=True),
        },
    )
    def patch(self, request, pk: UUID):
        serializer = SupplierWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = services.update_supplier(
            request.user, pk, serializer.validated_data, request=request
        )
        return Response(SupplierSerializer(supplier).data)

    @extend_schema(
        summary="Desactivar proveedor (soft delete)",
        description=(
            "Marca el proveedor como inactivo (is_active=False). "
            "El registro NO se elimina de la base de datos. "
            "Para reactivar, use POST /suppliers/{id}/activate/."
        ),
        responses={204: None, **standard_error_responses(include_404=True)},
    )
    def delete(self, request, pk: UUID):
        services.deactivate_supplier(request.user, pk, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=[TAG_PURCHASING])
class SupplierDeactivateView(APIView):
    permission_classes = _PERMS_OPERATOR

    @extend_schema(summary="Desactivar proveedor", responses={200: SupplierSerializer})
    def post(self, request, pk: UUID):
        supplier = services.deactivate_supplier(request.user, pk, request=request)
        return Response(SupplierSerializer(supplier).data)


@extend_schema(tags=[TAG_PURCHASING])
class SupplierActivateView(APIView):
    permission_classes = _PERMS_OPERATOR

    @extend_schema(summary="Reactivar proveedor", responses={200: SupplierSerializer})
    def post(self, request, pk: UUID):
        supplier = services.activate_supplier(request.user, pk, request=request)
        return Response(SupplierSerializer(supplier).data)


# ---------------------------------------------------------------------------
# PurchaseOrder views
# ---------------------------------------------------------------------------


@extend_schema(tags=[TAG_PURCHASING])
class PurchaseOrderListCreateView(APIView):
    pagination_class = ICMPageNumberPagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [p() for p in _PERMS_VIEWER]
        return [p() for p in _PERMS_OPERATOR]

    @extend_schema(
        summary="Listar órdenes de compra",
        responses={200: PurchaseOrderSerializer(many=True)},
    )
    def get(self, request):
        qs = selectors.get_purchase_orders(
            status=request.query_params.get("status"),
            supplier_id=request.query_params.get("supplier_id"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                PurchaseOrderSerializer(page, many=True).data
            )
        return Response(PurchaseOrderSerializer(qs, many=True).data)

    @extend_schema(
        summary="Crear orden de compra",
        request=PurchaseOrderCreateSerializer,
        responses={
            201: PurchaseOrderSerializer,
            **standard_error_responses(include_422=True),
        },
    )
    def post(self, request):
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = services.create_purchase_order(
            request.user, serializer.validated_data, request=request
        )
        return Response(
            PurchaseOrderSerializer(selectors.get_purchase_order(po.id)).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=[TAG_PURCHASING])
class PurchaseOrderDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [p() for p in _PERMS_VIEWER]
        return [p() for p in _PERMS_OPERATOR]

    @extend_schema(summary="Detalle de OC", responses={200: PurchaseOrderSerializer})
    def get(self, request, pk: UUID):
        po = selectors.get_purchase_order(pk)
        return Response(PurchaseOrderSerializer(po).data)

    @extend_schema(
        summary="Actualizar OC (completo, solo BORRADOR)",
        request=PurchaseOrderUpdateSerializer,
        responses={
            200: PurchaseOrderSerializer,
            **standard_error_responses(include_405=True, include_422=True),
        },
    )
    def put(self, request, pk: UUID):
        serializer = PurchaseOrderUpdateSerializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        po = services.update_purchase_order(
            request.user, pk, serializer.validated_data, request=request
        )
        return Response(
            PurchaseOrderSerializer(selectors.get_purchase_order(po.id)).data
        )

    @extend_schema(
        summary="Actualizar OC (parcial, solo BORRADOR)",
        request=PurchaseOrderUpdateSerializer,
        responses={
            200: PurchaseOrderSerializer,
            **standard_error_responses(include_405=True, include_422=True),
        },
    )
    def patch(self, request, pk: UUID):
        serializer = PurchaseOrderUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        po = services.update_purchase_order(
            request.user, pk, serializer.validated_data, request=request
        )
        return Response(
            PurchaseOrderSerializer(selectors.get_purchase_order(po.id)).data
        )


@extend_schema(tags=[TAG_PURCHASING])
class PurchaseOrderConfirmView(APIView):
    permission_classes = _PERMS_OPERATOR

    @extend_schema(
        summary="Confirmar OC (BORRADOR → PENDIENTE)",
        responses={
            200: PurchaseOrderSerializer,
            **standard_error_responses(include_422=True),
        },
    )
    def post(self, request, pk: UUID):
        po = services.confirm_purchase_order(request.user, pk, request=request)
        return Response(
            PurchaseOrderSerializer(selectors.get_purchase_order(po.id)).data
        )


@extend_schema(tags=[TAG_PURCHASING])
class PurchaseOrderCancelView(APIView):
    permission_classes = _PERMS_OPERATOR

    @extend_schema(
        summary="Cancelar OC",
        request=POCancelSerializer,
        responses={
            200: PurchaseOrderSerializer,
            **standard_error_responses(include_409=True, include_422=True),
        },
    )
    def post(self, request, pk: UUID):
        serializer = POCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = services.cancel_purchase_order(
            request.user, pk, serializer.validated_data["reason"], request=request
        )
        return Response(
            PurchaseOrderSerializer(selectors.get_purchase_order(po.id)).data
        )


# ---------------------------------------------------------------------------
# Reception views
# ---------------------------------------------------------------------------


@extend_schema(tags=[TAG_PURCHASING])
class ReceptionListCreateView(APIView):
    pagination_class = ICMPageNumberPagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [p() for p in _PERMS_VIEWER]
        return [p() for p in _PERMS_OPERATOR]

    @extend_schema(
        summary="Listar recepciones",
        responses={200: ReceptionSerializer(many=True)},
    )
    def get(self, request):
        qs = selectors.get_receptions(
            po_id=request.query_params.get("po_id"),
            status=request.query_params.get("status"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                ReceptionSerializer(page, many=True).data
            )
        return Response(ReceptionSerializer(qs, many=True).data)

    @extend_schema(
        summary="Crear recepción en BORRADOR",
        request=ReceptionCreateSerializer,
        responses={
            201: ReceptionSerializer,
            **standard_error_responses(include_409=True, include_422=True),
        },
    )
    def post(self, request):
        serializer = ReceptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        reception = services.create_reception(
            request.user,
            data["po_id"],
            {
                "destination_location_id": data["destination_location_id"],
                "notes": data.get("notes", ""),
                "items": [
                    {
                        "purchase_order_item_id": item["purchase_order_item_id"],
                        "quantity_received": item["quantity_received"],
                        "lot_code": item.get("lot_code", ""),
                        "lot_expiration_date": item.get("lot_expiration_date"),
                        "discrepancy_note": item.get("discrepancy_note", ""),
                        "allocations": [
                            {
                                "location_id": allocation["location_id"],
                                "quantity_received": allocation["quantity_received"],
                                "lot_code": allocation.get("lot_code", ""),
                                "lot_expiration_date": allocation.get(
                                    "lot_expiration_date"
                                ),
                            }
                            for allocation in item.get("allocations", [])
                        ],
                    }
                    for item in data.get("items", [])
                ],
            },
            request=request,
        )
        return Response(
            ReceptionSerializer(selectors.get_reception(reception.id)).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=[TAG_PURCHASING])
class ReceptionDetailView(APIView):
    permission_classes = _PERMS_VIEWER

    @extend_schema(summary="Detalle de recepción", responses={200: ReceptionSerializer})
    def get(self, request, pk: UUID):
        reception = selectors.get_reception(pk)
        return Response(ReceptionSerializer(reception).data)


@extend_schema(tags=[TAG_PURCHASING])
class ReceptionConfirmView(APIView):
    permission_classes = _PERMS_OPERATOR

    @extend_schema(
        summary="Confirmar recepción (genera Movements de ENTRADA)",
        responses={
            200: ReceptionSerializer,
            **standard_error_responses(
                include_405=True, include_409=True, include_422=True
            ),
        },
    )
    def post(self, request, pk: UUID):
        reception = services.confirm_reception(request.user, pk, request=request)
        return Response(ReceptionSerializer(selectors.get_reception(reception.id)).data)


@extend_schema(tags=[TAG_PURCHASING])
class ReceptionCancelView(APIView):
    permission_classes = _PERMS_OPERATOR

    @extend_schema(
        summary="Cancelar recepción (solo BORRADOR)",
        responses={
            200: ReceptionSerializer,
            **standard_error_responses(include_405=True),
        },
    )
    def post(self, request, pk: UUID):
        reception = services.cancel_reception(request.user, pk, request=request)
        return Response(ReceptionSerializer(selectors.get_reception(reception.id)).data)
