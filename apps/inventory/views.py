"""Vistas de inventario (RF-004)."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Location
from apps.inventory.selectors import (
    get_full_inventory,
    get_stock_by_location,
    get_stock_by_product,
    search_products,
)
from apps.inventory.serializers import (
    LocationCreateSerializer,
    LocationSerializer,
    LocationStateTransitionSerializer,
    PaginatedProductListSerializer,
    PaginatedStockByLocationListSerializer,
    ProductSerializer,
    StorageTypeCreateSerializer,
    StorageTemplateCreateSerializer,
    StorageTemplateSerializer,
    StorageTypeSerializer,
    StockByLocationSerializer,
    StockByProductResponseSerializer,
    StockReconstructRequestSerializer,
    StockReconstructResponseSerializer,
)
from apps.inventory.services import (
    create_storage_template,
    create_storage_type,
    create_location,
    deactivate_storage_template,
    deactivate_storage_type,
    deactivate_location,
    transition_location_state,
    trigger_stock_reconstruction,
    update_storage_template,
    update_storage_type,
    update_location,
)
from shared.openapi import TAG_INVENTORY, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


class InventoryFullListView(APIView):
    """GET — Inventario consolidado por producto (RF-004)."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="location_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="storage_type_id",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra productos con stock en ubicaciones del tipo dado.",
            ),
            OpenApiParameter(
                name="operational_status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra productos con stock en ubicaciones con este estado operativo.",
            ),
            OpenApiParameter(
                name="only_in_stock",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="stock_below_reorder",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Inventario listado exitosamente."),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        filters: dict = {}
        if cid := request.query_params.get("category_id"):
            filters["category_id"] = UUID(str(cid))
        if lid := request.query_params.get("location_id"):
            filters["location_id"] = UUID(str(lid))
        if stid := request.query_params.get("storage_type_id"):
            filters["storage_type_id"] = UUID(str(stid))
        if os_val := request.query_params.get("operational_status"):
            filters["operational_status"] = str(os_val)
        if request.query_params.get("only_in_stock", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            filters["only_in_stock"] = True
        if request.query_params.get("stock_below_reorder", "").lower() in (
            "1",
            "true",
            "yes",
        ):
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
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        data = LocationSerializer(
            Location.objects.all().order_by("code"), many=True
        ).data
        return Response(data)

    @extend_schema(
        request=LocationCreateSerializer,
        responses={
            201: LocationSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = LocationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        loc = create_location(
            request.user,
            name=d["name"],
            description=d.get("description", ""),
            is_retail=d.get("is_retail", None),
            max_capacity=d.get("max_capacity", None),
            storage_type_id=d.get("storage_type_id"),
            storage_template_id=d.get("storage_template_id"),
            operational_status=d.get("operational_status", Location.OperationalStatus.ACTIVE),
            capacity_mode=d.get("capacity_mode", Location.CapacityMode.NONE),
            capacity_level=d.get("capacity_level"),
            capacity_score=d.get("capacity_score"),
            occupancy_estimate_pct=d.get("occupancy_estimate_pct"),
        )
        return Response(LocationSerializer(loc).data, status=status.HTTP_201_CREATED)


class StorageTemplateListCreateView(APIView):
    """GET/POST plantillas de almacenamiento."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated()]

    @extend_schema(
        responses={
            200: StorageTemplateSerializer(many=True),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        from apps.inventory.models import StorageTemplate

        data = StorageTemplateSerializer(
            StorageTemplate.objects.select_related("storage_type").order_by(
                "sort_order", "name"
            ),
            many=True,
        ).data
        return Response(data)

    @extend_schema(
        request=StorageTemplateCreateSerializer,
        responses={
            201: StorageTemplateSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StorageTemplateCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        template = create_storage_template(request.user, **ser.validated_data)
        return Response(
            StorageTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED,
        )


class StorageTemplateDetailView(APIView):
    """GET/PATCH/DELETE(soft) plantilla de almacenamiento por id."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        responses={
            200: StorageTemplateSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, pk):
        from apps.inventory.models import StorageTemplate

        template = get_object_or_404(StorageTemplate, pk=pk)
        return Response(StorageTemplateSerializer(template).data)

    @extend_schema(
        request=StorageTemplateCreateSerializer,
        responses={
            200: StorageTemplateSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        ser = StorageTemplateCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        template = update_storage_template(request.user, UUID(str(pk)), ser.validated_data)
        return Response(StorageTemplateSerializer(template).data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Plantilla de almacenamiento desactivada."),
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def delete(self, request, pk):
        deactivate_storage_template(request.user, UUID(str(pk)))
        return Response(status=status.HTTP_204_NO_CONTENT)


class StorageTypeListCreateView(APIView):
    """GET/POST tipos de almacenamiento."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAlmacenista()]
        return [IsAuthenticated()]

    @extend_schema(
        responses={
            200: StorageTypeSerializer(many=True),
            **standard_error_responses(),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        from apps.inventory.models import StorageType

        data = StorageTypeSerializer(
            StorageType.objects.all().order_by("sort_order", "name"), many=True
        ).data
        return Response(data)

    @extend_schema(
        request=StorageTypeCreateSerializer,
        responses={
            201: StorageTypeSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StorageTypeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        st = create_storage_type(request.user, **ser.validated_data)
        return Response(StorageTypeSerializer(st).data, status=status.HTTP_201_CREATED)


class StorageTypeDetailView(APIView):
    """GET/PATCH/DELETE(soft) tipo de almacenamiento por id."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, pk):
        from apps.inventory.models import StorageType

        st = get_object_or_404(StorageType, pk=pk)
        return Response(StorageTypeSerializer(st).data)

    @extend_schema(
        request=StorageTypeCreateSerializer,
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def put(self, request, pk):
        ser = StorageTypeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        st = update_storage_type(request.user, UUID(str(pk)), ser.validated_data)
        return Response(StorageTypeSerializer(st).data)

    @extend_schema(
        request=StorageTypeCreateSerializer,
        responses={
            200: StorageTypeSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        ser = StorageTypeCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        st = update_storage_type(request.user, UUID(str(pk)), ser.validated_data)
        return Response(StorageTypeSerializer(st).data)

    @extend_schema(
        responses={
            204: OpenApiResponse(
                description="Tipo de almacenamiento desactivado exitosamente."
            ),
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def delete(self, request, pk):
        deactivate_storage_type(request.user, UUID(str(pk)))
        return Response(status=status.HTTP_204_NO_CONTENT)


class LocationDetailView(APIView):
    """GET/PATCH/DELETE(soft) ubicación por id (RF-004)."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAlmacenista()]

    @extend_schema(
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def get(self, request, pk):
        loc = get_object_or_404(Location, pk=pk)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        request=LocationSerializer,
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def put(self, request, pk):
        ser = LocationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        loc = update_location(request.user, UUID(str(pk)), ser.validated_data)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        request=LocationSerializer,
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def patch(self, request, pk):
        ser = LocationSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        loc = update_location(request.user, UUID(str(pk)), ser.validated_data)
        return Response(LocationSerializer(loc).data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Ubicación desactivada exitosamente."),
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def delete(self, request, pk):
        deactivate_location(request.user, UUID(str(pk)))
        return Response(status=status.HTTP_204_NO_CONTENT)


class LocationStateTransitionView(APIView):
    """POST transición formal de estado operativo para una ubicación."""

    permission_classes = (IsAuthenticated, IsAlmacenista)

    @extend_schema(
        request=LocationStateTransitionSerializer,
        responses={
            200: LocationSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request, pk):
        ser = LocationStateTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        loc = transition_location_state(
            request.user,
            UUID(str(pk)),
            ser.validated_data["operational_status"],
        )
        return Response(LocationSerializer(loc).data, status=status.HTTP_200_OK)


class StockByProductView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: StockByProductResponseSerializer,
            **standard_error_responses(include_404=True),
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
            **standard_error_responses(include_404=True),
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
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_INVENTORY],
    )
    def post(self, request):
        ser = StockReconstructRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        result = trigger_stock_reconstruction(
            request.user, d["product_id"], d["location_id"]
        )
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
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="subcategory",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            200: PaginatedProductListSerializer,
            **standard_error_responses(),
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
