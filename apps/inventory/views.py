"""Vistas de inventario (RF-004)."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Location
from apps.inventory.selectors import get_stock_by_location, get_stock_by_product, search_products
from apps.inventory.serializers import (
    LocationSerializer,
    PaginatedProductListSerializer,
    PaginatedStockByLocationListSerializer,
    ProductSerializer,
    StockByProductResponseSerializer,
    StockByLocationSerializer,
)
from shared.openapi import TAG_INVENTORY
from shared.pagination import ICMPageNumberPagination


class LocationListView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: LocationSerializer(many=True)}, tags=[TAG_INVENTORY])
    def get(self, request):
        data = LocationSerializer(Location.objects.all().order_by("code"), many=True).data
        return Response(data)


class StockByProductView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={200: StockByProductResponseSerializer},
        tags=[TAG_INVENTORY],
    )
    def get(self, request, product_id):
        from uuid import UUID

        return Response(get_stock_by_product(UUID(str(product_id))))


class StockByLocationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={200: PaginatedStockByLocationListSerializer},
        tags=[TAG_INVENTORY],
    )
    def get(self, request, location_id):
        from uuid import UUID

        qs = get_stock_by_location(UUID(str(location_id)))
        paginator = ICMPageNumberPagination()
        page = paginator.paginate_queryset(list(qs), request, view=self)
        ser = StockByLocationSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


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
        responses={200: PaginatedProductListSerializer},
        tags=[TAG_INVENTORY],
    )
    def get(self, request):
        from uuid import UUID

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
