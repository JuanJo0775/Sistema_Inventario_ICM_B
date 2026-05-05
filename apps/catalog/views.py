"""Vistas de catálogo (RF-003)."""

from __future__ import annotations

from django.db.models import Q
from drf_spectacular.utils import (OpenApiParameter, OpenApiResponse,
                                   extend_schema, extend_schema_view)
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Product, ProductCombo, Subcategory
from apps.catalog.permissions import IsAlmacenistaOrReadOnly
from apps.catalog.serializers import (CategoryCreateSerializer,
                                      CategorySerializer,
                                      ComboCreateSerializer, ComboSerializer,
                                      ProductCreateSerializer,
                                      ProductSerializer,
                                      ProductUpdateSerializer,
                                      ResolveIdentifierQuerySerializer,
                                      SubcategorySerializer)
from apps.catalog.services import (create_category, create_combo,
                                   create_product, resolve_identifier,
                                   update_product)
from shared.openapi import TAG_CATALOG, standard_error_responses
from shared.pagination import ICMPageNumberPagination
from shared.permissions import IsAlmacenista


@extend_schema_view(
    get=extend_schema(
        summary="Listar categorías",
        tags=[TAG_CATALOG],
        responses={
            200: CategorySerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Crear categoría",
        request=CategoryCreateSerializer,
        responses={
            201: CategorySerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_CATALOG],
    ),
)
class CategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = ICMPageNumberPagination

    def create(self, request, *args, **kwargs):
        ser = CategoryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        cat = create_category(
            request.user,
            name=d["name"],
            description=d.get("description", ""),
            requires_serial_number=d.get("requires_serial_number", False),
            is_returnable=d.get("is_returnable", False),
            request=request,
        )
        return Response(CategorySerializer(cat).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Listar subcategorías",
        tags=[TAG_CATALOG],
        responses={
            200: SubcategorySerializer(many=True),
            **standard_error_responses(),
        },
    ),
)
class SubcategoryListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Subcategory.objects.select_related("category").all()
    serializer_class = SubcategorySerializer
    pagination_class = ICMPageNumberPagination


@extend_schema_view(
    get=extend_schema(
        summary="Listar productos",
        tags=[TAG_CATALOG],
        responses={
            200: ProductSerializer(many=True),
            **standard_error_responses(include_403=True),
        },
    ),
    post=extend_schema(
        summary="Crear producto",
        request=ProductCreateSerializer,
        responses={
            201: ProductSerializer,
            **standard_error_responses(include_403=True),
        },
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
    get=extend_schema(
        summary="Detalle de producto",
        tags=[TAG_CATALOG],
        responses={
            200: ProductSerializer,
            **standard_error_responses(include_404=True),
        },
    ),
    put=extend_schema(
        summary="Actualizar producto",
        tags=[TAG_CATALOG],
        responses={
            200: ProductSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
    patch=extend_schema(
        summary="Actualizar producto parcialmente",
        tags=[TAG_CATALOG],
        responses={
            200: ProductSerializer,
            **standard_error_responses(include_403=True, include_404=True),
        },
    ),
)
class ProductDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    queryset = Product.objects.select_related("category", "subcategory")
    serializer_class = ProductSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ser = ProductUpdateSerializer(data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        payload = {k: v for k, v in ser.validated_data.items()}
        product = update_product(request.user, instance.pk, payload, request=request)
        return Response(ProductSerializer(product).data)


class ResolveIdentifierView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="SKU, código de barras o fragmento de nombre.",
            ),
            OpenApiParameter(
                name="identifier",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Alias de `q` (misma semántica).",
            ),
        ],
        responses={
            200: ProductSerializer,
            **standard_error_responses(include_404=True),
        },
        tags=[TAG_CATALOG],
    )
    def get(self, request):
        qser = ResolveIdentifierQuerySerializer(data=request.query_params)
        qser.is_valid(raise_exception=True)
        product = resolve_identifier(qser.validated_data["_value"])
        return Response(ProductSerializer(product).data)


@extend_schema_view(
    get=extend_schema(
        summary="Listar combos",
        tags=[TAG_CATALOG],
        responses={
            200: ComboSerializer(many=True),
            **standard_error_responses(),
        },
    ),
    post=extend_schema(
        summary="Crear combo",
        request=ComboCreateSerializer,
        responses={
            201: ComboSerializer,
            **standard_error_responses(include_403=True),
        },
        tags=[TAG_CATALOG],
    ),
)
class ComboListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAlmacenistaOrReadOnly)
    queryset = ProductCombo.objects.prefetch_related("combo_items__product").all()
    serializer_class = ComboSerializer
    pagination_class = ICMPageNumberPagination

    def create(self, request, *args, **kwargs):
        ser = ComboCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        combo = create_combo(request.user, ser.validated_data, request=request)
        return Response(ComboSerializer(combo).data, status=status.HTTP_201_CREATED)
