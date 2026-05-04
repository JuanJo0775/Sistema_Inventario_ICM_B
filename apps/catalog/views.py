"""Vistas de catálogo (RF-003)."""

from __future__ import annotations

from django.db.models import Q
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Product, ProductCombo, Subcategory
from apps.catalog.serializers import (
    CategorySerializer,
    ComboSerializer,
    ProductCreateSerializer,
    ProductSerializer,
    ResolveIdentifierQuerySerializer,
    SubcategorySerializer,
)
from apps.catalog.services import create_product, resolve_identifier
from shared.openapi import TAG_CATALOG
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


@extend_schema_view(
    get=extend_schema(summary="Listar categorías", tags=[TAG_CATALOG]),
)
class CategoryListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = ICMPageNumberPagination


@extend_schema_view(
    get=extend_schema(summary="Listar subcategorías", tags=[TAG_CATALOG]),
)
class SubcategoryListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Subcategory.objects.select_related("category").all()
    serializer_class = SubcategorySerializer
    pagination_class = ICMPageNumberPagination


@extend_schema_view(
    get=extend_schema(summary="Listar productos", tags=[TAG_CATALOG]),
    post=extend_schema(
        summary="Crear producto",
        request=ProductCreateSerializer,
        responses={201: ProductSerializer},
        tags=[TAG_CATALOG],
    ),
)
class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenista)
    queryset = Product.objects.select_related("category", "subcategory").all()
    serializer_class = ProductSerializer
    pagination_class = ICMPageNumberPagination

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        return qs

    def create(self, request, *args, **kwargs):
        ser = ProductCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        product = create_product(request.user, ser.validated_data, request=request)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(summary="Detalle de producto", tags=[TAG_CATALOG]),
    put=extend_schema(summary="Actualizar producto", tags=[TAG_CATALOG]),
    patch=extend_schema(summary="Actualizar producto parcialmente", tags=[TAG_CATALOG]),
)
class ProductDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Product.objects.select_related("category", "subcategory")
    serializer_class = ProductSerializer


class ResolveIdentifierView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[ResolveIdentifierQuerySerializer],
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Producto no encontrado para el identificador indicado."),
        },
        tags=[TAG_CATALOG],
    )
    def get(self, request):
        qser = ResolveIdentifierQuerySerializer(data=request.query_params)
        qser.is_valid(raise_exception=True)
        product = resolve_identifier(qser.validated_data["q"])
        if not product:
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)


@extend_schema_view(
    get=extend_schema(summary="Listar combos", tags=[TAG_CATALOG]),
)
class ComboListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = ProductCombo.objects.prefetch_related("combo_items__product").all()
    serializer_class = ComboSerializer
    pagination_class = ICMPageNumberPagination
