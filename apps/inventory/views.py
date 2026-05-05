"""Vistas de inventario (RF-004)."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Location
from apps.inventory.selectors import get_full_inventory, get_stock_by_location, get_stock_by_product, search_products
from apps.inventory.serializers import (
    LocationSerializer,
    PaginatedProductListSerializer,
    PaginatedStockByLocationListSerializer,
    ProductSerializer,
    StockByLocationSerializer,
    StockByProductResponseSerializer,
    StockReconstructRequestSerializer,
    StockReconstructResponseSerializer,
)
from apps.inventory.services import (
    create_location,
    deactivate_location,
    trigger_stock_reconstruction,
    update_location,
)
from shared.openapi import TAG_INVENTORY
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


class InventoryFullListView(APIView):
    """GET — Inventario consolidado por producto (RF-004)."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="category_id", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="location_id", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="only_in_stock", type=bool, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="stock_below_reorder", type=bool, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={
            200: OpenApiResponse(description="Inventario listado exitosamente."),
            400: OpenApiResponse(description="Parámetros de filtro inválidos."),
            401: OpenApiResponse(description="No autenticado."),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        filters: dict = {}
        if cid := request.query_params.get("category_id"):
            filters["category_id"] = UUID(str(cid))
        if lid := request.query_params.get("location_id"):
            filters["location_id"] = UUID(str(lid))
        if request.query_params.get("only_in_stock", "").lower() in ("1", "true", "yes"):
            filters["only_in_stock"] = True
        if request.query_params.get("stock_below_reorder", "").lower() in ("1", "true", "yes"):
            filters["stock_below_reorder"] = True
        data = get_full_inventory(filters)
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(data, request, view=self)
        return paginator.get_paginated_response(page)


class LocationListCreateView(APIView):
    """GET/POST ubicaciones (RF-004)."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated()]

    @extend_schema(
        responses={
            200: LocationSerializer(many=True),
            401: OpenApiResponse(description="No autenticado."),
        }, 
        tags=[TAG_INVENTORY]
    )
    def get(self, request):
        data = LocationSerializer(Location.objects.all().order_by("code"), many=True).data
        return Response(data)

    @extend_schema(
        request=LocationSerializer,
        responses={
            201: LocationSerializer,
            400: OpenApiResponse(description="Datos de ubicación inválidos."),
            401: OpenApiResponse(description="No autenticado."),
            403: OpenApiResponse(description="Permiso denegado (solo almacenista puede crear)."),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = LocationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        loc = create_location(
            request.user,
            code=ser.validated_data["code"],
            name=ser.validated_data["name"],
            description=ser.validated_data.get("description", ""),
            is_retail=ser.validated_data.get("is_retail", False),
        )
        return Response(LocationSerializer(loc).data, status=status.HTTP_201_CREATED)


class LocationDetailView(APIView):
    """GET/PATCH/DELETE(soft) ubicación por id (RF-004)."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        responses={
            200: LocationSerializer,
            401: OpenApiResponse(description="No autenticado."),
            404: OpenApiResponse(description="Ubicación no encontrada."),
        }, 
        tags=[TAG_INVENTORY]
    )
    def get(self, request, pk):
        loc = get_object_or_404(Location, pk=pk)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        request=LocationSerializer, 
        responses={
            200: LocationSerializer,
            400: OpenApiResponse(description="Datos de ubicación inválidos."),
            401: OpenApiResponse(description="No autenticado."),
            403: OpenApiResponse(description="Permiso denegado (solo almacenista puede modificar)."),
            404: OpenApiResponse(description="Ubicación no encontrada."),
        }, 
        tags=[TAG_INVENTORY]
    )
    def patch(self, request, pk):
        ser = LocationSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        loc = update_location(request.user, UUID(str(pk)), ser.validated_data)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Ubicación desactivada exitosamente."),
            401: OpenApiResponse(description="No autenticado."),
            403: OpenApiResponse(description="Permiso denegado (solo almacenista puede desactivar)."),
            404: OpenApiResponse(description="Ubicación no encontrada."),
        }, 
        tags=[TAG_INVENTORY]
    )
    def delete(self, request, pk):
        deactivate_location(request.user, UUID(str(pk)))
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockByProductView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: StockByProductResponseSerializer,
            400: OpenApiResponse(description="Identificador de producto inválido."),
            401: OpenApiResponse(description="No autenticado."),
            404: OpenApiResponse(description="Producto no encontrado."),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, product_id):
        return Response(get_stock_by_product(UUID(str(product_id))))


class StockByLocationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: PaginatedStockByLocationListSerializer,
            400: OpenApiResponse(description="Identificador de ubicación inválido."),
            401: OpenApiResponse(description="No autenticado."),
            404: OpenApiResponse(description="Ubicación no encontrada."),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, location_id):
        qs = get_stock_by_location(UUID(str(location_id)))
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        ser = StockByLocationSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class ReconstructStockView(APIView):
    """POST — Reconstrucción ledger vs stock derivado (solo almacenista)."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        request=StockReconstructRequestSerializer,
        responses={
            200: StockReconstructResponseSerializer,
            400: OpenApiResponse(description="Parámetros de reconstrucción inválidos."),
            401: OpenApiResponse(description="No autenticado."),
            403: OpenApiResponse(description="Permiso denegado (solo almacenista)."),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StockReconstructRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        result = trigger_stock_reconstruction(request.user, d["product_id"], d["location_id"])
        return Response(result, status=status.HTTP_200_OK)


class ProductSearchView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Texto para SKU, código de barras o nombre.",
            ),
            OpenApiParameter(name="category", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="subcategory", type=str, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={
            200: PaginatedProductListSerializer,
            400: OpenApiResponse(description="Parámetros de búsqueda inválidos."),
            401: OpenApiResponse(description="No autenticado."),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        q = request.query_params.get("q", "")
        category = request.query_params.get("category")
        subcategory = request.query_params.get("subcategory")
        qs = search_products(
            q,
            category_id=UUID(category) if category else None,
            subcategory_id=UUID(subcategory) if subcategory else None,
        )
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        ser = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)
